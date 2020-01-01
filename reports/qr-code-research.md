# QR code generation library research — `assets-svc`

> Research artifact for the QR support feature. Captures the options considered and why we chose one, so future contributors understand the decision.

## Decision

Use **[`Net.Codecrete.QrCodeGenerator`](https://www.nuget.org/packages/Net.Codecrete.QrCodeGenerator)** to generate QR codes server-side in `services/assets-svc` (.NET 8).

## Use case & constraints

- **Use case:** generate a QR image for an asset on the server. The payload is a deep-link URL to the asset's detail page.
- **Runtime:** the service runs in a **Linux container**. The library must **not** depend on native OS graphics (e.g. `System.Drawing.Common`, which is unsupported on non-Windows and needs native `libgdiplus`).
- **Decision criteria:** permissive license, active maintenance, a **pure-managed** rendering path, and **SVG** output (crisp at any size, no rasterization dependency).

## Options compared

| Library | License | Maintenance | Pure-managed rendering | Output formats |
| ------- | ------- | ----------- | ---------------------- | -------------- |
| **Net.Codecrete.QrCodeGenerator** | MIT | Active | **Yes** — emits SVG string / module matrix, no drawing deps | SVG, module bitmap (bring-your-own raster) |
| QRCoder | MIT | Active | Mixed — `SvgQRCode` is pure-managed, but the popular `PngByteQRCode` path and `System.Drawing` renderers pull native/Windows deps | PNG, SVG, others |
| ZXing.Net | Apache-2.0 | Active | Encoding is managed, but image rendering historically leans on `System.Drawing`/`SkiaSharp` bindings | Many (via renderer packages) |

## Why `Net.Codecrete.QrCodeGenerator`

- **No native graphics dependency.** It produces an SVG string directly from the QR module matrix, so nothing touches `System.Drawing` or a native imaging stack — it renders identically on a developer laptop and in the Linux container.
- **SVG is the right output.** The asset detail page scales the code responsively; a vector avoids the blurriness and byte overhead of a rasterized PNG.
- **Permissive license (MIT)** compatible with this project, and **actively maintained**.

## Integration sketch (`services/assets-svc`)

1. Add the package reference to `AssetsService.csproj`.
2. Store the deep-link payload per asset (`qr_payload` column), populated on write and backfilled for existing rows.
3. Add `GET /assets/{id}/qr` that reads the stored payload and returns `QrCode.EncodeText(payload, Ecc.Medium).ToSvgString(4)` with content type `image/svg+xml`.

## Sources

- Net.Codecrete.QrCodeGenerator — project & NuGet: <https://github.com/manuelbl/QrCodeGenerator>, <https://www.nuget.org/packages/Net.Codecrete.QrCodeGenerator>
- QRCoder — <https://github.com/codebude/QRCoder>
- ZXing.Net — <https://github.com/micjahn/ZXing.Net>
- .NET on why `System.Drawing.Common` is Windows-only — <https://learn.microsoft.com/dotnet/core/compatibility/core-libraries/6.0/system-drawing-common-windows-only>

> [!NOTE]
> This report is evidence for the decision, not the decision itself. If a reviewer prefers a different option that still satisfies the pure-managed + SVG + permissive-license constraints, the integration sketch is the only part that changes.
