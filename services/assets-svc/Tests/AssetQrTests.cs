using System.Net;
using System.Net.Http.Json;
using Contoso.Assets.Models;
using Microsoft.AspNetCore.Mvc.Testing;
using Xunit;

namespace Contoso.Assets.Tests;

/// <summary>
/// Tests for the QR code feature: the deep-link payload is populated on create
/// and backfilled for seed rows, and GET /assets/{id}/qr renders an SVG.
/// </summary>
public class AssetQrTests : IDisposable
{
    private readonly WebApplicationFactory<Program> _factory;
    private readonly HttpClient _client;
    private readonly string _dbPath;

    public AssetQrTests()
    {
        _dbPath = Path.Combine(Path.GetTempPath(), $"assets-qr-test-{Guid.NewGuid():N}.db");
        Environment.SetEnvironmentVariable("ASSETS_DB_PATH", _dbPath);
        _factory = new WebApplicationFactory<Program>()
            .WithWebHostBuilder(builder =>
            {
                builder.UseSetting("ASSETS_DB_PATH", _dbPath);
                Environment.SetEnvironmentVariable("ASSETS_DB_PATH", _dbPath);
            });
        _client = _factory.CreateClient();
    }

    public void Dispose()
    {
        _client.Dispose();
        _factory.Dispose();
        if (File.Exists(_dbPath)) File.Delete(_dbPath);
    }

    [Fact]
    public async Task Create_PopulatesQrPayload_WithDeepLinkContainingId()
    {
        var newAsset = new AssetCreate
        {
            AssetTag = "QR-001", AssetType = "Laptop", Manufacturer = "Dell",
            Model = "XPS 13", Status = "available"
        };

        var create = await _client.PostAsJsonAsync("/assets", newAsset);
        Assert.Equal(HttpStatusCode.Created, create.StatusCode);
        var created = await create.Content.ReadFromJsonAsync<Dictionary<string, long>>();
        var id = created!["id"];

        var asset = await _client.GetFromJsonAsync<Asset>($"/assets/{id}");
        Assert.NotNull(asset);
        Assert.False(string.IsNullOrEmpty(asset!.QrPayload));
        Assert.EndsWith($"/assets/{id}", asset.QrPayload);
    }

    [Fact]
    public async Task SeededAssets_HaveBackfilledQrPayload()
    {
        // Seed data is applied on first initialize; every row should carry a payload.
        var assets = await _client.GetFromJsonAsync<List<Asset>>("/assets");
        Assert.NotNull(assets);
        Assert.NotEmpty(assets!);
        Assert.All(assets!, a =>
        {
            Assert.False(string.IsNullOrEmpty(a.QrPayload));
            Assert.EndsWith($"/assets/{a.Id}", a.QrPayload!);
        });
    }

    [Fact]
    public async Task GetQr_ReturnsSvgImage()
    {
        var assets = await _client.GetFromJsonAsync<List<Asset>>("/assets");
        var id = assets![0].Id;

        var res = await _client.GetAsync($"/assets/{id}/qr");
        Assert.Equal(HttpStatusCode.OK, res.StatusCode);
        Assert.Equal("image/svg+xml", res.Content.Headers.ContentType?.MediaType);

        var svg = await res.Content.ReadAsStringAsync();
        Assert.Contains("<svg", svg);
        Assert.Contains("</svg>", svg);
    }

    [Fact]
    public async Task GetQr_ForMissingAsset_Returns404()
    {
        var res = await _client.GetAsync("/assets/999999/qr");
        Assert.Equal(HttpStatusCode.NotFound, res.StatusCode);
    }
}
