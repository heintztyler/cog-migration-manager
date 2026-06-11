import type { Dataset } from '../types';

interface DatasetCardProps {
  dataset: Dataset;
  onViewSchema: () => void;
  onStartMigration: () => void;
  onReset: () => void;
  isMigrating: boolean;
}

const COMPLEXITY_COLORS: Record<string, string> = {
  LOW: '#66bb6a',
  MEDIUM: '#ffa726',
  HIGH: '#ef5350',
  CRITICAL: '#ab47bc',
};

const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  NOT_STARTED: { label: 'Not Started', className: 'status-not-started' },
  QUEUED: { label: 'Queued', className: 'status-queued' },
  IN_PROGRESS: { label: 'In Progress', className: 'status-in-progress' },
  TESTING: { label: 'Testing', className: 'status-testing' },
  COMPLETED: { label: 'Completed', className: 'status-completed' },
  FAILED: { label: 'Failed', className: 'status-failed' },
};

export function DatasetCard({ dataset, onViewSchema, onStartMigration, onReset, isMigrating }: DatasetCardProps) {
  const statusConfig = STATUS_CONFIG[dataset.status] ?? STATUS_CONFIG.NOT_STARTED;
  const isActive = dataset.status === 'IN_PROGRESS' || dataset.status === 'QUEUED' || dataset.status === 'TESTING';
  const canStart = dataset.status === 'NOT_STARTED' || dataset.status === 'FAILED';

  return (
    <div className={`dataset-card ${statusConfig.className}`}>
      <div className="dataset-header">
        <div className="dataset-title-row">
          <h3 className="dataset-name">{dataset.name}</h3>
          <span
            className="complexity-badge"
            style={{ backgroundColor: COMPLEXITY_COLORS[dataset.complexity] }}
          >
            {dataset.complexity}
          </span>
        </div>
        <span className={`status-badge ${statusConfig.className}`}>
          {isActive && <span className="status-pulse" />}
          {statusConfig.label}
        </span>
      </div>

      <p className="dataset-description">{dataset.description}</p>

      <div className="dataset-meta">
        <div className="meta-item">
          <span className="meta-label">Source</span>
          <span className="meta-value">{dataset.source_system}</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Source Table</span>
          <span className="meta-value mono">{dataset.source_table}</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Target Table</span>
          <span className="meta-value mono">{dataset.target_table}</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Records</span>
          <span className="meta-value">{dataset.record_count.toLocaleString()}</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Est. Duration</span>
          <span className="meta-value">{dataset.estimated_duration}</span>
        </div>
      </div>

      <div className="dataset-actions">
        <button className="btn btn-secondary" onClick={onViewSchema}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M2 4h12M2 8h12M2 12h8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          View Schemas
        </button>

        {canStart && (
          <button
            className="btn btn-primary"
            onClick={onStartMigration}
            disabled={isMigrating}
          >
            {isMigrating ? (
              <>
                <span className="spinner" />
                Launching...
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M5 3l8 5-8 5V3z" fill="currentColor" />
                </svg>
                Start Migration
              </>
            )}
          </button>
        )}

        {isActive && dataset.session_url && (
          <a
            href={dataset.session_url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-devin"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" />
              <circle cx="8" cy="8" r="2" fill="currentColor" />
            </svg>
            Watch Devin Work
          </a>
        )}

        {dataset.status === 'COMPLETED' && dataset.session_url && (
          <a
            href={dataset.session_url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary"
          >
            View Session
          </a>
        )}

        {(dataset.status === 'COMPLETED' || dataset.status === 'FAILED') && (
          <button className="btn btn-ghost" onClick={onReset}>
            Reset
          </button>
        )}
      </div>
    </div>
  );
}
