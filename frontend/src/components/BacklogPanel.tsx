import type { Dataset } from '../types';

interface BacklogPanelProps {
  datasets: Dataset[];
  onStartMigration: (id: string) => void;
  onViewSchema: (id: string) => void;
  onCreateNew: () => void;
  migratingIds: Set<string>;
}

const COMPLEXITY_COLORS: Record<string, string> = {
  LOW: '#66bb6a',
  MEDIUM: '#ffa726',
  HIGH: '#ef5350',
  CRITICAL: '#ab47bc',
};

export function BacklogPanel({ datasets, onStartMigration, onViewSchema, onCreateNew, migratingIds }: BacklogPanelProps) {
  return (
    <div className="backlog-panel">
      <div className="backlog-header">
        <div className="backlog-title-row">
          <span className="backlog-icon">📋</span>
          <h3>Available Datasets</h3>
          <span className="backlog-count">{datasets.length}</span>
        </div>
        <button className="btn btn-primary btn-sm" onClick={onCreateNew}>
          + New Dataset
        </button>
      </div>
      <div className="backlog-list">
        {datasets.map(ds => (
          <div key={ds.id} className="backlog-item">
            <div className="backlog-item-header">
              <span className="backlog-item-name">{ds.name}</span>
              <span
                className="complexity-dot"
                style={{ backgroundColor: COMPLEXITY_COLORS[ds.complexity] }}
                title={ds.complexity}
              />
            </div>
            <div className="backlog-item-info">
              <span className="mono">{ds.source_table.split(' + ')[0]}</span>
              <span className="backlog-arrow">&rarr;</span>
              <span className="mono">{ds.target_table}</span>
            </div>
            <div className="backlog-item-stats">
              <span>{ds.record_count.toLocaleString()} records</span>
              <span className="backlog-item-complexity" style={{ color: COMPLEXITY_COLORS[ds.complexity] }}>
                {ds.complexity}
              </span>
            </div>
            <div className="backlog-item-actions">
              <button className="kanban-btn kanban-btn-schema" onClick={() => onViewSchema(ds.id)} title="View Schemas">
                <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
                  <path d="M2 4h12M2 8h12M2 12h8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
                Schemas
              </button>
              <button
                className="kanban-btn kanban-btn-start"
                onClick={() => onStartMigration(ds.id)}
                disabled={migratingIds.has(ds.id)}
                title="Start Migration"
              >
                {migratingIds.has(ds.id) ? (
                  <span className="spinner-sm" />
                ) : (
                  <>
                    <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
                      <path d="M5 3l8 5-8 5V3z" fill="currentColor" />
                    </svg>
                    Migrate
                  </>
                )}
              </button>
            </div>
          </div>
        ))}
        {datasets.length === 0 && (
          <div className="backlog-empty">
            All datasets have been started. Click "+ New Dataset" to add more.
          </div>
        )}
      </div>
    </div>
  );
}
