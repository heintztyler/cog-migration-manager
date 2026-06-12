from pydantic import BaseModel
from typing import Optional
from enum import Enum


class KanbanStage(str, Enum):
    BACKLOG = "BACKLOG"
    SCOPING = "SCOPING"
    DEVELOPMENT = "DEVELOPMENT"
    TESTING = "TESTING"
    AWAITING_REVIEW = "AWAITING_REVIEW"
    MERGED = "MERGED"


class MigrationStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    TESTING = "TESTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Complexity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SchemaField(BaseModel):
    name: str
    type: str
    description: str
    example: Optional[str] = None


class SchemaInfo(BaseModel):
    table_name: str
    description: str
    fields: list[SchemaField]


class DatasetInfo(BaseModel):
    id: str
    name: str
    description: str
    source_system: str
    source_table: str
    target_table: str
    record_count: int
    complexity: Complexity
    estimated_duration: str
    status: MigrationStatus
    stage: KanbanStage
    session_id: Optional[str] = None
    session_url: Optional[str] = None
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None


class MigrationRequest(BaseModel):
    dataset_id: str


class CreateDatasetRequest(BaseModel):
    name: str
    description: str
    source_system: str
    source_table: str
    target_table: str
    record_count: int
    complexity: Complexity
    estimated_duration: str


class MigrationSession(BaseModel):
    dataset_id: str
    session_id: str
    session_url: str
    status: MigrationStatus
    status_message: Optional[str] = None


class SessionStatusResponse(BaseModel):
    dataset_id: str
    session_id: str
    session_url: str
    status: str
    status_message: str
    stage: KanbanStage
    pr_url: Optional[str] = None
    last_update: Optional[str] = None


class SystemInfo(BaseModel):
    name: str
    description: str
    tables: list[str]
