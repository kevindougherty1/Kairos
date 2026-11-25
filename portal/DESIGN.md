---
version: 1.0
name: Hard Left
description: Calm, paper-and-pine design system for a 1:1 running coach. A warm cream ground and green-black ink (first matched to the old KPG logo), one pine-green action colour, Rethink Sans throughout, soft 8/12/20 radii and hairline rows. The public pages lead with photographs (Sunday); the logged-in portal is plain working screens (lists, schedules, forms) on the same tokens.

colors:
  canvas: "#efe9e0"        # --p-bg: page ground (logo cream)
  surface: "#e2d9cb"       # --p-surface: cards, panels, notices
  ink: "#22261f"           # --p-ink: text, hairlines (13% / 22%), logo green-black
  muted: "#5a5c53"         # --p-muted: dates, labels, meta only
  action: "#2e5b44"        # --p-action / --p-accent: primary button, links, focus ring, "Published"/"Completed" marks
  on-action: "#ffffff"
  field: "#fffdf9"         # --field-bg: inputs
  field-line: "#76736a"    # --field-line: input borders
  warn: "#8a3d1c"          # --warn: coach-facing warnings and form errors (text)
  warn-tint: "#f3dccd"     # --warn-bg: warning panel ground
  inverse-canvas: "#22261f"
  inverse-surface: "#2e322a"
  inverse-ink: "#efe9e0"
  inverse-muted: "#a19e96"

typography:
  family: "Rethink Sans (Google Fonts, 400..700), system-ui fallback"
  h1-public:   { fontSize: "clamp(38px, 3.24vw + 25.4px, 72px)", fontWeight: 400, lineHeight: 1.15, letterSpacing: -0.025em }
  h2-public:   { fontSize: "clamp(30px, 1.72vw + 23.3px, 48px)", fontWeight: 400, lineHeight: 1.15, letterSpacing: -0.025em }
  h1-app:      { fontSize: "clamp(30px, 1.72vw + 23.3px, 44px)", fontWeight: 400, lineHeight: 1.15, letterSpacing: -0.025em }
  h2-app:      { fontSize: "24px / 28px from 1024", fontWeight: 400 }
  h3:          { fontSize: "18px / 20px from 1024", fontWeight: 400 }
  body:        { fontSize: 16px, fontWeight: 400, lineHeight: 1.6 }
  small:       { fontSize: 14px }
  label:       { fontSize: 13px, fontWeight: 500 }
  button:      { fontSize: 16px, fontWeight: 500 }

spacing: [4, 8, 12, 16, 24, 32, 48, 64, 96, 128]   # --s-1 … --s-10
radii: { sm: 8px, md: 12px, lg: 20px, button: 8px, badge: 999px }
layout: { container: 1280px, gutter: "80 / 48 (640–1023) / 24 (<640)", header: "72 / 56 (<640)", measure: 62ch }
controls: { button: 44px, field: 48px, min-tap: 44px }
motion: { ease: "cubic-bezier(.2,.8,.2,1)", duration: 180ms }
---

# Hard Left Design System

**Brand name (2026-11-25): Hard Left**, as in the hard left turn of running a track. It's the display name only;
file and code names stay `kairos` (e.g. `kairos.css`).

**Where it lives:** tokens and components in `portal/static/kairos/kairos.css`; the shared page frame in
`portal/templates/base.html`; the mark/favicon in `portal/static/kairos/img/favicon.svg`. **Change a colour, size or radius in
kairos.css (and here), never in a template.**

## Overview

Hard Left is a 1:1 running coach, and the system should feel like a calm training log:
paper, pencil and one green pen. Colour comes from the logo, and later from photographs on the public pages.
The interface itself stays 90–95% neutral.

**How it was chosen (2026-11-22):** taste-skill dealt the palette and type for a *service* business in the
wellness/fitness trade. Its first palette (rose-grey and green) clashed with the KPG logo's cream ground, so
the second, **clay-pine**, was taken. It's effectively the logo's own colours. The first pairing,
**Rethink Sans**, was kept because its plain, sturdy sans matches the logo's lettering. Radius: soft.

**Two registers, one system:**
- **Public pages** (Home/Offer, About, Inquiry; Sunday): built with taste-skill's kit (`system.css`, one
  section per screen, photo-led, hero entrance), loading the same `:root` values. Use `h1-public`/`h2-public`.
- **Portal screens** (login, coach, client, plans, workouts): working screens. No heroes, no scroll
  moments. Use `h1-app`. Lists, cards and forms come from kairos.css.

## Colors

| Token | Hex | Use | Contrast (checked) |
|---|---|---|---|
| canvas | `#efe9e0` | Page ground | — |
| surface | `#e2d9cb` | Cards, panels, notices | — |
| ink | `#22261f` | All reading text | 12.75:1 on canvas, 11.0:1 on surface |
| muted | `#5a5c53` | Dates, labels, meta. Never paragraphs. | 5.63:1 on canvas, 4.86:1 on surface |
| action | `#2e5b44` | Primary button, links, focus ring, positive marks | 6.45:1 on canvas; white on it 7.79:1 |
| field-line | `#76736a` | Input borders | 3.93:1 on canvas, 3.39:1 on surface, 4.67:1 on field |
| warn | `#8a3d1c` | Warnings, form errors (text) | 6.29:1 on canvas; ink on warn-tint 11.67:1 |

