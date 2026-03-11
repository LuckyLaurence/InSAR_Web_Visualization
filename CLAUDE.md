# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an InSAR (Interferometric Synthetic Aperture Radar) web visualization platform built with Streamlit. It visualizes ground subsidence monitoring data from satellite imagery, with interactive 3D maps, road network overlay analysis, risk grading, and AI-generated reports.

**Tech Stack**: Streamlit, PyDeck (3D maps), GeoPandas, Shapely, OpenStreetMap API, DeepSeek API

## Development Commands

```bash
# Run the application
streamlit run src/app.py

# Run with specific port
streamlit run src/app.py --server.port 8501

# Install dependencies
pip install -r requirements.txt

# Test AI report generation
python src/utils/ai_report.py

# Test spatial analysis
python src/utils/spatial_analysis.py
```

## Project Architecture

### Entry Point and Flow
- **`src/app.py`**: Main Streamlit application. Single-file architecture for simplicity.
- Data flows: Load → Filter → Analyze → Visualize → AI Report

### Configuration System
- **`config/config.py`**: Central configuration for paths, thresholds, colors, API settings
- All hardcoded values should migrate here for consistency
- `PROCESSED_DATA_DIR`: Default InSAR data location (shapefiles)
- `EXTERNAL_DATA_DIR`: Road network data (OSM-derived)
- `VELOCITY_THRESHOLDS`: Risk classification thresholds (mm/year)

### Utility Modules (src/utils/)
| Module | Purpose |
|--------|---------|
| `spatial_analysis.py` | Spatial join between InSAR points and road networks, risk calculation |
| `ai_report.py` | DeepSeek API integration for generating analysis reports |
| `data_import.py` | Multi-format file upload (CSV, GeoJSON, Excel, Shapefile ZIP) |
| `gis_tools.py` | HDF5 to Shapefile conversion (from MintPy outputs) |
| `osm_tools.py` | OpenStreetMap data fetching |

### Data Format Requirements

**InSAR data must have**:
- `longitude`, `latitude`: WGS84 coordinates (EPSG:4326)
- `velocity`: subsidence rate in **mm/year** (negative = subsidence, positive = uplift)
- Optional: `velocity_mean`, `velocity_std`, `velocity_min`, `velocity_max`, `point_count`

**Road network data** (GeoDataFrame):
- `geometry`: LineString for roads
- `name`: Road identifier
- `highway`: Road type (from OSM)

### Risk Classification System
```python
# Thresholds in mm/year
severe: < -200      # High risk
high: -200 to -50   # Medium risk
moderate: -50 to -10 # Low risk
stable: > -10       # Stable
```

## Key Implementation Patterns

### Map Rendering with PyDeck
- Uses `ScatterplotLayer` for InSAR points, `PathLayer` for roads, `TextLayer` for labels
- Dynamic view state calculation based on data extent (`calculate_view_state()`)
- Color mapping function for velocity-based visualization

### Session State Management
```python
# Key session state variables
st.session_state.uploaded_gdf      # User-uploaded data
st.session_state.view_state        # Map camera position
```

### Data Loading Pattern
```python
@st.cache_data  # Always cache expensive data loads
def load_insar_data(file_path):
    return gpd.read_file(file_path)
```

### Spatial Join Performance Note
The `spatial_join_points_to_roads()` function can be slow with large datasets. It buffers roads by 0.002 degrees (~200m) before joining with InSAR points.

## Adding New Features

### To add a new data source type:
1. Add loader function to `src/utils/data_import.py` (see `load_csv_file`, `load_geojson_file` as templates)
2. Add file extension to `st.sidebar.file_uploader()` type list in `app.py`
3. Update validation in `validate_insar_data()`

### To modify risk thresholds:
Edit `config/config.py` → `VELOCITY_THRESHOLDS`. No code changes needed.

### To change map styling:
Modify PyDeck layer styles in `app.py` around line 340 (color function) and layer definitions.

## External Dependencies

- **Month2 Project**: Located at `F:/InSAR_WorkSpace/02_Projects/Project_Beijing` - contains MintPy HDF5 outputs
- **DeepSeek API**: Optional. Falls back to mock report if API key not provided
- **OpenStreetMap**: Road network data source

## Testing Data

- Default data: `data/processed/beijing_velocity_aggregated.shp` (~65K points)
- Mock roads: `data/external/beijing_mock_roads.shp`
- Export script: `scripts/export_to_csv.py` for data portability
