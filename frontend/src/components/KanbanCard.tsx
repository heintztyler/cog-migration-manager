import type { Dataset } from '../types';

interface KanbanCardProps {
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

export function KanbanCard({ dataset, onViewSchema, onStartMigration, onReset, isMigrating }: KanbanCardProps) {
  const isActive = dataset.stage === 'DEVELOPMENT' || dataset.stage === 'TESTING';
  const canStart = dataset.stage === 'BACKLOG' || dataset.stage === 'SCOPING';
  const isDone = dataset.stage === 'MERGED';

  return (
    <div className={`kanban-card stage-${dataset.stage.toLowerCase().replace('_', '-')}`}>
      <div className="kanban-card-header">
        <span className="kanban-card-name">{dataset.name}</span>
        <span
          className="complexity-dot"
          style={{ backgroundColor: COMPLEXITY_COLORS[dataset.complexity] }}
          title={dataset.complexity}
        />
      </div>

      <div className="kanban-card-meta">
        <span className="kanban-meta-item" title="Source">
          {dataset.source_system}
        </span>
        <span className="kanban-meta-sep">&rarr;</span>
        <span className="kanban-meta-item mono" title="Target">
          {dataset.target_table}
        </span>
      </div>

      <div className="kanban-card-stats">
        <span>{dataset.record_count.toLocaleString()} records</span>
        <span>{dataset.estimated_duration}</span>
      </div>

      <div className="kanban-card-actions">
        <button className="kanban-btn kanban-btn-schema" onClick={onViewSchema} title="View Schemas">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
            <path d="M2 4h12M2 8h12M2 12h8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>

        {canStart && (
          <button
            className="kanban-btn kanban-btn-start"
            onClick={onStartMigration}
            disabled={isMigrating}
            title="Start Migration"
          >
            {isMigrating ? (
              <span className="spinner-sm" />
            ) : (
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path d="M5 3l8 5-8 5V3z" fill="currentColor" />
              </svg>
            )}
          </button>
        )}

        {dataset.session_url && (
          <a
            href={dataset.session_url}
            target="_blank"
            rel="noopener noreferrer"
            className="kanban-btn kanban-btn-devin"
            title="Watch Devin Work"
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" />
              <circle cx="8" cy="8" r="2" fill="currentColor" />
            </svg>
          </a>
        )}

        {isActive && !dataset.session_url && (
          <span className="kanban-btn kanban-btn-devin-demo" title="Demo mode — no live session">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" />
              <circle cx="8" cy="8" r="2" fill="currentColor" />
            </svg>
          </span>
        )}

        {dataset.pr_url && (
          <a
            href={dataset.pr_url}
            target="_blank"
            rel="noopener noreferrer"
            className="kanban-btn kanban-btn-pr"
            title={`View PR #${dataset.pr_number ?? ''}`}
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
              <path d="M5 3v10M11 3v10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              <path d="M5 5l3-2 3 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </a>
        )}

        {isDone && (
          <button className="kanban-btn kanban-btn-reset" onClick={onReset} title="Reset">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
              <path d="M2 8a6 6 0 1 1 1.5 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              <path d="M2 12V8h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
