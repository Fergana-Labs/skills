#!/usr/bin/env python3
"""Semi-WYSIWYG text editor for the landing mockups.

    python3 docs/experiments/landing-redesign/edit.py
    open http://localhost:4321

Every run of visible text in a page is made editable in the browser. Saving
writes only those text runs back into the source file, so all of the markup,
indentation, and CSS in the file survives untouched.

The browser and the server enumerate text runs the same way and in the same
order. If the two counts ever disagree, the save is refused rather than
guessed at.
"""
import html
import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Assets are served from here, so relative paths like ../../img.png in your HTML
# resolve. Defaults to the folder holding the pages; set EDIT_ASSET_ROOT when the
# pages point at files above them.
REPO = Path(os.environ.get("EDIT_ASSET_ROOT", HERE)).resolve()
PORT = 4321
SKIP_TAGS = {"script", "style"}


class TextRuns(HTMLParser):
    """Find every maximal run of character data, with its source offsets.

    A run is what the browser turns into one text node: characters between
    two tags, with entity references counted as part of the same run.
    """

    def __init__(self, raw: str):
        super().__init__(convert_charrefs=False)
        self.raw = raw
        self.line_start = [0]
        for line in raw.splitlines(keepends=True):
            self.line_start.append(self.line_start[-1] + len(line))
        self.runs: list[tuple[int, int]] = []
        self.depth_skipped = 0
        self.open_run: list[int] | None = None
        self.feed(raw)
        self.close()
        self.flush()

    def source_offset(self) -> int:
        line, col = self.getpos()
        return self.line_start[line - 1] + col

    def flush(self) -> None:
        if self.open_run is None:
            return
        start, end = self.open_run
        self.open_run = None
        if self.raw[start:end].strip():
            self.runs.append((start, end))

    def add(self, length: int) -> None:
        if self.depth_skipped:
            return
        start = self.source_offset()
        end = start + length
        if self.open_run and self.open_run[1] == start:
            self.open_run[1] = end
        else:
            self.flush()
            self.open_run = [start, end]

    def handle_starttag(self, tag, attrs):
        self.flush()
        if tag in SKIP_TAGS:
            self.depth_skipped += 1

    def handle_startendtag(self, tag, attrs):
        self.flush()

    def handle_endtag(self, tag):
        self.flush()
        if tag in SKIP_TAGS and self.depth_skipped:
            self.depth_skipped -= 1

    def handle_data(self, data):
        self.add(len(data))

    def handle_entityref(self, name):
        self.add(len(name) + 2)

    def handle_charref(self, name):
        self.add(len(name) + 3)

    def handle_comment(self, data):
        self.flush()

    def handle_decl(self, decl):
        self.flush()

    def handle_pi(self, data):
        self.flush()


def pages() -> list[str]:
    return sorted(p.name for p in HERE.glob("*.html"))


def apply_edits(path: Path, texts: list[str]) -> int:
    raw = path.read_text()
    runs = TextRuns(raw).runs
    if len(texts) != len(runs):
        raise ValueError(
            f"{path.name}: browser sent {len(texts)} text runs, file has {len(runs)}. "
            "Reload the page and try again."
        )
    for (start, end), text in zip(reversed(runs), reversed(texts)):
        raw = raw[:start] + html.escape(text, quote=False) + raw[end:]
    path.write_text(raw)
    return len(runs)


