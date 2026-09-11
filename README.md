# Interactive Data Dashboard

Real-time data visualization dashboard with charts, filters, and export capabilities.
Built with React, TypeScript, and Recharts for displaying AI system metrics and analytics.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Components](#components)
- [Data Sources](#data-sources)
- [API Reference](#api-reference)
- [Setup](#setup)

## Overview

A responsive, real-time dashboard for monitoring AI system performance, knowledge graph
metrics, and business KPIs. Supports interactive filtering, drill-down, and data export.

## Features

- **Real-time Charts** — Line, bar, area, pie, and scatter charts with live updates
- **Interactive Filters** — Date range, category, agent, vertical, and status filters
- **Data Export** — CSV, JSON, PNG, and PDF export
- **Responsive Design** — Desktop, tablet, and mobile layouts
- **Dark Mode** — Full dark mode support
- **Drill-down** — Click any data point to see details
- **Custom Dashboards** — Save and share custom dashboard layouts

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Interactive Data Dashboard                         │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Dashboard Container                                         │    │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │    │
│  │  │  Chart      │  │  Filter      │  │  KPI             │   │    │
│  │  │  Panel      │  │  Panel       │  │  Cards           │   │    │
│  │  └─────────────┘  └──────────────┘  └──────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│  ┌───────────────────────────▼─────────────────────────────────┐    │
│  │  Data Layer                                                  │    │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │    │
│  │  │  WebSocket  │  │  REST API    │  │  Local           │   │    │
│  │  │  Client     │  │  Client      │  │  Storage         │   │    │
│  │  └─────────────┘  └──────────────┘  └──────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## Components

### ChartPanel

```tsx
interface ChartPanelProps {
  title: string;
  type: 'line' | 'bar' | 'area' | 'pie' | 'scatter';
  data: DataPoint[];
  xKey: string;
  yKey: string;
  colors?: string[];
  showLegend?: boolean;
  showGrid?: boolean;
  animate?: boolean;
  onDataPointClick?: (point: DataPoint) => void;
}
```

### FilterPanel

```tsx
interface FilterPanelProps {
  filters: FilterConfig[];
  onChange: (filters: Record<string, FilterValue>) => void;
  onReset: () => void;
}

interface FilterConfig {
  key: string;
  label: string;
  type: 'date-range' | 'select' | 'multi-select' | 'search' | 'toggle';
  options?: { label: string; value: string }[];
  defaultValue?: FilterValue;
}
```

### KPICard

```tsx
interface KPICardProps {
  title: string;
  value: number | string;
  change?: number;
  changeLabel?: string;
  icon?: React.ReactNode;
  color?: string;
}
```

### ExportButton

```tsx
interface ExportButtonProps {
  data: DataPoint[];
  filename: string;
  formats: ('csv' | 'json' | 'png' | 'pdf')[];
  onExport?: (format: string) => void;
}
```

## Data Sources

| Source | Type | Endpoint | Refresh |
|--------|------|----------|---------|
| Agent Metrics | WebSocket | /ws/agents | Real-time |
| Task Results | REST | /api/v1/tasks | 30s |
| Safety Events | REST | /api/v1/safety | 60s |
| Resource Usage | WebSocket | /ws/resources | 5s |
| KG Statistics | REST | /api/v1/graph/stats | 300s |

## API Reference

### GET /api/v1/dashboard/metrics

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| from | ISO date | 24h ago | Start date |
| to | ISO date | now | End date |
| agent | string | all | Filter by agent |
| vertical | string | all | Filter by vertical |
| granularity | string | 1m | Data granularity |

**Response:**
```json
{
  "metrics": [
    { "timestamp": "2024-01-15T10:00:00Z", "tasks_completed": 42, "avg_latency_ms": 150 },
    { "timestamp": "2024-01-15T10:01:00Z", "tasks_completed": 45, "avg_latency_ms": 145 }
  ],
  "total": 1440,
  "granularity": "1m"
}
```

## Setup

```bash
npm install
npm run dev
# Open http://localhost:3000/dashboard
```

## License

MIT
