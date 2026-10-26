# Newark water supply

Reservoir contributing watersheds and USGS station inventories for Newark, New Jersey.

## Notebooks

| Module | Watershed | Open in Colab |
|---|---|---|
| 6 | Canistear Reservoir | [Module 6](https://colab.research.google.com/github/JohannVera/newark-water-supply/blob/main/notebooks/Module6_CanistearWatershed_USGS.ipynb) |
| 7 | Oak Ridge Reservoir | [Module 7](https://colab.research.google.com/github/JohannVera/newark-water-supply/blob/main/notebooks/Module7_OakRidgeWatershed_USGS.ipynb) |

Module numbers retain continuity with the original Crabtree teaching sequence. The Newark project now lives independently here.

## Organization

- `notebooks/`: editable workflows
- `data/canistear/`: Canistear GIS layers, QGIS project, maps, station catalog and raw source responses
- `data/oak_ridge/`: Oak Ridge GIS layers, interactive map, station catalog and raw source responses

GIS project files remain beside their GeoPackages so relative paths continue to work.

## Run

In Colab, uncomment the pip-install cell and execute cells in order, skipping the optional QGIS section. Outputs go to `data/canistear` or `data/oak_ridge` beneath the working directory. Colab storage is temporary, so download outputs before ending the runtime.

For local use, clone the repository, install `requirements.txt`, and open either notebook. The notebook finds the project root when launched from inside the clone. Open the saved HTML maps in a browser with internet access for Leaflet and Esri tiles.

For QGIS, open the Canistear project in `data/canistear`, or load either GeoPackage directly. The Oak Ridge notebook includes an optional QGIS project/PNG export that has not been run in the delivered environment.

## Validated inventory snapshots

| Watershed | NLDI basin area | Basin sites | Buffer-only sites | Outward buffer |
|---|---:|---:|---:|---:|
| Canistear | 15.05 km² | 3 | 2 | 2 km |
| Oak Ridge | 69.73 km² | 7 | 10 | 2 km |

These are USGS NLDI upstream basins, not new DEM delineations or reservoir water-surface polygons. They differ from USGS published drainage areas by approximately -4.5% and -1.37%, respectively. Review before engineering use. Reservoir diversions and operations can differ from surface drainage.

Station inclusion does not establish continuous data availability, current operation, or hydrologic connectivity of buffer-only sites. Counts may change on rerun. Exact retrieval URLs/times and raw responses are retained with each dataset.

## Origin

Moved from [JohannVera/crabtree-flood-forecasting](https://github.com/JohannVera/crabtree-flood-forecasting) on October 16, 2026. The original history remains in that repository. Module 5 there remains a methodological reference.

## Five-reservoir consolidated analysis — October 26, 2026

The Newark system analysis now includes Charlotteburg, Clinton and Echo Lake alongside the existing Canistear and Oak Ridge basins. Existing basin files were preserved. The additions follow the same USGS NLDI upstream-basin and 2 km buffer workflow, using EPSG:32618 for metric operations and WGS84 GeoJSON for exchange.

| Reservoir | New notebook | Output folder |
|---|---|---|
| Charlotteburg | [Executed notebook](notebooks/charlotteburg/Charlotteburg_Watershed_USGS.ipynb) | [Data](data/charlotteburg/) |
| Clinton | [Executed notebook](notebooks/clinton/Clinton_Watershed_USGS.ipynb) | [Data](data/clinton/) |
| Echo Lake | [Executed notebook](notebooks/echo_lake/EchoLake_Watershed_USGS.ipynb) | [Data](data/echo_lake/) |

- [Consolidated interactive map](data/consolidated/newark_system_map.html): download the HTML and open it in a browser; GitHub's file viewer does not execute HTML. Internet is required for map libraries and tiles.
- [Station inventory](data/consolidated/usgs_station_inventory.csv), [variable-specific availability](data/consolidated/usgs_series_catalog.csv), [timing evidence](data/consolidated/station_timing_by_variable.csv) and [inside/nearby relationships](data/consolidated/station_watershed_relationships.csv).
- [GARR findings, basin checks, sources and limitations](data/consolidated/GARR_assessment.md).

The scope contains 49 unique USGS locations. Three rain gauges returned recent 15-minute observations, but their newest values were approximately 68 minutes old at retrieval. Observation spacing is not transmission frequency, and latest observation age is not measured publication latency. Station-specific telemetry remains unverified. Clinton's basin area differs by approximately +6% from the published reference and requires outlet/catchment review. Basins overlap; their areas must not be summed. Operational transfers are not represented by natural drainage polygons.

### Reproduce or refresh

From the repository root:

```bash
python -m pip install -r requirements.txt
python scripts/newark_analysis.py
python scripts/package_analysis.py
```

The first script reuses saved boundaries, discovers sites, fetches the complete available series catalog and seven days of IV data, then generates the consolidated outputs. The second exports enriched station labels, three reservoir GeoPackages/GeoJSONs, and notebooks with executed snapshot validation/display outputs. New notebook folders mirror the reservoir output folders. The saved map iframe is for notebook-server use; download/open the HTML directly when viewing from GitHub or Colab. Snapshot narrative findings in `GARR_assessment.md` and this README are dated and should be reviewed after a refresh. Exact URLs, raw responses and retrieval times are saved alongside outputs.
