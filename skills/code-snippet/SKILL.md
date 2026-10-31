---
name: code-snippet
description: Turn a piece of code into a branded, Carbon-style snippet image for social posts, in Damian Galarza's design system. Use when the user wants a code screenshot, code card, or shareable snippet image, mentions carbon.now.sh, or asks to make code look good for LinkedIn, X, a blog post, or a video. Produces a single HTML page with a live preview and an Export PNG button.
---

# Code Snippet

Builds one self-contained HTML page that shows code in a dark window on a brand-colour stage, with the logomark and site URL as a watermark. The user adjusts it in the browser and exports a PNG.

## Steps

1. **Pick the exact text to show.** Trim the code to what the post needs: drop type signatures, long comments, and unrelated methods. Never change what the code does. Comments the user asked for may be added or rewritten, so confirm that wording with them when it states a fact (a score, a threshold, a result).
2. **Write it to a file** in the scratchpad or a temp directory, never inside a project repo. Use a real extension (`.rb`, `.ts`, `.py`, `.sh`, `.json`, `.yml`) so the language is detected.
3. **Build the page:**

   ```bash
   python3 <skill-dir>/scripts/build.py snippet.rb \
     --filename app/models/example.rb \
     --title Example \
     --out ./example-snippet.html --open
   ```

   | Option | Default | Notes |
   | --- | --- | --- |
   | `--filename` | the file's name | Path shown in the title bar |
   | `--title` | the file's stem | Sidebar heading |
   | `--lang` | from extension | `ruby`, `typescript`, `javascript`, `python`, `shell`, `json`, `yaml`; anything else renders as plain text |
   | `--url` | `damiangalarza.com` | Watermark text |
   | `--out` | `code-snippet.html` | Output path |
   | `--open` | off | Open in the default browser |

4. **Check it.** Take a headless screenshot, or open the page, and read it before reporting back. Look at line wrapping, the title-bar path, and the watermark on the default background.
5. **Tell the user** where the file is and that **Export PNG** saves the image: 2x for the Fit shape, exact pixels for the fixed shapes.

## Controls in the page

Background swatches (Red, Yellow, Pale Blue, Purple, Grey 100, Black), shape, text size, padding, line numbers on/off, watermark on/off, and watermark placement (outside the window or inside its bottom-right corner). On light backgrounds an outside watermark turns black.

| Shape | Export size | Use |
| --- | --- | --- |
| Fit | sized to the code, 2x | Default; blog or a quick share |
| 4:5 | 1080 × 1350 | Instagram carousel slide |
| 1:1 | 1080 × 1080 | Square posts |
| Wide | 1600 × 900 | X and LinkedIn link images |

Picking a fixed shape sets a text size and padding that read well at that width; the sliders still override them. When the code does not fit the frame, the page shows "Code is clipped" and the export would cut it off. Shorten the snippet or lower the text size before exporting. Wide fits only short snippets, roughly 6 lines.

## Serving it to another device (optional)

Only when the user asks. Copy the page into its own empty directory so nothing else is exposed, serve that directory on a free port bound to `127.0.0.1`, and proxy it with `tailscale serve --bg --http=<port> http://127.0.0.1:<port>`. Use `tailscale serve`, never `tailscale funnel`, so the page stays inside the tailnet. Check `tailscale serve status` first and leave existing serves alone. Report how to turn it off (`tailscale serve --http=<port> off`).

## Notes

- **Brand source:** Colours and type styles come from the "Design System" page of the Damian Galarza Web Design Figma file (Colors frame `50:2823`, Logomark-Light `54:4039`). They are baked into `assets/template.html`; no Figma call is needed at runtime. Refresh them from Figma only when the brand changes.
- **Fonts:** PP Neue Machina and PP Neue Montreal are licensed and not bundled. Without them installed the page falls back to Helvetica and the system monospace. To use them, add `@font-face` rules to the template.
- **Network:** The page loads `html-to-image` from cdnjs for Export PNG, so exporting needs a connection.
- **Watermark colour:** The dark variant is the light logomark with a CSS `brightness(0)` filter (pure black, not brand Black `#191812`). Swap in the Logomark-Dark asset when it is available.
- **Public repo:** This skill's files are public. Never put private or client code in `assets/` or in examples here.
