"""In-memory state for migration sessions. In production, this would be persisted."""

migration_state: dict[str, dict] = {}
custom_datasets: list[dict] = []
