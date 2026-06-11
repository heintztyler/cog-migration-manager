from fastapi import APIRouter
from app.models import DatasetInfo, SchemaInfo, SchemaField, SystemInfo
from app.legacy_systems import system_alpha, system_bravo
from app.unified_system import target_schema

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.get("", response_model=list[DatasetInfo])
async def list_datasets():
    """List all migration datasets with their current status."""
    from app.state import migration_state

    datasets = []
    for ds in target_schema.MIGRATION_DATASETS:
        state = migration_state.get(ds["id"], {})
        datasets.append(
            DatasetInfo(
                id=ds["id"],
                name=ds["name"],
                description=ds["description"],
                source_system=ds["source_system"],
                source_table=ds["source_table"],
                target_table=ds["target_table"],
                record_count=ds["record_count"],
                complexity=ds["complexity"],
                estimated_duration=ds["estimated_duration"],
                status=state.get("status", ds["status"]),
                session_id=state.get("session_id"),
                session_url=state.get("session_url"),
            )
        )
    return datasets


@router.get("/{dataset_id}", response_model=DatasetInfo)
async def get_dataset(dataset_id: str):
    """Get details for a specific dataset."""
    from app.state import migration_state

    for ds in target_schema.MIGRATION_DATASETS:
        if ds["id"] == dataset_id:
            state = migration_state.get(ds["id"], {})
            return DatasetInfo(
                id=ds["id"],
                name=ds["name"],
                description=ds["description"],
                source_system=ds["source_system"],
                source_table=ds["source_table"],
                target_table=ds["target_table"],
                record_count=ds["record_count"],
                complexity=ds["complexity"],
                estimated_duration=ds["estimated_duration"],
                status=state.get("status", ds["status"]),
                session_id=state.get("session_id"),
                session_url=state.get("session_url"),
            )
    return {"error": "Dataset not found"}


@router.get("/{dataset_id}/source-schema", response_model=SchemaInfo)
async def get_source_schema(dataset_id: str):
    """Get the source schema for a dataset."""
    schema = _find_source_schema(dataset_id)
    if not schema:
        return {"error": "Schema not found"}
    return SchemaInfo(
        table_name=schema["table_name"],
        description=schema["description"],
        fields=[SchemaField(**f) for f in schema["fields"]],
    )


@router.get("/{dataset_id}/target-schema", response_model=SchemaInfo)
async def get_target_schema(dataset_id: str):
    """Get the target schema for a dataset."""
    ds_def = _find_dataset_def(dataset_id)
    if not ds_def:
        return {"error": "Dataset not found"}

    target_table = ds_def["target_table"]
    schema = target_schema.SCHEMAS.get(target_table)
    if not schema:
        return {"error": "Target schema not found"}

    return SchemaInfo(
        table_name=schema["table_name"],
        description=schema["description"],
        fields=[SchemaField(**f) for f in schema["fields"]],
    )


@router.get("/{dataset_id}/sample-data")
async def get_sample_data(dataset_id: str):
    """Get sample data from the source system."""
    ds_def = _find_dataset_def(dataset_id)
    if not ds_def:
        return {"error": "Dataset not found"}

    source_table = ds_def["source_table"].split(" + ")[0]
    source_system = ds_def["source_system"].split(" + ")[0]

    if source_system == "GCSS-Army":
        data = system_alpha.SAMPLE_DATA.get(source_table, [])
    else:
        data = system_bravo.SAMPLE_DATA.get(source_table, [])

    return {"dataset_id": dataset_id, "source_table": source_table, "records": data}


@router.get("/systems/overview", response_model=list[SystemInfo])
async def get_systems_overview():
    """Get overview of all systems (legacy + unified)."""
    return [
        SystemInfo(
            name=system_alpha.SYSTEM_NAME,
            description=system_alpha.SYSTEM_DESCRIPTION,
            tables=list(system_alpha.SCHEMAS.keys()),
        ),
        SystemInfo(
            name=system_bravo.SYSTEM_NAME,
            description=system_bravo.SYSTEM_DESCRIPTION,
            tables=list(system_bravo.SCHEMAS.keys()),
        ),
        SystemInfo(
            name=target_schema.SYSTEM_NAME,
            description=target_schema.SYSTEM_DESCRIPTION,
            tables=list(target_schema.SCHEMAS.keys()),
        ),
    ]


def _find_dataset_def(dataset_id: str) -> dict | None:
    for ds in target_schema.MIGRATION_DATASETS:
        if ds["id"] == dataset_id:
            return ds
    return None


def _find_source_schema(dataset_id: str) -> dict | None:
    ds_def = _find_dataset_def(dataset_id)
    if not ds_def:
        return None

    source_table = ds_def["source_table"].split(" + ")[0]
    source_system = ds_def["source_system"].split(" + ")[0]

    if source_system == "GCSS-Army":
        return system_alpha.SCHEMAS.get(source_table)
    elif source_system == "LMP":
        return system_bravo.SCHEMAS.get(source_table)
    return None
