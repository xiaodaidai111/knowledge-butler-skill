# Local Knowledge Base Taxonomy

Use the knowledge base's existing structure first. If there is no clear structure, use this fallback.

## Default Folders

- `00_Inbox/`: temporary captures not yet processed.
- `10_Projects/`: active projects with deliverables, deadlines, or implementation tasks.
- `20_Areas/`: ongoing responsibilities and long-lived domains.
- `30_Resources/`: reusable knowledge, tutorials, references, concepts, and skill inventories.
- `40_Archive/`: inactive or completed material.

## Placement Rules

- Put learning notes, tutorials, frameworks, and technology explainers under `30_Resources/`.
- Put research project execution notes under `10_Projects/` if they drive a specific paper or experiment.
- Put reusable research concepts under `30_Resources/科研/` or the closest existing equivalent.
- Put competition project plans under `10_Projects/` while the competition is active.
- Put Codex or agent skill inventories under `30_Resources/Codex Skills/` unless the knowledge base has a better existing folder.

## App-Specific Notes

- Obsidian and Foam can use this taxonomy directly.
- Logseq may prefer `pages/` for concept notes and `journals/` only for dated capture.
- Dendron may encode folders as dotted filenames instead of nested folders.
- Plain Markdown folders can use `index.md` instead of MOC if that is the existing convention.
- Notion exports often need cleanup before placement because exported filenames may include IDs or duplicated folder names.

## Topic Folder Pattern

For a substantial topic, create:

```text
30_Resources/
  Topic Name/
    01 Topic Name MOC.md
    02 Concept A.md
    03 Concept B.md
```

Skip a dedicated folder if the topic only needs one note.

