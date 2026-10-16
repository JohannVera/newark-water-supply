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
