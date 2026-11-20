---
name: design-md
description: Reference library of 84 DESIGN.md design-system writeups of real websites (tokens, type, layout, components, do's and don'ts), plus the DESIGN.md format for Kairos's own design system. Use when choosing or documenting the Kairos visual system, writing or updating portal/DESIGN.md, or when Kevin asks how a site like Oura, Nike, Apple, Airbnb, Linear, Notion or Cal handles something.
metadata:
  author: VoltAgent (awesome-design-md, MIT); Kairos wrapper
  version: "1.0.0"
---

# DESIGN.md Reference Library

Adapted from VoltAgent/awesome-design-md (MIT, see `LICENSE` in this folder). Upstream is a
plain collection of markdown files and ships no skill. This wrapper makes it usable from Claude Code.

## Source

`library/` is a **directory junction** to
`C:\Users\kevin\Downloads\gitlab-imports\awesome-design-md\design-md` (upstream commit `fcc7028`,
2026-10-28). It's gitignored. To update, `git pull` in the clone. A fresh checkout needs the clone
and the junction re-created:

```powershell
New-Item -ItemType Junction -Path .claude\skills\design-md\library -Target C:\Users\kevin\Downloads\gitlab-imports\awesome-design-md\design-md
```

Each entry is `library/<site>/DESIGN.md`. The file starts with YAML front matter (colors, typography,
spacing, radii tokens), then prose sections: Overview, Colors, Typography, Layout (spacing, grid,
breakpoints, touch targets), Elevation & Depth, Shapes, Components (nav, hero, buttons, forms, cards),
and Do's and Don'ts. The `README.md` beside each one is only a link to getdesign.md, so skip it.

## How Kairos uses it

1. **Format for Kairos's own design system.** The Kairos visual system lives in one file,
   `portal/DESIGN.md`, written in this format (front-matter tokens plus the same prose sections).
   It is the single source of truth for tokens: the CSS custom properties in the portal are generated
   from it or kept in sync with it by hand.
2. **Reference, not a template.** Read entries to see how mature systems solve a specific problem
   (form density, schedule/list layout, pill vs. square buttons, how a wellness brand uses warm
   neutrals). Borrow the *reasoning*, not the identity.
3. **Never clone a brand.** Don't copy a site's palette and type pairing wholesale, don't use its
   proprietary fonts (Nike Futura, Helvetica Now, Oura's Editorial serif and similar are licensed),
   and don't reproduce logos, wordmarks or signature components. Kairos must look like Kairos.

### Most relevant entries for a 1:1 running coach

| Entry | Why look at it |
|---|---|
| `oura` | Wellness/health, warm paper palette, calm photo-led layouts, one decisive action color |
| `nike` | Athletic voice, photography-first, strict neutral chrome with sparse accents |
| `apple` | Restraint, typographic hierarchy, product-detail pacing |
| `airbnb` | Friendly service brand, cards, booking-style forms |
| `cal` | Scheduling UI: closest analog to the client workout schedule |
| `linear.app`, `notion` | Dense logged-in app screens: lists, editing, keyboard-friendly |
| `stripe`, `wise` | Trustworthy forms, clear numbers (useful for pace/mileage tables) |

## Precedence with the other design skills

1. **Kevin's decisions** win (e.g. Title Case for headings and buttons, see `PORTAL_SESSION_LOG.md`).
2. **`design-taste-frontend` (taste-skill)** picks the visual system: palette, type pairing, layout,
   photos, motion. Record its choices in `portal/DESIGN.md`.
3. **This library** informs and documents those choices. It doesn't override taste-skill.
4. **`web-design-guidelines`** is the quality gate for every page, regardless of what a reference does.
