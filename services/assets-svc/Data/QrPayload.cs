using Net.Codecrete.QrCodeGenerator;

namespace Contoso.Assets.Data;

/// <summary>
/// Builds the QR deep-link payload for an asset and renders it as a pure-managed
/// SVG (no native System.Drawing dependency, so it runs unchanged in the Linux
/// container). The payload is a deep link to the asset's detail page in the web
/// app; the scanning phase lives in a later milestone.
/// </summary>
public static class QrPayload
{
    // The web base URL is fixed for the course environment but overridable so the
    // same code works if the app is hosted elsewhere.
    public static string WebBaseUrl() =>
        Environment.GetEnvironmentVariable("WEB_BASE_URL")?.TrimEnd('/') ?? "http://localhost:4321";

    // Base fragment stored per row; the asset id is appended to form the payload.
    public static string DeepLinkBase() => $"{WebBaseUrl()}/assets/";

    public static string For(long id) => $"{DeepLinkBase()}{id}";

    /// <summary>Render a payload string as an SVG QR code (border = 4 modules).</summary>
    public static string ToSvg(string payload)
    {
        var qr = QrCode.EncodeText(payload, QrCode.Ecc.Medium);
        return qr.ToSvgString(4);
    }
}
