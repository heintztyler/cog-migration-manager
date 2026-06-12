import os
import logging
from fastapi import APIRouter, HTTPException
from app.models import MigrationRequest, MigrationStatus, SessionStatusResponse
from app.devin_client import DevinClient, build_migration_prompt
from app.legacy_systems import system_alpha, system_bravo
from app.unified_system import target_schema

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/migrations", tags=["migrations"])

devin_client = DevinClient()

REPO_URL = os.environ.get("MIGRATION_REPO_URL", "https://github.com/heintztyler/erp-migration-accelerator")


@router.post("/start")
async def start_migration(request: MigrationRequest):
    """Kick off a Devin session to generate a migration script for a dataset."""
    from app.state import migration_state

    dataset_id = request.dataset_id
    ds_def = _find_dataset_def(dataset_id)
    if not ds_def:
        raise HTTPException(status_code=404, detail="Dataset not found")

    current_state = migration_state.get(dataset_id, {})
    if current_state.get("status") in [MigrationStatus.IN_PROGRESS, MigrationStatus.QUEUED]:
        raise HTTPException(
            status_code=409,
            detail="Migration already in progress for this dataset",
        )

    source_table = ds_def["source_table"].split(" + ")[0]
    source_system_name = ds_def["source_system"].split(" + ")[0]

    if source_system_name == "GCSS-Army":
        source_schema = system_alpha.SCHEMAS.get(source_table, {})
        sample_data = system_alpha.SAMPLE_DATA.get(source_table, [])
    else:
        source_schema = system_bravo.SCHEMAS.get(source_table, {})
        sample_data = system_bravo.SAMPLE_DATA.get(source_table, [])

    target_table = ds_def["target_table"]
    target_schema_def = target_schema.SCHEMAS.get(target_table, {})

    prompt = build_migration_prompt(
        dataset_id=dataset_id,
        dataset_name=ds_def["name"],
        source_system=source_system_name,
        source_schema=source_schema,
        target_schema=target_schema_def,
        sample_data=sample_data,
        repo_url=REPO_URL,
    )

    title = f"ERP Migration: {ds_def['name']} ({source_system_name} -> ALERP)"

    result = await devin_client.create_session(prompt=prompt, title=title)

    migration_state[dataset_id] = {
        "status": MigrationStatus.IN_PROGRESS,
        "session_id": result["session_id"],
        "session_url": result["url"],
        "status_message": "Devin session created - analyzing schemas...",
    }

    return {
        "dataset_id": dataset_id,
        "session_id": result["session_id"],
        "session_url": result["url"],
        "status": MigrationStatus.IN_PROGRESS,
        "message": f"Migration session started for {ds_def['name']}",
    }


@router.get("/status/{dataset_id}", response_model=SessionStatusResponse)
async def get_migration_status(dataset_id: str):
    """Get the current status of a migration session."""
    from app.state import migration_state

    state = migration_state.get(dataset_id)
    if not state:
        raise HTTPException(status_code=404, detail="No migration session for this dataset")

    session_id = state.get("session_id", "")

    if devin_client.is_configured and session_id:
        api_status = await devin_client.get_session_status(session_id)
        devin_status = api_status.get("status", "unknown")

        if devin_status in ("finished", "stopped"):
            state["status"] = MigrationStatus.COMPLETED
            state["status_message"] = "Migration script generated and committed successfully"
        elif devin_status == "error":
            state["status"] = MigrationStatus.FAILED
            state["status_message"] = api_status.get("status_message", "Session encountered an error")
        else:
            state["status_message"] = api_status.get("status_message", state.get("status_message", ""))

    return SessionStatusResponse(
        dataset_id=dataset_id,
        session_id=session_id,
        session_url=state.get("session_url", ""),
        status=state.get("status", MigrationStatus.NOT_STARTED),
        status_message=state.get("status_message", ""),
    )


@router.get("/status")
async def get_all_migration_statuses():
    """Get status of all active migrations."""
    from app.state import migration_state

    statuses = []
    for dataset_id, state in migration_state.items():
        statuses.append({
            "dataset_id": dataset_id,
            "session_id": state.get("session_id"),
            "session_url": state.get("session_url"),
            "status": state.get("status", MigrationStatus.NOT_STARTED),
            "status_message": state.get("status_message", ""),
        })
    return statuses


@router.post("/reset/{dataset_id}")
async def reset_migration(dataset_id: str):
    """Reset a migration dataset back to NOT_STARTED."""
    from app.state import migration_state

    if dataset_id in migration_state:
        del migration_state[dataset_id]
    return {"dataset_id": dataset_id, "status": MigrationStatus.NOT_STARTED}


def _find_dataset_def(dataset_id: str) -> dict | None:
    for ds in target_schema.MIGRATION_DATASETS:
        if ds["id"] == dataset_id:
            return ds
    return None