- **One accent.** Pine green is the only colour that means "act" or "good". It's used for the primary button,
  links, the focus ring, and the Published/Completed badges. Nothing else is green.
- **Warn is functional, not decorative.** It's used only for engine warnings the coach must see and for
  form errors. It's never a heading colour or decoration.
- Hairlines are ink at 13% (`--line`) and 22% (`--line-strong`). Never #000, never violet.

## Typography

- Rethink Sans for everything. Headlines at 400 with tight tracking (−2.5%); buttons and labels at 500.
- **Casing (Kevin's decision, overrides taste-skill): Title Case for headings and buttons**, sentence case
  for body text, labels and help text.
- Text people read is 16px or larger. 14px is for help text and dates, 13px for labels and badges. Nothing smaller.
- Numbers in lists (dates, miles, times) use `.num` / tabular figures so columns line up.
- Curly apostrophes and quotes in copy (’ “ ”). Brand names carry `translate="no"`.

## Layout

- `.wrap`: 1280px column with equal side gutters (80 / 48 / 24). Every header, page and footer aligns to it.
- Fixed header, 72px (56 on phones): opaque canvas with a hairline under it. No blur, no shrinking.
  `scroll-padding-top` keeps focused or linked elements clear of it.
- Page head (`.page-head`): h1 + one muted line, then 48px to the content.
- Breakpoints: under 640 (phone: one column, full-width buttons), 640–1023, 1024 and up (two-column `.split`).
- Touch targets at least 44px; fields 48px with 16px text, so phones never zoom.

## Elevation & Depth

Flat. No shadows. Depth comes from the canvas → surface step and 1px hairlines only.

## Shapes

Radius scale (soft): controls 8px, panels and notices 12px, cards 20px, buttons 8px, badges fully round.

## Components

| Component | Class | Notes |
|---|---|---|
| Primary button | `.btn.btn--primary` | Pine, white label, 44px. **One per view.** Lifts 1px on hover, presses on click. |
| Secondary button | `.btn.btn--secondary` | Transparent, 22% ink border. Log Out, back actions. |
| Card | `.card` | Surface ground, 20px radius, 24/32px padding. Never a box in a box. |
| Card grid | `.cards` | Columns at least 480px wide: one column on phones, two on desktop. |
| Split | `.split` | 5/7 columns from 1024 (reading card + working card), stacked below. |
| Rows | `.rows` > `li` > `.row` | Hairline-ruled list: date · title · meta. Used for workouts and plans. |
| Facts | `.facts` | Inline muted meta line (date · type · distance); `strong` for the key figure. |
| Badge | `.badge` (+ `--live`, `--done`, `--draft`, `--muted`, `--warn`) | Status only: Published, Completed, Draft (dashed), Archived, Demo. |
| Notice | `.notice`, `.notice--warn` | Demo-data label; engine warnings on coach plan views. |
| Field | `.field` (label above, input, `.field__help`, errors) | Visible label always; errors under the field in warn; first invalid field focused. |
| Auth card | `.auth` | Centred 440px column for login and password reset. |
| Header | `.nav`, `.brand`, `.mark`, `.nav__link` | Dots mark + "Hard Left" (17px on phones, never wraps); current page has a 2px underline (`aria-current`). |

## Do's and Don'ts

**Do**
- Keep each screen to one primary action (e.g. Log Result).
- Label fixtures. Demo plans show the "Demo plan" notice and the Demo badge.
- Show engine warnings to the coach in a warn notice at the top of the week they belong to.
- Use real photographs on public pages (Kevin's own, or licensed stand-ins listed as such).

**Don't**
- Add a second accent, gradients, shadows, glass/blur, or violet.
- Put paragraphs in muted grey, or text under 13px.
- Use placeholders as labels, or block paste.
- Show a client a draft, a coach warning, or another client's data (the access layer enforces this; the design never relies on hiding).

## Responsive Behavior

- **Phone (<640):** header 56px; user name hidden, brand name at 17px; rows wrap the date above the
  title; primary form buttons go full width; cards stack.
- **Tablet (640–1023):** 48px gutters, single column.
- **Desktop (1024+):** `.split` goes two-column, `.cards` two-up, h3 and lead sizes step up.

## Iteration Guide

1. Change tokens in `kairos.css` `:root` **and** the front matter above, in the same commit.
2. After any visual change, run the "check my work" routine: screenshots at 390 and 1280, console and requests
   clean, no sideways overflow, then the web-design-guidelines review.
3. A new component goes in kairos.css with a row in the Components table. Don't use one-off styles in templates.

## Known Gaps

- Fonts load from Google Fonts. Self-host before launch for privacy and speed (Phase 3).
- No dark mode (deliberate: the light-only paper look; taste-skill reserves dark for tech pages).
- Public-page components (hero, photo sections, footer, inquiry form) come from taste-skill's kit on Sunday.
- **No real logo yet.** The mark is taste-skill's dealt placeholder (`dots`, ink on canvas, also the favicon) until a
  Hard Left logo exists. The old KPG logo is no longer used in the portal.
