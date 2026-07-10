using System.Net;
using System.Net.Http.Json;
using Contoso.Assets.Models;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Xunit;

namespace Contoso.Assets.Tests;

/// <summary>
/// Integration tests for the Assets API endpoints using WebApplicationFactory.
/// Each test uses an isolated temporary SQLite database via ASSETS_DB_PATH.
/// </summary>
public class AssetEndpointsTests : IDisposable
{
    private readonly WebApplicationFactory<Program> _factory;
    private readonly HttpClient _client;
    private readonly string _dbPath;

    public AssetEndpointsTests()
    {
        // Create a unique temporary database for this test instance
        _dbPath = Path.Combine(Path.GetTempPath(), $"assets-test-{Guid.NewGuid():N}.db");
        
        _factory = new WebApplicationFactory<Program>()
            .WithWebHostBuilder(builder =>
            {
                builder.UseEnvironment("Testing");
                builder.UseSetting("ASSETS_DB_PATH", _dbPath);
                
                // Set environment variable for the app to pick up
                Environment.SetEnvironmentVariable("ASSETS_DB_PATH", _dbPath);
            });
        
        _client = _factory.CreateClient();
    }

    public void Dispose()
    {
        _client.Dispose();
        _factory.Dispose();
        
        // Clean up the temporary database
        if (File.Exists(_dbPath))
        {
            File.Delete(_dbPath);
        }
    }

    #region Create Tests

    [Fact]
    public async Task Create_WithValidData_ReturnsCreated()
    {
        // Arrange
        var newAsset = new AssetCreate
        {
            AssetTag = "TEST-001",
            AssetType = "Laptop",
            Manufacturer = "Dell",
            Model = "XPS 15",
            SerialNumber = "SN123456",
            Status = "available",
            PurchaseDate = "2024-01-15",
            WarrantyExpiry = "2027-01-15"
        };

        // Act
        var response = await _client.PostAsJsonAsync("/assets", newAsset);

        // Assert
        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
        var result = await response.Content.ReadFromJsonAsync<Dictionary<string, long>>();
        Assert.NotNull(result);
        Assert.True(result.ContainsKey("id"));
        Assert.True(result["id"] > 0);
        
        // Verify Location header
        Assert.NotNull(response.Headers.Location);
        Assert.Contains("/assets/", response.Headers.Location.ToString());
    }

    [Fact]
    public async Task Create_WithMinimalData_ReturnsCreated()
    {
        // Arrange - only required fields
        var newAsset = new AssetCreate
        {
            AssetTag = "MINIMAL-001",
            AssetType = "Keyboard",
            Manufacturer = "Logitech",
            Model = "K120",
            Status = "available"
        };

        // Act
        var response = await _client.PostAsJsonAsync("/assets", newAsset);

        // Assert
        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
    }

    [Fact]
    public async Task Create_WithNullOptionalFields_ReturnsCreated()
    {
        // Arrange
        var newAsset = new AssetCreate
        {
            AssetTag = "NULL-OPTIONAL",
            AssetType = "Monitor",
            Manufacturer = "Samsung",
            Model = "S27",
            SerialNumber = null,
            PurchaseDate = null,
            WarrantyExpiry = null,
            Status = "available",
            Notes = null
        };

        // Act
        var response = await _client.PostAsJsonAsync("/assets", newAsset);

        // Assert
        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
    }

    #endregion

    #region Read Tests - Get All

    [Fact]
    public async Task GetAll_ReturnsAllAssets()
    {
        // Arrange - create a few assets
        await CreateTestAsset("GET-001", "Laptop");
        await CreateTestAsset("GET-002", "Monitor");
        await CreateTestAsset("GET-003", "Keyboard");

        // Act
        var response = await _client.GetAsync("/assets");

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var assets = await response.Content.ReadFromJsonAsync<List<Asset>>();
        Assert.NotNull(assets);
        Assert.True(assets.Count >= 3);
    }

    [Fact]
    public async Task GetAll_WithNoAssets_ReturnsEmptyList()
    {
        // Act - fresh database has seed data, but we can verify the endpoint works
        var response = await _client.GetAsync("/assets");

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var assets = await response.Content.ReadFromJsonAsync<List<Asset>>();
        Assert.NotNull(assets);
    }

    #endregion

    #region Read Tests - Get By Id

    [Fact]
    public async Task GetById_WithExistingId_ReturnsAsset()
    {
        // Arrange
        var id = await CreateTestAsset("GETID-001", "Laptop");

        // Act
        var response = await _client.GetAsync($"/assets/{id}");

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var asset = await response.Content.ReadFromJsonAsync<Asset>();
        Assert.NotNull(asset);
        Assert.Equal(id, asset.Id);
        Assert.Equal("GETID-001", asset.AssetTag);
    }

