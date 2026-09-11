# Interactive Data Dashboard — Real-Time Charts, Filters & Export

A full-stack interactive dashboard built with FastAPI, Chart.js, and WebSocket for real-time data visualization.

## Features

- **Real-time Charts** — Bar, line, area charts powered by Chart.js with live WebSocket updates (5s interval)
- **Interactive Filters** — Time range, agent, vertical, and date range filters
- **Data Export** — CSV, JSON, PNG (chart image) export with active filters applied
- **KPI Summary Cards** — Live KPI metrics with change indicators
- **Responsive Design** — Dark theme, mobile/tablet/desktop layouts
- **Live Connection Status** — WebSocket connection indicator with auto-reconnect
- **Data Table** — Recent metrics table with sortable columns

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Interactive Data Dashboard                    │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  Frontend (Chart.js + Vanilla JS)                      │   │
│  │  - KPI cards, filter panel, chart grid, data table     │   │
│  │  - WebSocket client for real-time updates              │   │
│  │  - CSV/JSON/PNG export buttons                         │   │
│  └───────────────────────────────────────────────────────┘   │
│                            │                                   │
│                            ▼                                   │
│  ┌───────────────────────────────────────────────────────┐   │
│  │  Backend (FastAPI)                                     │   │
│  │  - REST API: /api/v1/dashboard/*                      │   │
│  │  - WebSocket: /ws/dashboard                           │   │
│  │  - Export: CSV, JSON with filter passthrough          │   │
│  │  - Health: /health                                     │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Install dependencies
pip install fastapi uvicorn python-multipart

# Run the server (serves dashboard at http://localhost:8000)
uvicorn dashboard.api:app --reload

# Run tests (14 tests)
python -m pytest tests/ -v --rootdir=.
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Interactive dashboard (HTML) |
| GET | `/dashboard` | Interactive dashboard (HTML) |
| GET | `/api/v1/dashboard/metrics` | Metrics data with filters |
| GET | `/api/v1/dashboard/timeseries` | Time series for charts |
| GET | `/api/v1/dashboard/kpis` | KPI summary cards |
| GET | `/api/v1/dashboard/export/csv` | Export filtered data as CSV |
| GET | `/api/v1/dashboard/export/json` | Export filtered data as JSON |
| WS | `/ws/dashboard` | Real-time metrics stream |
| GET | `/health` | Health check |

## Query Parameters

**`/api/v1/dashboard/metrics`**:
- `from_time` — ISO datetime (default: 24h ago)
- `to_time` — ISO datetime (default: now)
- `agent` — Filter by agent ID
- `vertical` — Filter by vertical (healthcare, legal, finance, etc.)
- `granularity` — Data interval: `1m` or `5m` (default: `1m`)

**`/api/v1/dashboard/timeseries`**:
- `hours` — Hours of data (1-168, default: 24)
- `vertical` — Filter by vertical

**Export endpoints** inherit the same filter parameters as `/metrics`.

## File Structure

```
t_2be3d0d3/
├── dashboard/
│   └── api.py          # FastAPI backend + HTML/JS frontend
├── tests/
│   ├── conftest.py     # Pytest sys.path fix
│   └── test_dashboard.py  # 14 tests
├── .github/
│   └── workflows/      # CI/CD config
└── README.md
```

## Tech Stack

- **Backend**: FastAPI (async), Python 3.11+
- **Frontend**: Chart.js 4.4, vanilla JS (no build step)
- **Real-time**: WebSocket with auto-reconnect
- **Testing**: pytest + httpx (FastAPI TestClient)

## License

MIT
