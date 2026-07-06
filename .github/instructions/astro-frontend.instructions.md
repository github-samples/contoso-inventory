---
applyTo: "services/web/src/**/*.{astro,ts,tsx}"
description: This file describes instructions for the Astro + TypeScript frontend in the web service.
---

- Keep the frontend SSR-first: fetch data in Astro frontmatter/server code, and use React islands only for genuinely interactive UI.
- Route all backend access through `services/web/src/lib/api/*`; do not call backend services directly from the browser.
- Use strict TypeScript with explicit types at module boundaries, no `any`, and no unsafe casts unless there is a clear boundary and a brief justification.
- Prefer small, composable components and helpers over large page files; keep UI, data shaping, and request logic separated.
- Preserve accessibility by default: use semantic HTML, correct heading order, labeled controls, keyboard-friendly interactions, and `aria-*` only when native elements are insufficient.
- Keep styling consistent with Bootstrap 5 and `services/web/src/styles/app.css`; reuse existing utilities and patterns before adding custom CSS.
- Favor server-side data shaping and parallel requests where possible; keep error, empty, and loading states explicit and user-visible.
- Keep React islands lightweight and avoid hydration unless the interaction needs client-side state or events.
- Prefer minimal dependencies; use existing Astro, React, and Bootstrap capabilities before introducing new packages.
- Make incremental, easy-to-review changes that preserve current behavior, keep public markup stable when practical, and update focused tests or coverage when behavior changes.
