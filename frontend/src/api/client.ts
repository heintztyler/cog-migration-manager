import type { Dataset, SchemaInfo, MigrationStatusResponse } from '../types';

const BASE = '/api';

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

export async function fetchDatasets(): Promise<Dataset[]> {
  return fetchJSON<Dataset[]>('/datasets');
}

export async function fetchSourceSchema(datasetId: string): Promise<SchemaInfo> {
  return fetchJSON<SchemaInfo>(`/datasets/${datasetId}/source-schema`);
}

export async function fetchTargetSchema(datasetId: string): Promise<SchemaInfo> {
  return fetchJSON<SchemaInfo>(`/datasets/${datasetId}/target-schema`);
}

export async function fetchSampleData(datasetId: string): Promise<{ records: Record<string, unknown>[] }> {
  return fetchJSON(`/datasets/${datasetId}/sample-data`);
}

export async function startMigration(datasetId: string): Promise<{
  dataset_id: string;
  session_id: string;
  session_url: string;
  status: string;
  message: string;
}> {
  return fetchJSON('/migrations/start', {
    method: 'POST',
    body: JSON.stringify({ dataset_id: datasetId }),
  });
}

export async function fetchMigrationStatus(datasetId: string): Promise<MigrationStatusResponse> {
  return fetchJSON<MigrationStatusResponse>(`/migrations/status/${datasetId}`);
}

export async function resetMigration(datasetId: string): Promise<void> {
  await fetchJSON(`/migrations/reset/${datasetId}`, { method: 'POST' });
}
