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
src/polaris2/
├── config.py        Constants
├── models.py        Pydantic models
├── utils/
│   ├── angles.py    DD.MMSS <-> float conversions
│   └── io.py        YAML persistence
├── core/
│   ├── scenario.py  Position/datetime generation
│   ├── almanac.py   Skyfield ephemeris queries
│   ├── sight.py     Sextant reading computation
│   └── reduction.py Sight reduction + LSQ fix solver
├── cli/app.py       CLI entry point
├── tui/app.py       Textual TUI placeholder
└── webui/app.py     Streamlit + folium map
```

## How it works

1. Generates a random position in the Atlantic (10-50°N, 10-80°W) and a daytime UTC datetime
2. Picks a DR position at a random bearing at `--error` nmi from real
3. Identifies visible bodies (Sun, Moon, stars above 10° altitude)
4. Selects best bodies (30-60° altitude range preferred)
5. Computes apparent altitude at real position → Ho
6. Computes apparent altitude at DR position → Hc, Zn
7. Intercept α = (Hc − Ho) × 60 (nmi)
8. Iterative least-squares fix: A·x = −α, where A = [cos Zn, sin Zn]
9. Fix error computed via haversine formula

## Testing

```bash
uv run pytest tests/ -v          # run tests
uv run pytest --cov=src/polaris2  # with coverage
uv run ruff check                 # lint
uv run ruff format                # format
```

## Dependencies

- Skyfield (ephemeris), Pydantic (models), NumPy/SciPy (solver)
- Streamlit + folium (WebUI), Textual (TUI placeholder)
