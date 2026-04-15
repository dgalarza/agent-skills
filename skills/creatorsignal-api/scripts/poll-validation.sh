#!/usr/bin/env bash
# Poll a CreatorSignal validation until complete or max attempts reached.
# Usage: poll-validation.sh <idea_id> [--base-url <url>] [--max-attempts <n>]
#
# Requires: curl, jq
# Env: CS_API_KEY (required)
#
# Outputs final validation JSON to stdout. Progress messages go to stderr.

set -e

# --- Dependency checks ---

for cmd in curl jq; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "{\"error\": \"$cmd not installed\"}" >&2
    exit 1
  fi
done

# --- Argument parsing ---

IDEA_ID=""
BASE_URL="${CS_BASE_URL:-https://app.creatorsignal.io}"
MAX_ATTEMPTS=12

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-url)
      BASE_URL="$2"
      shift 2
      ;;
    --max-attempts)
      MAX_ATTEMPTS="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: poll-validation.sh <idea_id> [--base-url <url>] [--max-attempts <n>]" >&2
      echo "" >&2
      echo "Poll a CreatorSignal validation until complete." >&2
      echo "" >&2
      echo "Arguments:" >&2
      echo "  idea_id              ID of the idea to poll" >&2
      echo "  --base-url <url>     API base URL (default: \$CS_BASE_URL or https://app.creatorsignal.io)" >&2
      echo "  --max-attempts <n>   Maximum poll attempts (default: 12)" >&2
      echo "" >&2
      echo "Environment:" >&2
      echo "  CS_API_KEY           API key (required, format: cs_live_<prefix>_<secret>)" >&2
      echo "  CS_BASE_URL          Default base URL if --base-url not provided" >&2
      exit 0
      ;;
    *)
      if [[ -z "$IDEA_ID" ]]; then
        IDEA_ID="$1"
      else
        echo "{\"error\": \"Unknown argument: $1\"}" >&2
        exit 1
      fi
      shift
      ;;
  esac
done

# --- Validation ---

if [[ -z "$IDEA_ID" ]]; then
  echo "Usage: poll-validation.sh <idea_id> [--base-url <url>] [--max-attempts <n>]" >&2
  exit 1
fi

if [[ -z "$CS_API_KEY" ]]; then
  echo '{"error": "CS_API_KEY environment variable is required"}' >&2
  exit 1
fi

# --- Helpers ---

HEADERS_FILE=$(mktemp)
trap 'rm -f "$HEADERS_FILE"' EXIT

retry_after() {
  local default="${1:-10}"
  local value
  value=$(grep -i 'Retry-After' "$HEADERS_FILE" 2>/dev/null | tr -d '[:space:]' | cut -d: -f2)
  echo "${value:-$default}"
}

# --- Polling loop ---

ATTEMPT=0
URL="${BASE_URL}/api/v1/ideas/${IDEA_ID}/validation"

while [[ $ATTEMPT -lt $MAX_ATTEMPTS ]]; do
  ATTEMPT=$((ATTEMPT + 1))

  BODY=$(curl -s -w "\n%{http_code}" -D "$HEADERS_FILE" \
    "$URL" \
    -H "Authorization: Bearer $CS_API_KEY")

  HTTP_CODE=$(echo "$BODY" | tail -1)
  JSON_BODY=$(echo "$BODY" | sed '$d')

  if [[ "$HTTP_CODE" == "200" ]]; then
    STATUS=$(echo "$JSON_BODY" | jq -r '.validation.status')
    if [[ "$STATUS" == "complete" ]]; then
      VERDICT=$(echo "$JSON_BODY" | jq -r '.validation.verdict')
      SCORE=$(echo "$JSON_BODY" | jq -r '.validation.score')
      echo "Validation complete: verdict=$VERDICT score=$SCORE" >&2
    elif [[ "$STATUS" == "failed" ]]; then
      echo "Validation failed: $(echo "$JSON_BODY" | jq -r '.validation.error_message')" >&2
    fi
    echo "$JSON_BODY"
    exit 0
  elif [[ "$HTTP_CODE" == "202" ]]; then
    RETRY_AFTER=$(retry_after 10)
    VALIDATION_STATUS=$(echo "$JSON_BODY" | jq -r '.validation.status')
    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS: status=$VALIDATION_STATUS, retrying in ${RETRY_AFTER}s..." >&2
    sleep "$RETRY_AFTER"
  elif [[ "$HTTP_CODE" == "401" ]]; then
    echo '{"error": "Authentication failed — check CS_API_KEY"}' >&2
    exit 1
  elif [[ "$HTTP_CODE" == "404" ]]; then
    echo "{\"error\": \"Idea $IDEA_ID not found or does not belong to this account\"}" >&2
    exit 1
  elif [[ "$HTTP_CODE" == "429" ]]; then
    RETRY_AFTER=$(retry_after 30)
    echo "Rate limited, retrying in ${RETRY_AFTER}s..." >&2
    sleep "$RETRY_AFTER"
  else
    echo "{\"error\": \"Unexpected HTTP status: $HTTP_CODE\"}" >&2
    exit 1
  fi
done

echo "{\"error\": \"Max attempts ($MAX_ATTEMPTS) reached. Validation still in progress for idea $IDEA_ID.\"}" >&2
exit 1
