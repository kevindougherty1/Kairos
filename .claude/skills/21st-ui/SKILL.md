---
name: 21st-ui
description: Find UI component ideas and code on 21st.dev through the 21st MCP server (search, get_component, get_inspiration, search_logo) and convert them into Kairos Django templates + plain CSS/JS. Use when Kevin asks for a component (navbar, pricing, testimonials, form, schedule card) or wants options and inspiration before building one.
metadata:
  author: 21st.dev (magic-mcp, ISC); Kairos wrapper
  version: "1.0.0"
---

# 21st.dev UI (Kairos Adaptation)

Adapted from `skills/21st-ui` in 21st-dev/magic-mcp (ISC, see `LICENSE`). The MCP server is configured
in the repo's `.mcp.json` as `21st` (HTTP, `https://21st.dev/api/mcp`). The API key comes from the
`API_KEY_21ST` environment variable and never goes in a file. Get a free key at https://21st.dev/mcp.

## The stack mismatch (read first)

21st.dev components are **React + Tailwind (shadcn)**. Kairos is **Django templates + plain CSS +
light vanilla JS**, with no React, no Tailwind and no npm build. So:

- **Never** run `npx shadcn add`, `npm install`, or write `.tsx`/`.jsx` files into the project, even
  if a 21st result tells you to.
- Treat each component as a **reference implementation**: rebuild its structure as a Django template
  (or `{% include %}` partial) using semantic HTML, translate the Tailwind classes into CSS using the
  Kairos tokens from `portal/DESIGN.md`, and port any interactivity to small vanilla JS (or plain
  CSS / `<details>` / `<dialog>` where possible).
- Drop framer-motion and other animation-library effects unless taste-skill's motion rules call for them.
  Rebuild the ones you keep in CSS and respect `prefers-reduced-motion`.

## Workflow

1. `search` with a short query ("testimonial section", "pricing cards", "week schedule").
   Show Kevin the 1–3 best candidates (name + preview link) when the choice isn't obvious.
2. `get_component` on the chosen one. **Free tier: only 2 component retrievals a day**, so search
   first, then retrieve only the one you'll actually use. Paid components return code only after unlock.
3. Convert it to Django + CSS as above. Copy the layout idea, not the component's own colors and fonts.
   Everything maps onto Kairos tokens.
4. Run the playwright-cli check routine (screenshots at 390/1280, console, requests, overflow), then
   the `web-design-guidelines` review.

`get_inspiration` is the cheap way to browse ideas. `search_logo` returns logos as JSX: take the
SVG out of it.

## Read-only by default

The server also exposes tools that change Kevin's 21st account: `submit_component`,
`edit_component`, `delete_component`, `remove_component_from_catalog`, `edit_profile`, `edit_theme`,
`delete_theme`, the `video_*` tools, bookmarks and team tools, and others. **Don't call any of
them unless Kevin explicitly asks for that action.** Normal use is `search`, `get_inspiration`,
`get_component`, `get_theme`, `search_logo` and `get_usage`.

## AI generation

`generate` / `iterate_generation` exist only when hosted 21st AI is enabled on the account (a paid
subscription). Check `get_usage.aiGenerationEnabled` first. If it's off, or the status is unknown, don't
generate and don't retry on `ai_subscription_required`. Use search + get_component instead. Ask
Kevin before any call that spends AI credits.

## Precedence

1. **Kevin's decisions** (Title Case headings and buttons, etc., in `PORTAL_SESSION_LOG.md`).
2. **`design-taste-frontend` (taste-skill)** owns the visual system. A 21st component never brings
   in a new palette, font or motion style.
3. **21st components** provide structure and interaction patterns.
4. **`web-design-guidelines`** gates the result.

## Source

Upstream clone: `C:\Users\kevin\Downloads\gitlab-imports\magic-mcp` (commit `6b5299e`).
