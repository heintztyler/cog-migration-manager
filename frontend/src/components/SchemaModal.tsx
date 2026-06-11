import type { SchemaInfo } from '../types';

interface SchemaModalProps {
  datasetId: string;
  datasetName: string;
  sourceSchema: SchemaInfo;
  targetSchema: SchemaInfo;
  onClose: () => void;
}

export function SchemaModal({ datasetName, sourceSchema, targetSchema, onClose }: SchemaModalProps) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Schema Mapping: {datasetName}</h2>
          <button className="modal-close" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M5 5l10 10M15 5l-10 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        <div className="schema-comparison">
          <div className="schema-panel">
            <div className="schema-panel-header legacy-header">
              <h3>Source: {sourceSchema.table_name}</h3>
              <span className="field-count">{sourceSchema.fields.length} fields</span>
            </div>
            <p className="schema-description">{sourceSchema.description}</p>
            <table className="schema-table">
              <thead>
                <tr>
                  <th>Field</th>
                  <th>Type</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {sourceSchema.fields.map(f => (
                  <tr key={f.name}>
                    <td className="mono field-name">{f.name}</td>
                    <td className="mono type-cell">{f.type}</td>
                    <td>{f.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="schema-arrow">
            <svg width="40" height="40" viewBox="0 0 40 40">
              <line x1="5" y1="20" x2="30" y2="20" stroke="#4fc3f7" strokeWidth="2" />
              <polygon points="28,14 38,20 28,26" fill="#4fc3f7" />
            </svg>
          </div>

          <div className="schema-panel">
            <div className="schema-panel-header unified-header">
              <h3>Target: {targetSchema.table_name}</h3>
              <span className="field-count">{targetSchema.fields.length} fields</span>
            </div>
            <p className="schema-description">{targetSchema.description}</p>
            <table className="schema-table">
              <thead>
                <tr>
                  <th>Field</th>
                  <th>Type</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {targetSchema.fields.map(f => (
                  <tr key={f.name}>
                    <td className="mono field-name">{f.name}</td>
                    <td className="mono type-cell">{f.type}</td>
                    <td>{f.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
