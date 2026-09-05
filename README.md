# Vertical AI Deployment Dashboard

Single-page dashboard showing the status of all 7 vertical AI knowledge graph projects.

## Quick Start

```bash
# Serve with any static file server
cd dashboard
python -m http.server 8080

# Or deploy via the existing CI/CD pipeline
# Push to itsPremkumar/aetheria-dashboard main branch
```

## Projects

| # | Project | Status | Repo |
|---|---------|--------|------|
| 1 | Healthcare Medical KG | ✅ Verified | aetheria-healthcare |
| 2 | Legal Contract Analysis KG | ✅ Verified | aetheria-legal |
| 3 | Education Learning Assistant KG | ⏳ Pending | aetheria-education |
| 4 | Finance Reasoning KG | ⏳ Pending | aetheria-finance |
| 5 | Agriculture Crop & Soil KG | ⏳ Pending | aetheria-agriculture |
| 6 | Manufacturing Supply Chain KG | 🔨 Building | aetheria-manufacturing |
| 7 | Customer Service Knowledge Base KG | 🔨 Building | aetheria-customer-service |

## CI/CD Integration

This dashboard is deployed via the aetheria-ci-cd pipeline:
- Push to main → triggers GitHub Actions
- Tests run → build → deploy to GitHub Pages

## Tech Stack

- Pure HTML/CSS/JS (no build step)
- Responsive design
- GitHub API integration ready
- Deployable via GitHub Pages
