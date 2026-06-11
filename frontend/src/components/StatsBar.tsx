import type { Dataset } from '../types';

interface StatsBarProps {
  datasets: Dataset[];
}

export function StatsBar({ datasets }: StatsBarProps) {
  const total = datasets.length;
  const completed = datasets.filter(d => d.status === 'COMPLETED').length;
  const inProgress = datasets.filter(d => d.status === 'IN_PROGRESS' || d.status === 'QUEUED' || d.status === 'TESTING').length;
  const notStarted = datasets.filter(d => d.status === 'NOT_STARTED').length;
  const failed = datasets.filter(d => d.status === 'FAILED').length;
  const totalRecords = datasets.reduce((sum, d) => sum + d.record_count, 0);
  const migratedRecords = datasets
    .filter(d => d.status === 'COMPLETED')
    .reduce((sum, d) => sum + d.record_count, 0);

  const progressPct = total > 0 ? Math.round((completed / total) * 100) : 0;

  return (
    <section className="stats-bar">
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{total}</div>
          <div className="stat-label">Total Datasets</div>
        </div>
        <div className="stat-card stat-completed">
          <div className="stat-value">{completed}</div>
          <div className="stat-label">Completed</div>
        </div>
        <div className="stat-card stat-progress">
          <div className="stat-value">{inProgress}</div>
          <div className="stat-label">In Progress</div>
        </div>
        <div className="stat-card stat-pending">
          <div className="stat-value">{notStarted}</div>
          <div className="stat-label">Not Started</div>
        </div>
        {failed > 0 && (
          <div className="stat-card stat-failed">
            <div className="stat-value">{failed}</div>
            <div className="stat-label">Failed</div>
          </div>
        )}
        <div className="stat-card">
          <div className="stat-value">{totalRecords.toLocaleString()}</div>
          <div className="stat-label">Total Records</div>
        </div>
        <div className="stat-card stat-completed">
          <div className="stat-value">{migratedRecords.toLocaleString()}</div>
          <div className="stat-label">Records Migrated</div>
        </div>
      </div>
      <div className="progress-bar-container">
        <div className="progress-bar-label">
          <span>Overall Migration Progress</span>
          <span>{progressPct}%</span>
        </div>
        <div className="progress-bar">
          <div className="progress-bar-fill" style={{ width: `${progressPct}%` }} />
        </div>
      </div>
    </section>
  );
}
