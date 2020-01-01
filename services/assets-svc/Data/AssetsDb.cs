using Dapper;
using Microsoft.Data.Sqlite;

namespace Contoso.Assets.Data;

public class AssetsDb
{
    private readonly string _connectionString;

    public AssetsDb(string path)
    {
        var dir = Path.GetDirectoryName(path);
        if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir))
        {
            Directory.CreateDirectory(dir);
        }
        _connectionString = $"Data Source={path}";
    }

    public SqliteConnection Open()
    {
        var conn = new SqliteConnection(_connectionString);
        conn.Open();
        return conn;
    }

    public void Initialize()
    {
        using var conn = Open();
        conn.Execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_tag TEXT NOT NULL UNIQUE,
                asset_type TEXT NOT NULL,
                manufacturer TEXT NOT NULL,
                model TEXT NOT NULL,
                serial_number TEXT,
                purchase_date TEXT,
                warranty_expiry TEXT,
                status TEXT NOT NULL,
                notes TEXT,
                qr_payload TEXT
            );
        """);

        // Migration: add qr_payload to databases created before QR support existed.
        var columns = conn.Query<string>("SELECT name FROM pragma_table_info('assets');");
        if (!columns.Contains("qr_payload"))
        {
            conn.Execute("ALTER TABLE assets ADD COLUMN qr_payload TEXT;");
        }

        var count = conn.ExecuteScalar<long>("SELECT COUNT(*) FROM assets;");
        if (count == 0)
        {
            SeedData.Apply(conn);
        }

        // Backfill the deep-link payload for any rows missing it (seed rows and
        // assets that already existed before this column was added). The payload
        // needs the asset id, which only exists after the row is inserted.
        conn.Execute(
            $"UPDATE assets SET qr_payload = @base || id WHERE qr_payload IS NULL OR qr_payload = '';",
            new { @base = QrPayload.DeepLinkBase() });
    }
}
