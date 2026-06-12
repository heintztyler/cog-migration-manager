import { useState, useEffect } from 'react';
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
          <button className="modal-close" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M5 5l10 10M15 5l-10 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
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
