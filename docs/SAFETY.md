# Safety Model

ZSM deliberately does not format, partition, relabel, mount, unmount or delete directories automatically. Those operations can threaten user data and require context-specific decisions.

A rename validates the UUID and destination, rejects duplicate records and non-empty destination directories, creates an SQLite backup, stops the configured service, performs one parameterized update in a transaction, restarts the service and verifies the result. On failure it restores the snapshot.
