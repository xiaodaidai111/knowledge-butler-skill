---
name: knowledge-butler
description: "Organize long text, research material, tutorials, project notes, skill inventories, pasted knowledge, or exported notes into a local Markdown knowledge base. Use when the user asks to put content into Obsidian, Logseq, Dendron, Foam, a plain Markdown folder, a Notion export, a Zotero notes folder, or any local knowledge base; also use for MOC notes, linked notes, vault organization, deduplication, and structured Markdown ingest."
---

# Knowledge Butler

Use this skill to transform raw material into durable local knowledge notes. Obsidian is the default target, but the workflow also supports Logseq, Dendron, Foam, plain Markdown folders, Notion Markdown exports, and local reading-note folders.

The goal is not just to save text, but to create a small navigable knowledge structure that the user can keep learning from.

## Default Knowledge Base

When no knowledge base is specified, prefer:

```text
D:\Knowledge Management System
```

If that path is unavailable, ask for the local knowledge base path before writing. Do not guess another path.

## Supported Targets

Use `references/local-kb-adapters.md` when the target app or folder type matters.

- **Obsidian**: Markdown vaults with `[[wikilinks]]`, MOC notes, and optional `.obsidian/`.
- **Logseq**: graph folders with `pages/`, `journals/`, block-first writing, and page links.
- **Dendron**: hierarchical Markdown notes such as `area.topic.concept.md`.
- **Foam / VS Code Markdown**: Markdown workspace with wikilinks and graph view.
- **Plain Markdown**: ordinary local folders with Markdown links and index notes.
- **Notion export**: exported Markdown folders that should be cleaned and restructured.
- **Zotero / reading-note folders**: local literature notes, annotations, summaries, and paper-reading outputs.

## Before Writing

1. Identify the input type: pasted text, local file, transcript, research material, tutorial, project notes, or a list of skills/tools.
2. Identify the target knowledge base type if possible by folder structure or user wording.
3. Inspect the target vault, graph, workspace, or folder before creating notes.
4. Search for likely existing notes by topic keywords to avoid duplicates.
5. Propose the files to create or update in 3-6 concrete bullets.
6. Preserve source attribution when available: file path, URL, paper title, date, or conversation context.

## Ingest Workflow

1. **Clarify the knowledge goal**
   - Decide whether the material is for learning, research, project execution, reference, or skill inventory.
   - Choose a durable topic name. Prefer clear Chinese titles when the user's material is Chinese.

2. **Choose folder placement**
   - Prefer existing knowledge base conventions.
   - If no convention is visible, use the taxonomy in `references/vault-taxonomy.md`.
   - Keep folders shallow. Avoid scattering one topic across many top-level folders.

3. **Split notes by concept**
   - Create one MOC note for the topic.
   - Create focused child notes only when each note has its own reusable idea.
   - Avoid making tiny notes for every paragraph.
   - Keep each note useful on its own: definition, why it matters, key ideas, examples, and next actions where relevant.

4. **Add local navigation**
   - Use the target's native link style.
   - Prefer `[[wikilinks]]` for Obsidian and Foam.
   - Prefer Logseq page links and block-friendly outlines for Logseq.
   - Prefer Dendron hierarchical filenames when the workspace already uses them.
   - Prefer standard Markdown links for plain Markdown folders.
   - Add a short "Related" section when cross-links are useful.
   - Use a MOC note as the entry point, not a giant flat dump.

5. **Write in the user's style**
   - Use Chinese explanations by default.
   - Make steps concrete and copy-pasteable.
   - Keep headings descriptive.
   - Do not over-polish technical notes into marketing prose.

6. **Validate the ingest**
   - Confirm every created note is linked from the MOC or another parent note.
   - Check for duplicate titles.
   - Check that file names are Windows-safe.
   - Check that source context is not lost.
   - Summarize created and updated files.

## When to Read References

- Read `references/local-kb-adapters.md` when the target is not clearly Obsidian, or when importing from Logseq, Dendron, Foam, plain Markdown, Notion export, or Zotero notes.
- Read `references/vault-taxonomy.md` when choosing folders or when the knowledge base structure is unclear.
- Read `references/note-patterns.md` when deciding how to structure MOC, concept, tutorial, project, or skill inventory notes.
- Read `references/ingest-checklist.md` before the final response or before making many files.

## File Naming

- Prefer readable Chinese filenames for Chinese notes.
- Avoid characters invalid on Windows: `< > : " / \ | ? *`.
- Use numbered prefixes only for learning paths or ordered guides, such as `01 Agent Frontier MOC.md`.
- Keep MOC names explicit, such as `Topic MOC.md`.
- For Dendron, follow existing dotted hierarchy if present, such as `agent.frontier.computer-use.md`.

## Update Existing Notes

When a related note already exists:

- Append a dated section if the new content is additive.
- Merge into the existing structure if the note already has the same purpose.
- Create a new note only when the new material is a distinct concept.
- Never overwrite a note wholesale unless the user explicitly asks.

## Output Standard

A complete ingest should include:

- The knowledge base type, path, and target folder.
- Created and updated note list.
- The top-level MOC path.
- Any assumptions made.
- Any source material not ingested and why.