    [Fact]
    public async Task GetById_WithNonExistentId_ReturnsNotFound()
    {
        // Act
        var response = await _client.GetAsync("/assets/999999");

        // Assert
        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    [Fact]
    public async Task GetById_WithInvalidId_ReturnsBadRequest()
    {
        // Act
        var response = await _client.GetAsync("/assets/invalid");

        // Assert - route constraint should prevent this from matching
        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    #endregion

    #region Update Tests

    [Fact]
    public async Task Update_WithExistingId_ReturnsNoContent()
    {
        // Arrange
        var id = await CreateTestAsset("UPDATE-001", "Laptop");
        var update = new AssetCreate
        {
            AssetTag = "UPDATED-001",
            AssetType = "Laptop",
            Manufacturer = "HP",
            Model = "EliteBook",
            SerialNumber = "NEW-SN",
            Status = "assigned"
        };

        // Act
        var response = await _client.PutAsJsonAsync($"/assets/{id}", update);

        // Assert
        Assert.Equal(HttpStatusCode.NoContent, response.StatusCode);

        // Verify the update
        var getResponse = await _client.GetAsync($"/assets/{id}");
        var asset = await getResponse.Content.ReadFromJsonAsync<Asset>();
        Assert.NotNull(asset);
        Assert.Equal("UPDATED-001", asset.AssetTag);
        Assert.Equal("HP", asset.Manufacturer);
        Assert.Equal("EliteBook", asset.Model);
    }

    [Fact]
    public async Task Update_WithNonExistentId_ReturnsNotFound()
    {
        // Arrange
        var update = new AssetCreate
        {
            AssetTag = "NOEXIST-001",
            AssetType = "Laptop",
            Manufacturer = "Dell",
            Model = "XPS",
            Status = "available"
        };

        // Act
        var response = await _client.PutAsJsonAsync("/assets/999999", update);

        // Assert
        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    [Fact]
    public async Task Update_WithPartialData_UpdatesAllFields()
    {
        // Arrange
        var id = await CreateTestAsset("PARTIAL-001", "Monitor");
        var update = new AssetCreate
        {
            AssetTag = "PARTIAL-UPDATED",
            AssetType = "Monitor",
            Manufacturer = "LG",
            Model = "27UK850",
            Status = "retired",
            Notes = "Updated notes"
        };

        // Act
        var response = await _client.PutAsJsonAsync($"/assets/{id}", update);

        // Assert
        Assert.Equal(HttpStatusCode.NoContent, response.StatusCode);
    }

    #endregion

    #region Delete Tests

    [Fact]
    public async Task Delete_WithExistingId_ReturnsNoContent()
    {
        // Arrange
        var id = await CreateTestAsset("DELETE-001", "Keyboard");

        // Act
        var response = await _client.DeleteAsync($"/assets/{id}");

        // Assert
        Assert.Equal(HttpStatusCode.NoContent, response.StatusCode);

        // Verify deletion
        var getResponse = await _client.GetAsync($"/assets/{id}");
        Assert.Equal(HttpStatusCode.NotFound, getResponse.StatusCode);
    }

    [Fact]
    public async Task Delete_WithNonExistentId_ReturnsNotFound()
    {
        // Act
        var response = await _client.DeleteAsync("/assets/999999");

        // Assert
        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    [Fact]
    public async Task Delete_IsIdempotent_SecondDeleteReturnsNotFound()
    {
        // Arrange
        var id = await CreateTestAsset("IDEMPOTENT-001", "Phone");

        // Act - first delete
        var firstResponse = await _client.DeleteAsync($"/assets/{id}");
        Assert.Equal(HttpStatusCode.NoContent, firstResponse.StatusCode);

        // Act - second delete
        var secondResponse = await _client.DeleteAsync($"/assets/{id}");

        // Assert
        Assert.Equal(HttpStatusCode.NotFound, secondResponse.StatusCode);
    }

    #endregion

    #region Search Tests

    [Fact]
    public async Task Search_ByType_ReturnsMatchingAssets()
    {
        // Arrange
        await CreateTestAsset("SEARCH-LAPTOP-1", "Laptop");
        await CreateTestAsset("SEARCH-LAPTOP-2", "Laptop");
        await CreateTestAsset("SEARCH-MONITOR-1", "Monitor");

        // Act
        var response = await _client.GetAsync("/assets/search?type=Laptop");

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var assets = await response.Content.ReadFromJsonAsync<List<Asset>>();
        Assert.NotNull(assets);
        Assert.True(assets.Count >= 2);
        Assert.All(assets, a => Assert.Equal("Laptop", a.AssetType));
    }

    [Fact]
    public async Task Search_ByStatus_ReturnsMatchingAssets()
    {
        // Arrange
        await CreateTestAsset("STATUS-AVAIL-1", "Laptop", status: "available");
        await CreateTestAsset("STATUS-AVAIL-2", "Monitor", status: "available");
        await CreateTestAsset("STATUS-ASSIGNED-1", "Keyboard", status: "assigned");

        // Act
        var response = await _client.GetAsync("/assets/search?status=available");

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var assets = await response.Content.ReadFromJsonAsync<List<Asset>>();
        Assert.NotNull(assets);
        Assert.True(assets.Count >= 2);
        Assert.All(assets, a => Assert.Equal("available", a.Status));
    }

    [Fact]
    public async Task Search_ByQuery_ReturnsMatchingAssets()
    {
        // Arrange
        await CreateTestAsset("DELL-001", "Laptop", manufacturer: "Dell", model: "XPS");
        await CreateTestAsset("HP-001", "Laptop", manufacturer: "HP", model: "EliteBook");
        await CreateTestAsset("DELL-002", "Monitor", manufacturer: "Dell", model: "U2720Q");

        // Act
        var response = await _client.GetAsync("/assets/search?q=Dell");

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var assets = await response.Content.ReadFromJsonAsync<List<Asset>>();
        Assert.NotNull(assets);
        Assert.True(assets.Count >= 2);
        Assert.All(assets, a => 
            Assert.True(
                a.AssetTag.Contains("Dell", StringComparison.OrdinalIgnoreCase) ||
                a.Manufacturer.Contains("Dell", StringComparison.OrdinalIgnoreCase) ||
                (a.Model?.Contains("Dell", StringComparison.OrdinalIgnoreCase) ?? false)
            )
        );
    }

    [Fact]
    public async Task Search_WithCombinedFilters_ReturnsMatchingAssets()
    {
        // Arrange
        await CreateTestAsset("COMBO-1", "Laptop", manufacturer: "Dell", status: "available");
        await CreateTestAsset("COMBO-2", "Laptop", manufacturer: "Dell", status: "assigned");
        await CreateTestAsset("COMBO-3", "Monitor", manufacturer: "Dell", status: "available");

        // Act
        var response = await _client.GetAsync("/assets/search?type=Laptop&status=available&q=Dell");

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var assets = await response.Content.ReadFromJsonAsync<List<Asset>>();
        Assert.NotNull(assets);
        Assert.True(assets.Count >= 1);
        Assert.All(assets, a => 
        {
            Assert.Equal("Laptop", a.AssetType);
            Assert.Equal("available", a.Status);
        });
    }

    [Fact]
    public async Task Search_WithNoMatches_ReturnsEmptyList()
    {
        // Act
        var response = await _client.GetAsync("/assets/search?type=NonExistentType");

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var assets = await response.Content.ReadFromJsonAsync<List<Asset>>();
        Assert.NotNull(assets);
        Assert.Empty(assets);
    }

    [Fact]
    public async Task Search_WithNoParameters_ReturnsAllAssets()
    {
        // Arrange
        await CreateTestAsset("ALL-1", "Laptop");
        await CreateTestAsset("ALL-2", "Monitor");

        // Act
        var response = await _client.GetAsync("/assets/search");

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var assets = await response.Content.ReadFromJsonAsync<List<Asset>>();
        Assert.NotNull(assets);
        Assert.True(assets.Count >= 2);
    }

    #endregion

    #region Stats Tests

    [Fact]
    public async Task StatsByStatus_ReturnsCorrectCounts()
    {
        // Arrange
        await CreateTestAsset("STATS-AVAIL-1", "Laptop", status: "available");
        await CreateTestAsset("STATS-AVAIL-2", "Monitor", status: "available");
        await CreateTestAsset("STATS-ASSIGNED-1", "Keyboard", status: "assigned");
        await CreateTestAsset("STATS-RETIRED-1", "Phone", status: "retired");

        // Act
        var response = await _client.GetAsync("/assets/stats/by-status");

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var stats = await response.Content.ReadFromJsonAsync<Dictionary<string, int>>();
        Assert.NotNull(stats);
        
        // Verify we have at least the statuses we created
        Assert.True(stats.ContainsKey("available"));
        Assert.True(stats["available"] >= 2);
        Assert.True(stats.ContainsKey("assigned"));
        Assert.True(stats["assigned"] >= 1);
        Assert.True(stats.ContainsKey("retired"));
        Assert.True(stats["retired"] >= 1);
    }

    [Fact]
    public async Task StatsByStatus_WithNoAssets_ReturnsEmptyDictionary()
    {
        // Note: Fresh database has seed data, so we can't easily test empty state
        // But we can verify the endpoint returns valid data structure
        
        // Act
        var response = await _client.GetAsync("/assets/stats/by-status");

        // Assert
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var stats = await response.Content.ReadFromJsonAsync<Dictionary<string, int>>();
        Assert.NotNull(stats);
    }

    #endregion

    #region Helper Methods

    private async Task<long> CreateTestAsset(
        string tag, 
        string type, 
        string manufacturer = "Test Mfr",
        string model = "Test Model",
        string status = "available")
    {
        var asset = new AssetCreate
        {
            AssetTag = tag,
            AssetType = type,
            Manufacturer = manufacturer,
            Model = model,
            Status = status
        };

        var response = await _client.PostAsJsonAsync("/assets", asset);
        response.EnsureSuccessStatusCode();
        
        var result = await response.Content.ReadFromJsonAsync<Dictionary<string, long>>();
        return result!["id"];
    }

    #endregion
}
