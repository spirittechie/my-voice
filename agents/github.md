# GitHub Execution and Commit Discipline

## Purpose

This repository must maintain continuous Git discipline. The agent working in this repo is not permitted to make loose edits, silent rewrites, or large uncommitted change piles. Every meaningful modification must be captured in Git immediately and pushed to GitHub as part of normal execution.

This file is operational policy, not suggestion.

## Core Rule

For every meaningful repository change:

1. Make the change.
2. Verify the affected files.
3. Update related markdown or documentation if the code behavior changed.
4. Commit immediately with a clear message.
5. Push immediately to the active GitHub branch.

Do not batch unrelated edits together unless explicitly instructed.

## Required Behavior

The agent must treat Git as part of the edit cycle, not a cleanup step at the end.

The agent must:
- check repo status before starting work
- inspect the active branch before editing
- make small, traceable commits
- push after each meaningful edit set
- keep markdown, docs, and code synchronized
- refuse to leave the repo in a dirty state unless explicitly told to pause without committing
- never ask the user unless the task cannot be completed without it or an error occurs that requires user decision

## Definition of Meaningful Edit

A meaningful edit includes any of the following:
- code change
- config change
- prompt change
- markdown/spec correction
- README update
- refactor affecting behavior
- file creation
- file deletion
- rename
- test addition or modification

Minor whitespace-only cleanup may be grouped, but do not hide real work inside “formatting” commits.

## Documentation Synchronization Rule

If code behavior changes, the agent must check whether the following also need updates:
- README.md
- docs/
- agents/
- architecture markdown
- setup instructions
- usage examples
- service descriptions
- file maps or inheritance notes

The repo must not advertise architecture that the code does not implement.

If markdown contradicts code, the contradiction must be corrected as part of the same work cycle or explicitly called out in the commit message.

## Commit Cadence

The default cadence is:
- one logical change
- one commit
- one push

Do not wait for a “final cleanup” phase to commit.

Do not accumulate large uncommitted work trees.

Do not mix multiple unrelated fixes into one commit unless explicitly instructed.

## Commit Message Policy

Commit messages must be short, concrete, and technical.

Preferred style:
- `fix: add state reset for interrupted recording`
- `docs: align README with actual GTK DBus voice flow`
- `refactor: move clipboard handling into service helper`
- `test: add coverage for DBus transcription path`

Avoid vague messages like:
- `update stuff`
- `misc changes`
- `cleanup`
- `working on it`

If the change corrects repo drift between markdown and code, say so directly.

Examples:
- `docs: remove agent-runtime claims not backed by code`
- `docs: archive speculative orchestration md files`
- `fix: align puck UI actions with DBus service methods`

## Push Policy

After each commit, push to GitHub immediately.

Default command flow:
```bash
git status
git branch --show-current
git add <changed files>
git commit -m "type: concise technical summary"
git push
```

If the branch has no upstream yet, set it:

```bash
git push -u origin "$(git branch --show-current)"
```

Do not defer pushes unless:

* the user explicitly says not to push
* credentials are unavailable
* network access is unavailable
* the repo is in a broken intermediate state and the user explicitly wants a local checkpoint only

If push fails, report the exact reason and keep the local commit intact.

## Pre-Commit Sanity Check

Before committing, the agent should quickly verify:

* changed files are intentional
* no unrelated files are accidentally staged
* docs reflect code if behavior changed
* no placeholder text or hallucinated architecture was introduced
* no secrets or tokens are being committed

## Branch Awareness

The agent must always know:

* current branch
* whether upstream is configured
* whether the branch is ahead/behind
* whether there are uncommitted changes before starting new work

The agent must not create random branches unless explicitly instructed.

## Markdown Governance

Markdown in this repo is treated as operational truth only when backed by code.

The agent must not:

* invent live subsystems that do not exist
* describe speculative architecture as implemented
* leave outdated specs in active paths without marking them as future or archived
* expand design fiction while the codebase remains smaller and simpler

If a markdown file is aspirational, label it clearly as future design, proposal, or archive material.

## Required Working Pattern

For every task, the agent should follow this order:

1. Read the relevant code and markdown.
2. Identify the smallest coherent change.
3. Edit only what is necessary.
4. Sync related docs.
5. Review the diff.
6. Commit immediately.
7. Push immediately.
8. Report what changed.

## Diff Review Expectation

Before commit, inspect the diff:

```bash
git diff --stat
git diff -- <important file>
```

Before push, confirm status:

```bash
git status
```

After push, confirm clean state:

```bash
git status
```

A clean working tree is the expected resting state.

## Failure Handling

If the agent cannot commit or push, it must report:

* what changed
* what remains uncommitted
* why the commit or push failed
* the exact next command required to recover

It must not pretend the repo is synchronized when it is not.

## Non-Negotiable Rule

No significant edit should be left floating in the working tree.

The repository history is part of the project architecture.

Commit early. Commit clearly. Push continuously.

# Git Hard Rules

The agent must commit and push after every meaningful repository edit.

A meaningful edit includes code, config, docs, prompts, tests, file creation, deletion, rename, or behavior change.

Default workflow:
1. inspect status
2. edit
3. update related docs
4. review diff
5. commit
6. push
7. confirm clean working tree

The agent must not leave large uncommitted work trees.

The agent must not let markdown drift away from code.

The agent must not describe speculative architecture as implemented.

If push fails, report the reason exactly and preserve the local commit.

One logical change equals one commit.
