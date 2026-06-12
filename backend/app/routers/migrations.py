import os
import time
import logging
from fastapi import APIRouter, HTTPException
from app.models import MigrationRequest, MigrationStatus, SessionStatusResponse, KanbanStage
from app.devin_client import DevinClient, build_migration_prompt
from app.legacy_systems import system_alpha, system_bravo
from app.unified_system import target_schema

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/migrations", tags=["migrations"])

devin_client = DevinClient()

REPO_URL = os.environ.get("MIGRATION_REPO_URL", "https://github.com/heintztyler/cog-migration-manager")

# Mock demo progression: after starting, cards advance through stages over time
MOCK_STAGE_DURATIONS = {
    "DEVELOPMENT": 15,
    "TESTING": 10,
    "AWAITING_REVIEW": 10,
}


def _compute_stage_from_state(state: dict) -> KanbanStage:
    """Derive Kanban stage from state dict."""
    if not state:
        return KanbanStage.BACKLOG
    if state.get("pr_merged"):
        return KanbanStage.MERGED
    if state.get("pr_url"):
        return KanbanStage.AWAITING_REVIEW
    status = state.get("status", MigrationStatus.NOT_STARTED)
    if status == MigrationStatus.TESTING:
        return KanbanStage.TESTING
    if status == MigrationStatus.IN_PROGRESS:
        return KanbanStage.DEVELOPMENT
    if status == MigrationStatus.QUEUED:
        return KanbanStage.SCOPING
    if status == MigrationStatus.COMPLETED:
        return KanbanStage.MERGED
    return KanbanStage.BACKLOG


def _maybe_advance_mock(state: dict) -> None:
    """In demo mode (no API key), auto-advance cards through stages over time."""
    if devin_client.is_configured:
        return
    started_at = state.get("started_at")
    if not started_at:
        return

    elapsed = time.time() - started_at
    dev_time = MOCK_STAGE_DURATIONS["DEVELOPMENT"]
    test_time = dev_time + MOCK_STAGE_DURATIONS["TESTING"]
    review_time = test_time + MOCK_STAGE_DURATIONS["AWAITING_REVIEW"]

    if elapsed >= review_time:
        state["status"] = MigrationStatus.COMPLETED
        state["pr_merged"] = True
        state["pr_url"] = state.get("pr_url", f"https://github.com/heintztyler/cog-migration-manager/pull/{state.get('mock_pr', 42)}")
        state["status_message"] = "Migration script merged successfully"
    elif elapsed >= test_time:
        state["status"] = MigrationStatus.COMPLETED
        state["pr_url"] = f"https://github.com/heintztyler/cog-migration-manager/pull/{state.get('mock_pr', 42)}"
        state["pr_number"] = state.get("mock_pr", 42)
        state["status_message"] = "PR opened — awaiting review"
    elif elapsed >= dev_time:
        state["status"] = MigrationStatus.TESTING
        state["status_message"] = "Running transformation validation tests..."
    else:
        state["status_message"] = f"Generating migration script... ({int(elapsed)}s)"


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

    import random
    migration_state[dataset_id] = {
        "status": MigrationStatus.IN_PROGRESS,
        "session_id": result["session_id"],
        "session_url": result["url"],
        "status_message": "Devin session created - analyzing schemas...",
        "started_at": time.time(),
        "mock_pr": random.randint(2, 50),
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
    else:
        _maybe_advance_mock(state)

    stage = _compute_stage_from_state(state)

    return SessionStatusResponse(
        dataset_id=dataset_id,
        session_id=session_id,
        session_url=state.get("session_url", ""),
        status=state.get("status", MigrationStatus.NOT_STARTED),
        status_message=state.get("status_message", ""),
        stage=stage,
        pr_url=state.get("pr_url"),
    )


@router.get("/status")
async def get_all_migration_statuses():
    """Get status of all active migrations."""
    from app.state import migration_state

    statuses = []
    for dataset_id, state in migration_state.items():
        _maybe_advance_mock(state)
        statuses.append({
            "dataset_id": dataset_id,
            "session_id": state.get("session_id"),
            "session_url": state.get("session_url"),
            "status": state.get("status", MigrationStatus.NOT_STARTED),
            "status_message": state.get("status_message", ""),
            "pr_url": state.get("pr_url"),
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
    from app.state import custom_datasets
    for ds in target_schema.MIGRATION_DATASETS + custom_datasets:
        if ds["id"] == dataset_id:
            return ds
    return None
