# Knowledge Butler Skill

A Codex skill for turning long text, research notes, tutorials, project material, and skill inventories into a tidy local Markdown knowledge base.

It focuses on knowledge organization rather than app automation: topic splitting, folder placement, MOC notes, backlinks, source notes, and final ingest checks.

## Supported Local Knowledge Bases

- Obsidian vaults.
- Logseq graph folders.
- Dendron workspaces.
- Foam / VS Code Markdown workspaces.
- Plain Markdown folders.
- Notion Markdown exports.
- Zotero, paper, or reading-note folders that store notes as Markdown.

The skill reads the local folder structure first, then adapts note naming, links, and folder placement to that system.

## Install

Copy the skill folder into your Codex skills directory:

```powershell
Copy-Item -Recurse .\skills\knowledge-butler $env:USERPROFILE\.codex\skills\
```

Restart Codex or reload skills after installing.

## Use

Example prompts:

```text
Use $knowledge-butler to organize this Agent frontier text into my Obsidian vault.
```

```text
Use $knowledge-butler to turn these research notes into a MOC plus linked notes under D:\Knowledge Management System.
```

```text
Use $knowledge-butler to import this Notion Markdown export into my local knowledge base.
```

## What It Produces

- A clear folder placement plan.
- One MOC note for the topic.
- Focused Markdown notes with stable titles.
- App-appropriate links: Obsidian/Foam wikilinks, Logseq page links, Dendron hierarchy titles, or plain Markdown links.
- Source and status metadata where useful.
- A final ingest checklist covering duplicates, broken links, and missing context.

## Repository Layout

```text
skills/
  knowledge-butler/
    SKILL.md
    agents/openai.yaml
    references/
      ingest-checklist.md
      local-kb-adapters.md
      note-patterns.md
      vault-taxonomy.md
```
