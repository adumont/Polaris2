# Polaris2

Celestial navigation scenario generator and sight reduction simulator. Generate random Atlantic Ocean scenarios with real/DR positions, compute sextant readings, perform sight reductions, and solve least-squares fixes.

App is published at https://polaris2.streamlit.app.

## Quickstart

```bash
# Install
uv sync

# CLI: generate a scenario
uv run polaris2 --seed 42

# WebUI
uv run polaris2-web
```

## Usage

```
uv run polaris2 [--error NMI] [--he FEET] [--seed N] [--output FILE]
uv run polaris2-web                       # Streamlit WebUI
uv run polaris2-tui                       # Textual TUI (placeholder)
```

- `--error` — DR error in nautical miles (default: 5)
- `--he` — height of eye in feet (default: 10)
- `--seed` — random seed for reproducibility
- `--output` — save scenario to YAML file

## Architecture

```
celnav-core/          ← shared sibling package (celnav-core on PyPI)
  config, models, ephemeris, almanac, sight, reduction, cartography, angles

src/polaris2/
├── utils/io.py       YAML persistence
├── core/scenario.py  Scenario generation
├── cli/app.py        CLI entry point
├── tui/app.py        Textual TUI
└── webui/app.py      Streamlit + folium map
```

Core nav logic (Skyfield queries, sight reduction, fix solving, charts) is in the **celnav-core** package — shared with navpac-simulator.

## How it works

1. Generates a random position in the Atlantic (10-50°N, 10-80°W) and a daytime UTC datetime
2. Picks a DR position at a random bearing at \\`--error\\` nmi from real
3. Identifies visible bodies (Sun, Moon, stars above 10° altitude)
4. Selects best bodies (30-60° altitude range preferred)
5. Computes apparent altitude at real position → Ho  *(celnav-core)*
6. Computes apparent altitude at DR position → Hc, Zn *(celnav-core)*
7. Intercept I = (Ho − Hc) × 60 (nmi). Positive I = toward the body (in Zn direction)
8. Iterative least-squares fix: A·x = I, where A = [cos Zn, sin Zn] *(celnav-core)*
9. Fix error computed via haversine formula

## Testing

```bash
uv run pytest tests/ -v          # run tests
uv run pytest --cov=src/polaris2  # with coverage
uv run ruff check                 # lint
uv run ruff format                # format
```

## Dependencies

- **celnav-core** (shared: Skyfield, Pydantic, NumPy, Matplotlib)
- Streamlit + folium (WebUI), Textual (TUI placeholder)
