# ERP Migration Accelerator

**AI-accelerated legacy ERP consolidation for Army logistics systems.**

Demonstrates how [Devin](https://devin.ai) can dramatically accelerate the consolidation of two legacy SAP-based ERP systems (GCSS-Army and LMP) into a single unified platform (ALERP).

![Dashboard Screenshot](docs/screenshot.png)

## What This Does

Large government agencies face multi-year, multi-million dollar ERP consolidation efforts. This project shows how AI can compress months of migration development into hours by:

1. **Analyzing** source and target schemas across legacy systems
2. **Generating** data transformation scripts automatically
3. **Testing** migration logic against sample data
4. **Committing** validated scripts to a version-controlled repository

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   GCSS-Army     │     │    ALERP     │     │      LMP        │
│  (Legacy SAP)   │────▶│  (Unified)   │◀────│  (Legacy SAP)   │
│                 │     │              │     │                 │
│ • Equipment     │     │ • Assets     │     │ • Vendors       │
│ • Work Orders   │     │ • Maint Ord  │     │ • Purchase Ord  │
│ • Supply/Matl   │     │ • Supply     │     │ • PO Line Items │
│ • Readiness     │     │ • Vendors    │     │ • Warehouse Inv │
│                 │     │ • Procure    │     │ • Shipments     │
│  4 tables       │     │ • Inventory  │     │                 │
│                 │     │ • Shipments  │     │  5 tables       │
│                 │     │ • Readiness  │     │                 │
│                 │     │  8 tables    │     │                 │
└─────────────────┘     └──────────────┘     └─────────────────┘
        │                      ▲                      │
        └──────────── Devin AI ───────────────────────┘
                    (Migration Scripts)
```

## The Legacy Systems

### GCSS-Army (System Alpha)
Global Combat Support System - Army. Manages tactical logistics:
- SAP-style field naming (EQUNR, AUFNR, MATNR)
- Equipment readiness tracking (FMC/PMC/NMC)
- Maintenance work orders (PM module)
- Unit-level supply management

### LMP (System Bravo)
Logistics Modernization Program. Manages national-level logistics:
- Different SAP configuration and naming conventions
- Procurement and contract management
- Depot/warehouse inventory management
- Shipment and transportation tracking

### ALERP (Unified Target)
Army Logistics Enterprise Resource Planning. The consolidated system:
- Modern, readable field naming
- UUID-based primary keys
- Standardized enumerations
- Built-in audit trails
- Normalized reference data

## Migration Dashboard

The dashboard provides:
- **System overview** showing legacy → unified data flow
- **Dataset browser** with 8 migration datasets across all domain areas
- **Schema viewer** comparing source and target field mappings
- **One-click migration** launching Devin sessions per dataset
- **Live status tracking** with links to active Devin sessions
- **Progress metrics** showing overall migration completion

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- A [Devin API key](https://app.devin.ai) (optional for demo mode)

### Setup

```bash
# Clone
git clone https://github.com/heintztyler/erp-migration-accelerator.git
cd erp-migration-accelerator

# Backend
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### Configure (Optional)

```bash
cp .env.example .env
# Edit .env with your Devin API key and repo URL
```

### Run

```bash
# Terminal 1: Backend
cd backend
PYTHONPATH=. .venv/bin/uvicorn app.main:app --port 8000

# Terminal 2: Frontend (dev mode)
cd frontend
npm run dev
```

Open **http://localhost:3000**.

### Production Build

```bash
cd frontend && npm run build
# Frontend is served from backend at http://localhost:8000
cd ../backend
PYTHONPATH=. .venv/bin/uvicorn app.main:app --port 8000
```

## How the Devin Integration Works

When you click "Start Migration" on a dataset:

1. The dashboard sends the source schema, target schema, and sample data to the backend
2. The backend constructs a detailed migration prompt and creates a Devin session
3. Devin analyzes both schemas and generates:
   - A Python migration script (`migrations/<dataset>_migration.py`)
   - A test file (`migrations/test_<dataset>_migration.py`)
   - Documentation of the mapping logic
4. Devin tests the script against sample data
5. Devin commits the validated script to this repository
6. The dashboard shows real-time progress and links to the Devin session

Without a Devin API key, the app runs in demo/mock mode — all UI features work, but no real sessions are created.

## Project Structure

```
erp-migration-accelerator/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application
│   │   ├── models.py                # Pydantic models
│   │   ├── state.py                 # In-memory migration state
│   │   ├── devin_client.py          # Devin API client + prompt builder
│   │   ├── routers/
│   │   │   ├── datasets.py          # Dataset & schema endpoints
│   │   │   └── migrations.py        # Migration session endpoints
│   │   ├── legacy_systems/
│   │   │   ├── system_alpha.py      # GCSS-Army schemas + sample data
│   │   │   └── system_bravo.py      # LMP schemas + sample data
│   │   └── unified_system/
│   │       └── target_schema.py     # ALERP target schemas + dataset defs
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx                  # Main dashboard
│   │   ├── components/              # React components
│   │   ├── api/client.ts            # API client
│   │   └── types/index.ts           # TypeScript types
│   └── package.json
├── migrations/                      # Devin-generated migration scripts
└── README.md
```

## Demo Script

For presenting to senior stakeholders:

1. **Open the dashboard** — show the system overview (two legacy systems → one unified)
2. **Browse a dataset** — click "View Schemas" on Equipment & Asset Records to show the SAP-to-modern field mapping
3. **Start a migration** — click "Start Migration" to launch a Devin session live
4. **Watch Devin work** — click "Watch Devin Work" to show the AI analyzing schemas, writing code, and testing
5. **Review the output** — show the generated migration script in the GitHub repo
6. **Repeat** — kick off multiple migrations in parallel to show scale

Key talking points:
- Traditional approach: 6-12 months per dataset with specialized SAP consultants
- AI-accelerated approach: hours per dataset with automated testing
- All code is version-controlled, auditable, and human-reviewable
- Devin handles the repetitive mapping work; humans review and approve
