from pydantic import BaseModel
from typing import Optional
from enum import Enum


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
    session_id: Optional[str] = None
    session_url: Optional[str] = None


class MigrationRequest(BaseModel):
    dataset_id: str


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
    last_update: Optional[str] = None


class SystemInfo(BaseModel):
    name: str
    description: str
    tables: list[str]
