import { useState, useEffect, useRef } from 'react';
import type { AvailableSchema, Complexity } from '../types';
import { fetchAvailableSchemas } from '../api/client';

interface CreateDatasetModalProps {
  onClose: () => void;
  onCreate: (payload: {
    name: string;
    description: string;
    source_system: string;
    source_table: string;
    target_table: string;
    record_count: number;
    complexity: Complexity;
    estimated_duration: string;
  }) => void;
}

export function CreateDatasetModal({ onClose, onCreate }: CreateDatasetModalProps) {
  const [sourceSchemas, setSourceSchemas] = useState<AvailableSchema[]>([]);
  const [targetSchemas, setTargetSchemas] = useState<AvailableSchema[]>([]);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [sourceIdx, setSourceIdx] = useState<number>(-1);
  const [targetIdx, setTargetIdx] = useState<number>(-1);
  const [recordCount, setRecordCount] = useState(10000);
  const [complexity, setComplexity] = useState<Complexity>('MEDIUM');
  const [duration, setDuration] = useState('45 min');
  const [importOpen, setImportOpen] = useState(false);
  const importRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (importRef.current && !importRef.current.contains(e.target as Node)) {
        setImportOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  useEffect(() => {
    fetchAvailableSchemas().then(data => {
      setSourceSchemas(data.source_schemas);
      setTargetSchemas(data.target_schemas);
    });
  }, []);

  const selectedSource = sourceIdx >= 0 ? sourceSchemas[sourceIdx] : null;
  const selectedTarget = targetIdx >= 0 ? targetSchemas[targetIdx] : null;

  const canSubmit = name && selectedSource && selectedTarget;

  const handleSubmit = () => {
    if (!canSubmit || !selectedSource || !selectedTarget) return;
    onCreate({
      name,
      description: description || `Migrate ${selectedSource.table} from ${selectedSource.system} to ${selectedTarget.table} in ALERP.`,
      source_system: selectedSource.system ?? 'Unknown',
      source_table: selectedSource.table,
      target_table: selectedTarget.table,
      record_count: recordCount,
      complexity,
      estimated_duration: duration,
    });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal create-dataset-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Create Migration Dataset</h2>
          <div className="header-actions">
            <div className="import-dropdown" ref={importRef}>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setImportOpen(!importOpen)}
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M7 1v9M4 7l3 3 3-3M2 12h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                Import
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none" style={{ marginLeft: 2 }}>
                  <path d="M2.5 4l2.5 2.5L7.5 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
              {importOpen && (
                <div className="import-menu">
                  <button className="import-menu-item" onClick={() => { setImportOpen(false); }}>
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <rect x="1" y="1" width="14" height="14" rx="3" stroke="currentColor" strokeWidth="1.2" />
                      <circle cx="8" cy="8" r="2.5" stroke="currentColor" strokeWidth="1.2" />
                    </svg>
                    Import from Linear
                  </button>
                  <button className="import-menu-item" onClick={() => { setImportOpen(false); }}>
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path d="M2 5.5A3.5 3.5 0 015.5 2h2A3.5 3.5 0 0111 5.5v1A3.5 3.5 0 017.5 10h-2A3.5 3.5 0 012 6.5v-1z" stroke="currentColor" strokeWidth="1.2" />
                      <path d="M5 10v1.5A3.5 3.5 0 008.5 15h2a3.5 3.5 0 003.5-3.5v-1A3.5 3.5 0 0010.5 7h-2" stroke="currentColor" strokeWidth="1.2" />
                    </svg>
                    Import from Jira
                  </button>
                </div>
              )}
            </div>
          <button className="modal-close" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M5 5l10 10M15 5l-10 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
          </div>
        </div>

        <div className="create-form">
          <div className="form-group">
            <label>Dataset Name</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g., Personnel Records Migration"
            />
          </div>

          <div className="form-group">
            <label>Description (optional)</label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Describe the migration scope..."
              rows={2}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Source Schema</label>
              <select value={sourceIdx} onChange={e => setSourceIdx(Number(e.target.value))}>
                <option value={-1}>Select source...</option>
                {sourceSchemas.map((s, i) => (
                  <option key={i} value={i}>
                    [{s.system}] {s.table} ({s.field_count} fields)
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Target Schema</label>
              <select value={targetIdx} onChange={e => setTargetIdx(Number(e.target.value))}>
                <option value={-1}>Select target...</option>
                {targetSchemas.map((s, i) => (
                  <option key={i} value={i}>
                    {s.table} ({s.field_count} fields)
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Record Count</label>
              <input
                type="number"
                value={recordCount}
                onChange={e => setRecordCount(Number(e.target.value))}
                min={1}
              />
            </div>

            <div className="form-group">
              <label>Complexity</label>
              <select value={complexity} onChange={e => setComplexity(e.target.value as Complexity)}>
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="CRITICAL">Critical</option>
              </select>
            </div>

            <div className="form-group">
              <label>Est. Duration</label>
              <input
                type="text"
                value={duration}
                onChange={e => setDuration(e.target.value)}
                placeholder="e.g., 45 min"
              />
            </div>
          </div>

          <div className="form-actions">
            <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button className="btn btn-primary" onClick={handleSubmit} disabled={!canSubmit}>
              Create Dataset
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
