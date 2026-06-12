import { useState, useEffect, useCallback } from 'react';
import type { Dataset, SchemaInfo, CreateDatasetPayload } from './types';
import { fetchDatasets, fetchSourceSchema, fetchTargetSchema, startMigration, resetMigration, createDataset } from './api/client';
import { Header } from './components/Header';
import { SystemOverview } from './components/SystemOverview';
import { StatsBar } from './components/StatsBar';
import { KanbanBoard } from './components/KanbanBoard';
import { BacklogPanel } from './components/BacklogPanel';
import { SchemaModal } from './components/SchemaModal';
import { CreateDatasetModal } from './components/CreateDatasetModal';
import './styles.css';

export default function App() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
  const [sourceSchema, setSourceSchema] = useState<SchemaInfo | null>(null);
  const [targetSchema, setTargetSchema] = useState<SchemaInfo | null>(null);
  const [schemaModalOpen, setSchemaModalOpen] = useState(false);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [migrating, setMigrating] = useState<Set<string>>(new Set());

  const loadDatasets = useCallback(async () => {
    try {
      const data = await fetchDatasets();
      setDatasets(data);
    } catch (err) {
      console.error('Failed to fetch datasets:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDatasets();
    const interval = setInterval(loadDatasets, 3000);
    return () => clearInterval(interval);
  }, [loadDatasets]);

  const handleViewSchema = async (datasetId: string) => {
    setSelectedDataset(datasetId);
    try {
      const [src, tgt] = await Promise.all([
        fetchSourceSchema(datasetId),
        fetchTargetSchema(datasetId),
      ]);
      setSourceSchema(src);
      setTargetSchema(tgt);
      setSchemaModalOpen(true);
    } catch (err) {
      console.error('Failed to load schemas:', err);
    }
  };

  const handleStartMigration = async (datasetId: string) => {
    setMigrating(prev => new Set(prev).add(datasetId));
    try {
      await startMigration(datasetId);
      await loadDatasets();
    } catch (err) {
      console.error('Failed to start migration:', err);
    } finally {
      setMigrating(prev => {
        const next = new Set(prev);
        next.delete(datasetId);
        return next;
      });
    }
  };

  const handleReset = async (datasetId: string) => {
    try {
      await resetMigration(datasetId);
      await loadDatasets();
    } catch (err) {
      console.error('Failed to reset migration:', err);
    }
  };

  const handleCreate = async (payload: CreateDatasetPayload) => {
    try {
      await createDataset(payload);
      await loadDatasets();
      setCreateModalOpen(false);
    } catch (err) {
      console.error('Failed to create dataset:', err);
    }
  };

  const backlogDatasets = datasets.filter(d => d.stage === 'BACKLOG');
  const activeDatasets = datasets.filter(d => d.stage !== 'BACKLOG');

  if (loading) {
    return (
      <div className="app">
        <Header />
        <div className="loading">Loading migration datasets...</div>
      </div>
    );
  }

  return (
    <div className="app">
      <Header />
      <main className="main-kanban">
        <SystemOverview />
        <StatsBar datasets={datasets} />
        <section className="kanban-section">
          <div className="kanban-layout">
            <BacklogPanel
              datasets={backlogDatasets}
              onStartMigration={handleStartMigration}
              onViewSchema={handleViewSchema}
              onCreateNew={() => setCreateModalOpen(true)}
              migratingIds={migrating}
            />
            <KanbanBoard
              datasets={activeDatasets}
              onViewSchema={handleViewSchema}
              onStartMigration={handleStartMigration}
              onReset={handleReset}
              migratingIds={migrating}
            />
          </div>
        </section>
      </main>

      {schemaModalOpen && sourceSchema && targetSchema && (
        <SchemaModal
          datasetId={selectedDataset!}
          datasetName={datasets.find(d => d.id === selectedDataset)?.name ?? ''}
          sourceSchema={sourceSchema}
          targetSchema={targetSchema}
          onClose={() => setSchemaModalOpen(false)}
        />
      )}

      {createModalOpen && (
        <CreateDatasetModal
          onClose={() => setCreateModalOpen(false)}
          onCreate={handleCreate}
        />
      )}
    </div>
  );
}
