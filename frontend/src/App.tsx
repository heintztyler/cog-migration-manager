import { useState, useEffect, useCallback } from 'react';
import type { Dataset, SchemaInfo } from './types';
import { fetchDatasets, fetchSourceSchema, fetchTargetSchema, startMigration, resetMigration } from './api/client';
import { Header } from './components/Header';
import { SystemOverview } from './components/SystemOverview';
import { DatasetCard } from './components/DatasetCard';
import { SchemaModal } from './components/SchemaModal';
import { StatsBar } from './components/StatsBar';
import './styles.css';

export default function App() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
  const [sourceSchema, setSourceSchema] = useState<SchemaInfo | null>(null);
  const [targetSchema, setTargetSchema] = useState<SchemaInfo | null>(null);
  const [schemaModalOpen, setSchemaModalOpen] = useState(false);
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
    const interval = setInterval(loadDatasets, 5000);
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
      <main className="main">
        <SystemOverview />
        <StatsBar datasets={datasets} />
        <section className="datasets-section">
          <h2 className="section-title">Migration Datasets</h2>
          <p className="section-desc">
            Each dataset represents a logical grouping of records to be migrated from legacy systems
            to the unified ALERP platform. Click "Start Migration" to launch a Devin session that
            will analyze the schemas, generate transformation scripts, and test the migration.
          </p>
          <div className="datasets-grid">
            {datasets.map(ds => (
              <DatasetCard
                key={ds.id}
                dataset={ds}
                onViewSchema={() => handleViewSchema(ds.id)}
                onStartMigration={() => handleStartMigration(ds.id)}
                onReset={() => handleReset(ds.id)}
                isMigrating={migrating.has(ds.id)}
              />
            ))}
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
    </div>
  );
}
