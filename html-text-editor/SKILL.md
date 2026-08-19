---
name: html-text-editor
description: Edit the visible text of static HTML files in the browser, semi-WYSIWYG, and save back to the source file without touching markup, indentation, or CSS. Use when someone wants to reword a mockup, a landing page, or any hand-written HTML without opening an editor or hunting through tags.
---

# HTML text editor

A local server that makes every run of visible text in your HTML files editable in the
browser. Saving writes only the text back into the source file. Markup, attributes,
indentation, and CSS come out byte-identical.

## Run it

    python3 edit.py

Then open http://localhost:4321. Every `.html` file next to `edit.py` is listed.

Pick a page, type over any text, and press Save or Cmd+S. The bar at the bottom shows the
file name, links to the other pages, an edit toggle, and the save status.

Python 3.10 or newer. No dependencies.

## How it stays safe

The browser and the server both enumerate *text runs*: maximal spans of character data
between two tags, which is exactly what the browser turns into one text node. Both sides
skip `<script>` and `<style>` and skip whitespace-only runs, so they produce the same list
in the same order.

On save the browser sends the current text of every run, in order. The server re-parses the
file, finds the source offsets of every run, and replaces them back to front. If the two
counts disagree, the save is **refused** with an error rather than guessed at — a mismatch
means the DOM no longer matches the file, and writing would put the right text in the wrong
place.

Two rules keep the DOM stable while you type:

- **Enter is blocked.** A new line in `contenteditable` creates elements, which changes the
  run count. Paragraphs cannot be split.
- **Paste is forced to plain text**, with whitespace collapsed, so pasted markup cannot
  enter the document.

The editor uses a plain `contenteditable`, not `plaintext-only`: Chrome forces
`white-space: pre-wrap` on a plaintext-only host, which reflows the page while you edit it.

## Configuration

Both live at the top of `edit.py`:

- `PORT` — defaults to 4321.
- `EDIT_ASSET_ROOT` — the directory served for images, CSS, and other assets, so relative
  paths in your HTML resolve. It defaults to the folder holding the pages. Set it when the
  pages reference files above themselves:

      EDIT_ASSET_ROOT=~/code/myrepo python3 edit.py

## Limits

- Text only. It cannot add, remove, or reorder elements, and it cannot change attributes,
  links, or styles.
- The list of editable pages is the `.html` files in the same folder as `edit.py`.
- A page open in a browser tab goes stale if the file changes on disk. Reload before
  editing, or the save is refused.
- No authentication. It binds to 127.0.0.1 and is meant for local use.
