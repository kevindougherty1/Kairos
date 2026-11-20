---
name: web-design-guidelines
description: Review UI code for Web Interface Guidelines compliance. Use when asked to "review my UI", "check accessibility", "audit design", "review UX", or "check my site against best practices", and before any Kairos portal or public page is called done.
metadata:
  author: vercel
  version: "1.0.0"
  argument-hint: <file-or-pattern>
---

# Web Interface Guidelines

Review files for compliance with Web Interface Guidelines.

Adapted from vercel-labs/agent-skills `web-design-guidelines` (MIT, see LICENSE). The upstream skill
fetches its rules from the web at review time. This copy reads a **pinned local copy** instead, so
the rules only change when Kevin chooses to update them.

## Rules source

`rules.md` in this folder. It's a copy of `vercel-labs/web-interface-guidelines/command.md` at commit
`434b7f9`, copied 2026-11-19. To update it, `git pull` in
`C:\Users\kevin\Downloads\gitlab-imports\web-interface-guidelines` and copy `command.md` over `rules.md`.

## How it works

1. Read `rules.md` from this folder.
2. Read the specified files (or ask the user which files/pattern to review).
3. Check against all rules.
4. Output findings in the terse `file:line` format that `rules.md` specifies.

## Kairos adaptations

Kairos is Django templates + HTML/CSS + light vanilla JS, not React. Apply the rules like this:

- JSX names map to their HTML equivalents: `htmlFor` → `for`, `spellCheck={false}` → `spellcheck="false"`,
  `onKeyDown` → native elements (`<button>`, `<a>`) that already handle the keyboard.
- Skip the React-only rules: Hydration Safety, `useState`/nuqs URL sync (the HTML principle "URL
  reflects state" still applies via query params), React virtualization libraries.
- **Copy casing decision (Kevin, 2026-11-19): Title Case for headings and buttons**, sentence case
  for body text. This wins over taste-skill's casing.
- Use this together with the `design-taste-frontend` skill (taste-skill). That skill sets the look;
  this one is the quality gate. Both apply to every page.
