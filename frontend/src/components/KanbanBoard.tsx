import type { Dataset, KanbanStage } from '../types';
import { KanbanCard } from './KanbanCard';

interface KanbanBoardProps {
  datasets: Dataset[];
  onViewSchema: (id: string) => void;
  onStartMigration: (id: string) => void;
  onReset: (id: string) => void;
  migratingIds: Set<string>;
}

interface ColumnDef {
  stage: KanbanStage;
  label: string;
  icon: string;
  color: string;
}

const COLUMNS: ColumnDef[] = [
  { stage: 'DEVELOPMENT', label: 'Development', icon: '⚡', color: '#4fc3f7' },
  { stage: 'TESTING', label: 'Testing', icon: '🧪', color: '#ab47bc' },
  { stage: 'AWAITING_REVIEW', label: 'Awaiting Review', icon: '👀', color: '#ff7043' },
  { stage: 'MERGED', label: 'Merged', icon: '✓', color: '#66bb6a' },
];

export function KanbanBoard({ datasets, onViewSchema, onStartMigration, onReset, migratingIds }: KanbanBoardProps) {
  const grouped = new Map<KanbanStage, Dataset[]>();
  for (const col of COLUMNS) {
    grouped.set(col.stage, []);
  }
  for (const ds of datasets) {
    if (ds.stage === 'BACKLOG') continue;
    const list = grouped.get(ds.stage);
    if (list) list.push(ds);
  }

  return (
    <div className="kanban-board">
      {COLUMNS.map(col => {
        const items = grouped.get(col.stage) ?? [];
        return (
          <div key={col.stage} className="kanban-column">
            <div className="kanban-column-header" style={{ borderBottomColor: col.color }}>
              <span className="kanban-column-icon">{col.icon}</span>
              <span className="kanban-column-label">{col.label}</span>
              <span className="kanban-column-count" style={{ color: col.color }}>
                {items.length}
              </span>
            </div>
            <div className="kanban-column-body">
              {items.map(ds => (
                <KanbanCard
                  key={ds.id}
                  dataset={ds}
                  onViewSchema={() => onViewSchema(ds.id)}
                  onStartMigration={() => onStartMigration(ds.id)}
                  onReset={() => onReset(ds.id)}
                  isMigrating={migratingIds.has(ds.id)}
                />
              ))}
              {items.length === 0 && (
                <div className="kanban-empty">No datasets</div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
