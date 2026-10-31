#!/usr/bin/env python3
"""Fill assets/template.html with a code file and write a self-contained snippet page."""
import argparse, base64, html, json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXT = {".rb": "ruby", ".ts": "typescript", ".tsx": "typescript", ".js": "javascript", ".jsx": "javascript",
       ".py": "python", ".sh": "shell", ".zsh": "shell", ".bash": "shell", ".json": "json",
       ".yml": "yaml", ".yaml": "yaml"}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("code_file", help="file holding the exact text to show")
    p.add_argument("--filename", help="path shown in the title bar (default: the code file's name)")
    p.add_argument("--title", help="heading in the sidebar (default: the file's stem)")
    p.add_argument("--lang", help="ruby, typescript, javascript, python, shell, json, yaml (default: from extension)")
    p.add_argument("--url", default="damiangalarza.com", help="watermark text")
    p.add_argument("--out", default="code-snippet.html", help="output HTML path")
    p.add_argument("--open", action="store_true", help="open the page in the default browser")
    a = p.parse_args()

    code_path = Path(a.code_file)
    code = code_path.read_text()
    lang = a.lang or EXT.get(code_path.suffix.lower(), "plain")
    logo = base64.b64encode((ROOT / "assets" / "logomark-light.svg").read_bytes()).decode()

    page = (ROOT / "assets" / "template.html").read_text()
    # </ would end the JSON <script> block early
    code_json = json.dumps(code).replace("</", "<\\/")
    fills = {
        "__CODE_JSON__": code_json,
        "__LOGO__": "data:image/svg+xml;base64," + logo,
        "__TITLE__": html.escape(a.title or code_path.stem),
        "__FILENAME__": html.escape(a.filename or code_path.name),
        "__URL__": html.escape(a.url),
        "__LANG__": html.escape(lang),
    }
    for key, value in fills.items():
        page = page.replace(key, value)

    out = Path(a.out)
    out.write_text(page)
    print(out.resolve())
    if a.open:
        subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", str(out)], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