EDITOR = """
<div data-editor id="ed-bar">
  <span id="ed-name"></span>
  <span class="ed-files"></span>
  <span class="ed-spacer"></span>
  <label class="ed-toggle"><input type="checkbox" id="ed-on" checked> edit text</label>
  <span id="ed-status">no changes</span>
  <button id="ed-save">Save</button>
</div>
<style data-editor>
  #ed-bar { position: fixed; z-index: 9999; left: 0; right: 0; bottom: 0;
    display: flex; align-items: center; gap: 14px; padding: 9px 16px;
    background: #16130F; color: #F7F4EE; font: 500 12.5px/1.4 ui-monospace, Menlo, monospace; }
  #ed-bar a { color: rgba(247,244,238,0.6); text-decoration: none; margin-right: 12px; }
  #ed-bar a:hover, #ed-bar a.on { color: #FF5A36; }
  #ed-name { color: #FF5A36; }
  .ed-spacer { flex: 1; }
  .ed-toggle { display: flex; align-items: center; gap: 6px; color: rgba(247,244,238,0.6); }
  #ed-status { color: rgba(247,244,238,0.45); }
  #ed-status.dirty { color: #FFB627; }
  #ed-status.saved { color: #6FCF97; }
  #ed-status.error { color: #FF5A36; }
  #ed-save { font: inherit; background: #FF5A36; color: #fff; border: 0; border-radius: 6px;
    padding: 7px 14px; cursor: pointer; }
  body { padding-bottom: 52px; }
  [contenteditable="plaintext-only"]:hover, [contenteditable="true"]:hover {
    outline: 1px dashed rgba(255,90,54,0.5); outline-offset: 2px; }
  [contenteditable]:focus { outline: 2px solid #FF5A36; outline-offset: 2px; }
</style>
<script data-editor>
(function () {
  const FILE = document.currentScript.dataset.file;
  const PAGES = JSON.parse(document.currentScript.dataset.pages);

  const bar = document.getElementById('ed-bar');
  const status = document.getElementById('ed-status');
  document.getElementById('ed-name').textContent = FILE;
  bar.querySelector('.ed-files').innerHTML = PAGES
    .map((p) => `<a href="${p}" class="${p === FILE ? 'on' : ''}">${p.replace(/\\.html$/, '')}</a>`)
    .join('');

  // Same walk the server does: every run of visible text, in document order,
  // skipping the editor's own chrome.
  function textNodes() {
    const walker = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const el = node.parentElement;
        if (!el) return NodeFilter.FILTER_REJECT;
        if (el.tagName === 'SCRIPT' || el.tagName === 'STYLE') return NodeFilter.FILTER_REJECT;
        if (el.closest('[data-editor]')) return NodeFilter.FILTER_REJECT;
        return node.data.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      },
    });
    const out = [];
    let node;
    while ((node = walker.nextNode())) out.push(node);
    return out;
  }

  const nodes = textNodes();
  const original = nodes.map((n) => n.data);
  // A plain editable, not plaintext-only: Chrome forces white-space: pre-wrap on
  // a plaintext-only host, which reflows the page while you edit it. Enter and
  // rich paste are blocked below, which is what plaintext-only was for.
  const mode = 'true';

  function setEditable(on) {
    const seen = new Set();
    nodes.forEach((n) => {
      const el = n.parentElement;
      if (seen.has(el)) return;
      seen.add(el);
      if (on) el.setAttribute('contenteditable', mode);
      else el.removeAttribute('contenteditable');
    });
  }
  setEditable(true);
  document.getElementById('ed-on').addEventListener('change', (e) => setEditable(e.target.checked));

  function mark(text, cls) {
    status.textContent = text;
    status.className = cls || '';
  }

  document.addEventListener('input', () => mark('unsaved changes', 'dirty'));

  // Keep the DOM structure identical to the file: no new elements, no line breaks.
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.target.isContentEditable) e.preventDefault();
  });
  document.addEventListener('paste', (e) => {
    if (!e.target.isContentEditable) return;
    e.preventDefault();
    const text = e.clipboardData.getData('text/plain').replace(/\\s+/g, ' ');
    document.execCommand('insertText', false, text);
  });

  async function save() {
    const now = textNodes();
    if (now.length !== original.length) {
      mark(`structure changed (${now.length} vs ${original.length}) — reload`, 'error');
      return;
    }
    mark('saving…');
    const res = await fetch('/__save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file: FILE, texts: now.map((n) => n.data) }),
    });
    const body = await res.json();
    if (!res.ok) return mark(body.error || 'save failed', 'error');
    mark(`saved ${body.runs} text runs`, 'saved');
  }

  document.getElementById('ed-save').addEventListener('click', save);
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 's') {
      e.preventDefault();
      save();
    }
  });
})();
</script>
"""

INDEX = """<title>Stash mockups — editor</title>
<style>
  body { background:#F7F4EE; color:#16130F; font:16px/1.6 -apple-system, system-ui, sans-serif;
    max-width:640px; margin:0 auto; padding:80px 24px; }
  h1 { font-size:28px; letter-spacing:-0.02em; }
  p { color:#7C7469; margin-top:12px; }
  a.page { display:block; margin-top:10px; padding:16px 18px; border:1px solid rgba(22,19,15,.12);
    border-radius:10px; background:#fff; color:#16130F; text-decoration:none;
    font:500 15px ui-monospace, Menlo, monospace; }
  a.page:hover { border-color:#FF5A36; color:#FF5A36; }
  ul { margin-top:14px; color:#7C7469; padding-left:20px; }
</style>
<h1>Edit the landing mockups</h1>
<p>Click a page, type over any text, then press Save or Cmd+S. Only the text you
  changed is written back to the file. Layout, CSS, and markup are left alone.</p>
%s
<ul>
  <li>Turn editing off with the checkbox to click links and scroll normally.</li>
  <li>Enter does nothing on purpose, so a paragraph cannot be split in two.</li>
  <li>If the bar reports a structure change, reload the page and edit again.</li>
</ul>
"""


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(REPO), **kwargs)

    def log_message(self, fmt, *args):
        print(f"  {fmt % args}")

    def send_html(self, body: str, code: int = 200) -> None:
        payload = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def send_json(self, obj: dict, code: int = 200) -> None:
        payload = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        name = self.path.lstrip("/").split("?")[0]
        if name in ("", "index.html"):
            links = "\n".join(f'<a class="page" href="/{p}">{p}</a>' for p in pages())
            return self.send_html(INDEX % links)
        if name in pages():
            raw = (HERE / name).read_text()
            editor = EDITOR.replace(
                "<script data-editor>",
                f'<script data-editor data-file="{name}" '
                f"data-pages='{json.dumps(pages())}'>",
            )
            rel = HERE.relative_to(REPO).as_posix() if HERE != REPO else ""
            base = f'<base href="/{rel + "/" if rel else ""}">'
            return self.send_html(base + raw + editor)
        return super().do_GET()

    def do_POST(self):
        if self.path != "/__save":
            return self.send_json({"error": "unknown endpoint"}, 404)
        length = int(self.headers["Content-Length"])
        payload = json.loads(self.rfile.read(length))
        name = payload["file"]
        if name not in pages():
            return self.send_json({"error": f"unknown file {name}"}, 400)
        try:
            runs = apply_edits(HERE / name, payload["texts"])
        except ValueError as err:
            return self.send_json({"error": str(err)}, 409)
        print(f"  saved {name} ({runs} text runs)")
        return self.send_json({"runs": runs})


if __name__ == "__main__":
    print(f"editing {', '.join(pages())}")
    print(f"open http://localhost:{PORT}")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
