export interface SchemaField {
  name: string;
  type: string;
  description: string;
  example: string | null;
}

export interface SchemaInfo {
  table_name: string;
  description: string;
  fields: SchemaField[];
}

export type MigrationStatus =
  | 'NOT_STARTED'
  | 'QUEUED'
  | 'IN_PROGRESS'
  | 'TESTING'
  | 'COMPLETED'
  | 'FAILED';

export type Complexity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface Dataset {
  id: string;
  name: string;
  description: string;
  source_system: string;
  source_table: string;
  target_table: string;
  record_count: number;
  complexity: Complexity;
  estimated_duration: string;
  status: MigrationStatus;
  session_id: string | null;
  session_url: string | null;
}

export interface MigrationStatusResponse {
  dataset_id: string;
  session_id: string;
  session_url: string;
  status: string;
  status_message: string;
  last_update: string | null;
}
