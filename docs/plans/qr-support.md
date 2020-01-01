# Plan — QR code support for AssetTrack

> Library: `Net.Codecrete.QrCodeGenerator` (see `reports/qr-code-research.md`). The QR payload is a deep-link URL to the asset's detail page. Base URL for the course environment: `http://localhost:4321`.

## Goal

Every asset carries a scannable QR code that deep-links to its detail page, generated server-side and surfaced in the UI. Scanning is a later phase; this feature is generation + display only.

## Waves

The work splits into independent waves that meet only at the `GET /assets/{id}/qr` contract, so the backend and frontend can proceed in parallel.

### Wave 1 — Schema & payload (`services/assets-svc`)

- Add a `qr_payload TEXT` column to the `assets` table.
- Populate the payload **on write**: after inserting an asset, set `qr_payload = {WEB_BASE_URL}/assets/{id}`. The id only exists after the insert, so this is a second write — not part of the INSERT.
- **Backfill** existing rows (including seed data) on startup: `UPDATE assets SET qr_payload = base || id WHERE qr_payload IS NULL OR qr_payload = ''`.
- Add a migration so databases created before this column get it via `ALTER TABLE`.

### Wave 2 — API (`services/assets-svc`)

- Expose the payload as JSON on the existing asset representation (`qrPayload`), for flexibility.
- Add `GET /assets/{id}/qr` that reads the stored payload and returns a server-side rendered **SVG** (`image/svg+xml`); 404 when the asset does not exist.

### Wave 3 — UI (`services/web`)

- Thread `qrPayload` through the TypeScript `Asset` model.
- On the asset detail page (`src/pages/assets/[id].astro`), fetch the SVG server-side and inline it in a "QR code" card, as an **accessible image** (`role="img"` + descriptive `aria-label`), with a caption showing the target URL. Degrade gracefully if the image can't be fetched.

## Tests

- **assets-svc (xUnit):** payload is populated on create and ends with `/assets/{id}`; seed rows are backfilled; `GET /assets/{id}/qr` returns an SVG; missing asset returns 404.
- **web (Playwright):** the asset detail page renders the QR card and an accessible QR image whose inline SVG is visible.

## Reviewer notes / gaps caught in rubber-duck critique

- **Deep-link needs the id, which doesn't exist until after insert.** Naively "generate on insert" is wrong. Resolved by populating in a second write and backfilling pre-existing rows — otherwise assets created before this feature (and the seed data) would have no code.
- **Container safety:** the library must be pure-managed (no `System.Drawing`), or it would pass locally and fail in the Linux container.
- **Accessibility:** the QR is meaningful content, not decorative — it needs a text alternative, so it is exposed as `role="img"` with an `aria-label` and a visible caption rather than a bare inline `<svg>`.
