# Local Knowledge Base Adapters

Use this reference to adapt the ingest workflow to different local knowledge systems.

## Detection

Inspect the target folder before writing:

- `.obsidian/` usually means Obsidian.
- `logseq/`, `pages/`, and `journals/` together usually mean Logseq.
- `dendron.yml` or dotted note names usually mean Dendron.
- `.foam/` or a VS Code workspace with Markdown notes may mean Foam.
- A folder full of `.md` files with no app config is a plain Markdown knowledge base.
- Notion exports often contain Markdown files plus attachment folders and filenames with long IDs.
- Zotero or paper-note folders often contain citation keys, paper titles, PDFs, and reading summaries.

## Obsidian

- Use `[[wikilinks]]`.
- Use MOC notes for topic entry points.
- Keep attachment paths unchanged unless the user asks to reorganize assets.
- Avoid editing `.obsidian/`.

## Logseq

- Prefer pages under `pages/`.
- Use `[[Page Name]]` page references.
- Favor outline-friendly blocks, but keep normal Markdown headings when the existing graph uses them.
- Do not put durable concepts into `journals/` unless the user asks for daily notes.

## Dendron

- Check for `dendron.yml`.
- Prefer existing dotted hierarchy, for example `research.aef.jepa.md`.
- Use standard Markdown links or wikilinks according to existing notes.
- Avoid creating deep folders when the workspace uses dotted names.

## Foam / VS Code Markdown

- Use `[[wikilinks]]` if existing notes use them.
- Create an index or MOC note for topic entry.
- Keep note titles simple and graph-friendly.

## Plain Markdown Folder

- Use standard Markdown links: `[Title](relative/path.md)`.
- Create `index.md` or `Topic MOC.md` depending on existing style.
- Prefer relative links that work in GitHub and local editors.
- Avoid relying on app-specific plugins.

## Notion Markdown Export

- Treat exported files as source material, not final structure.
- Remove duplicated title prefixes and unreadable ID fragments when creating new notes.
- Preserve attachments only when the notes reference them and the files exist locally.
- Create a cleaned MOC so the imported export is navigable.

## Zotero / Reading Notes

- Preserve citation metadata when available: title, authors, year, DOI, URL, citation key.
- Separate paper summaries from reusable concepts.
- Link paper notes to concept notes and project notes.
- Do not move PDFs unless the user explicitly asks.

## Link Style Selection

Prefer the style already present in the folder. If mixed or unclear:

1. Obsidian, Foam, Logseq: `[[Note Title]]`.
2. Dendron: dotted note names plus whatever the workspace already uses.
3. Plain Markdown or GitHub-facing repositories: relative Markdown links.

