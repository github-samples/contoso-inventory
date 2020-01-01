// The endpoint integration tests spin up WebApplicationFactory instances that
// read ASSETS_DB_PATH from a process-global environment variable. Running test
// classes in parallel races on that variable and causes SQLite write contention,
// so disable cross-class parallelization. Methods within a class already run
// sequentially.
[assembly: Xunit.CollectionBehavior(DisableTestParallelization = true)]
