APP_NAME = "Zima Storage Manager"
DEFAULT_DB = "/var/lib/casaos/db/local-storage.db"
DEFAULT_SERVICE = "auto"
SERVICE_CANDIDATES = [
    "zimaos-local-storage.service",
    "casaos-local-storage.service",
    "local-storage.service",
]
DEFAULT_MOUNT_ROOTS = ["/media", "/DATA/.media", "/var/lib/casaos_data/.media"]
DB_CANDIDATES = [
    "/var/lib/casaos/db/local-storage.db",
    "/var/lib/zimaos/db/local-storage.db",
]
