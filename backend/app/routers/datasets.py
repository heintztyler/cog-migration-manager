import uuid
from fastapi import APIRouter, HTTPException
from app.models import (
    DatasetInfo, SchemaInfo, SchemaField, SystemInfo,
    CreateDatasetRequest, KanbanStage, MigrationStatus, Complexity,
)
from app.legacy_systems import system_alpha, system_bravo
from app.unified_system import target_schema

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


def _compute_stage(state: dict) -> KanbanStage:
    """Derive the Kanban stage from migration state."""
    from app.routers.migrations import _maybe_advance_mock
    if state:
        _maybe_advance_mock(state)
    if not state:
        return KanbanStage.BACKLOG
    status = state.get("status", MigrationStatus.NOT_STARTED)
    if state.get("pr_merged"):
        return KanbanStage.MERGED
    if state.get("pr_url"):
        return KanbanStage.AWAITING_REVIEW
    if status == MigrationStatus.TESTING:
        return KanbanStage.TESTING
    if status == MigrationStatus.IN_PROGRESS:
        return KanbanStage.DEVELOPMENT
    if status in (MigrationStatus.QUEUED,):
        return KanbanStage.SCOPING
    if status == MigrationStatus.COMPLETED:
        return KanbanStage.MERGED
    return KanbanStage.BACKLOG


@router.get("", response_model=list[DatasetInfo])
async def list_datasets():
    """List all migration datasets with their current status and Kanban stage."""
    from app.state import migration_state, custom_datasets

    datasets = []
    for ds in target_schema.MIGRATION_DATASETS:
        state = migration_state.get(ds["id"], {})
        stage = _compute_stage(state)
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
                stage=stage,
                session_id=state.get("session_id"),
                session_url=state.get("session_url"),
                pr_url=state.get("pr_url"),
                pr_number=state.get("pr_number"),
            )
        )

    for ds in custom_datasets:
        state = migration_state.get(ds["id"], {})
        stage = _compute_stage(state)
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
                status=state.get("status", "NOT_STARTED"),
                stage=stage,
                session_id=state.get("session_id"),
                session_url=state.get("session_url"),
                pr_url=state.get("pr_url"),
                pr_number=state.get("pr_number"),
            )
        )
    return datasets


@router.post("", response_model=DatasetInfo)
async def create_dataset(request: CreateDatasetRequest):
    """Create a new custom migration dataset."""
    from app.state import custom_datasets

    dataset_id = f"custom-{uuid.uuid4().hex[:8]}"
    ds = {
        "id": dataset_id,
        "name": request.name,
        "description": request.description,
        "source_system": request.source_system,
        "source_table": request.source_table,
        "target_table": request.target_table,
        "record_count": request.record_count,
        "complexity": request.complexity,
        "estimated_duration": request.estimated_duration,
    }
    custom_datasets.append(ds)

    return DatasetInfo(
        id=dataset_id,
        name=request.name,
        description=request.description,
        source_system=request.source_system,
        source_table=request.source_table,
        target_table=request.target_table,
        record_count=request.record_count,
        complexity=request.complexity,
        estimated_duration=request.estimated_duration,
        status=MigrationStatus.NOT_STARTED,
        stage=KanbanStage.BACKLOG,
    )


@router.get("/schemas/available")
async def get_available_schemas():
    """Get lists of available source and target schemas for dataset creation."""
    source_schemas = []
    for table_name, schema in system_alpha.SCHEMAS.items():
        source_schemas.append({
            "system": "GCSS-Army",
            "table": table_name,
            "description": schema["description"],
            "field_count": len(schema["fields"]),
        })
    for table_name, schema in system_bravo.SCHEMAS.items():
        source_schemas.append({
            "system": "LMP",
            "table": table_name,
            "description": schema["description"],
            "field_count": len(schema["fields"]),
        })

    target_schemas = []
    for table_name, schema in target_schema.SCHEMAS.items():
        target_schemas.append({
            "table": table_name,
            "description": schema["description"],
            "field_count": len(schema["fields"]),
        })

    return {"source_schemas": source_schemas, "target_schemas": target_schemas}


@router.get("/{dataset_id}", response_model=DatasetInfo)
async def get_dataset(dataset_id: str):
    """Get details for a specific dataset."""
    from app.state import migration_state, custom_datasets

    for ds in target_schema.MIGRATION_DATASETS + custom_datasets:
        if ds["id"] == dataset_id:
            state = migration_state.get(ds["id"], {})
            stage = _compute_stage(state)
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
                status=state.get("status", ds.get("status", "NOT_STARTED")),
                stage=stage,
                session_id=state.get("session_id"),
                session_url=state.get("session_url"),
                pr_url=state.get("pr_url"),
                pr_number=state.get("pr_number"),
            )
    raise HTTPException(status_code=404, detail="Dataset not found")


@router.get("/{dataset_id}/source-schema", response_model=SchemaInfo)
async def get_source_schema(dataset_id: str):
    """Get the source schema for a dataset."""
    schema = _find_source_schema(dataset_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
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
        raise HTTPException(status_code=404, detail="Dataset not found")

    target_table = ds_def["target_table"]
    schema = target_schema.SCHEMAS.get(target_table)
    if not schema:
        raise HTTPException(status_code=404, detail="Target schema not found")

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
        raise HTTPException(status_code=404, detail="Dataset not found")

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
    from app.state import custom_datasets
    for ds in target_schema.MIGRATION_DATASETS + custom_datasets:
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
