# Newark system: station availability and GARR timing assessment

Snapshot queried October 26, 2026. Exact UTC retrieval time and request URLs: `provenance.json`. GARR is interpreted here as gauge-adjusted radar rainfall; confirm the operational update interval and acceptable observation age with the project team. No universal acceptance threshold is assumed. The 60-minute flags are screening flags, not a supplied project requirement.

## Findings

- 49 unique USGS locations meet the five-basin/2 km proximity scope. Historical, groundwater, reservoir and discontinued locations are deliberately included; presence is not evidence of live rainfall availability.
- Three precipitation locations returned valid data during the seven-day IV query: **410639074293001**, **410230074300001**, and **410148074252901**. All had modal observation spacing of **15 minutes**. At the IV retrieval, their latest valid observations were approximately **67.8 minutes old**. They are candidates for rainfall evaluation, not demonstrated low-latency operational feeds.
- No valid recent series in this snapshot had an hourly-or-coarser modal observation interval. This does **not** show that every station transmits more frequently than hourly.
- Streamflow sites 01382210 and 01382385 returned 15-minute discharge/stage series with latest observations approximately 37.8 minutes old. Site 01382500 returned 5-minute series approximately 12.8 minutes old. These support hydrological monitoring/validation; they do not directly replace rain gauges for radar rainfall adjustment. Consult the relationship table for inside versus nearby classification.
- Reservoir reference locations and historical series must not be assumed to provide near-real-time stage, storage or precipitation. All variable-specific catalog periods are retained in `usgs_series_catalog.csv` and summarized in the inventory. Empty IV series and missing variables are not silently treated as zero rainfall.

## Timing evidence and limitations

USGS general guidance says measurements are typically recorded at 15-minute intervals and often transmitted hourly, with possible more frequent reporting during critical events. This is general guidance, **not verification of the telemetry configuration at any listed station**:
https://www.usgs.gov/faqs/how-often-are-real-time-streamflow-data-updated

`station_timing_by_variable.csv` calculates spacing from valid observation timestamps over seven days. Modal spacing may conceal outages; maximum gaps are also included. Latest observation age is retrieval UTC minus latest observation UTC. It combines effects of collection schedule, transmission, processing, availability and possible outages. The IV response does not expose first-publication times, so neither actual transmission cadence nor publication latency can be derived from this snapshot. Historical series begin/end dates do not establish uninterrupted coverage, and an IV series with no valid observations does not establish permanent retirement.

For production GARR, obtain station-specific telemetry schedules from USGS/operator, and poll at the intended operational interval over multiple days and storms. Save poll time and first-seen observation time to bound publication delay and identify batch arrivals. Evaluate completeness, outages, clock/timezone consistency, accumulated-precipitation/reset conventions, QC flags and radar-grid/time-step alignment. A roughly 68-minute-old rain observation would not meet a requirement for observations less than 60 minutes old at this snapshot; suitability for a different tolerance remains conditional. No measured latency SLA is claimed.

## Basin verification

| Reservoir | NLDI area, km² | Published area, mi² | Difference |
|---|---:|---:|---:|
| Canistear | 15.046 | 6.08 | -4.45% |
| Oak Ridge | 69.735 | 27.3 | -1.37% |
| Charlotteburg | 147.445 | 56.2 | +1.30% |
| Clinton | 28.823 | 10.5 | +5.99% |
| Echo Lake | 11.490 | 4.35 | +1.98% |

Existing Canistear/Oak Ridge polygon files were preserved unchanged and checked for valid geometry and recomputed area. Three additional polygons were retrieved from NLDI using reservoir-reference USGS IDs 01382380, 01382300 and 01382400. These are NHDPlus-based upstream basins, not newly computed DEM watersheds or surveyed boundaries. All geometries are valid. Clinton's approximately 6% difference requires outlet snapping/catchment review before engineering use; geometric validity alone does not validate the hydrological boundary. Echo Lake's published area is 4.35 mi² (some extracted PDF tables may concatenate a footnote with this number).

Independent published drainage areas and reservoir-operation descriptions:
https://pubs.usgs.gov/wdr/WDR-NJ-02-1/pdf/vol1ver.1.01.pdf

The system contains nested upstream basins: do not sum all five areas or count duplicate gauges as independent sites. Reservoir releases, diversions and Echo Lake transfers can differ from natural surface drainage. A station within a 2 km buffer has proximity relevance only; flow connectivity and rainfall representativeness remain unverified.

## Deliverables and definitions

- `usgs_station_inventory.csv`: one row per USGS location, coordinates, parameter codes/labels, series periods, recent timing flags and source links.
- `usgs_series_catalog.csv`: one row per returned USGS data series, including data type, parameter, begin/end and count metadata. USGS parameter dictionary: https://help.waterdata.usgs.gov/parameter_cd
- `station_timing_by_variable.csv`: recent IV timing evidence by site and variable, including no-valid-observation series.
- `station_watershed_relationships.csv`: one row per qualifying reservoir/site relationship; `inside` includes boundary points, `nearby_outside` means outside and within 2 km. A site can be inside one basin and nearby another.
- `watersheds.geojson`, `stations.geojson`, `newark_system_map.html`: consolidated geometry and interactive map. Reservoir icons mark reference stations, not water-surface polygons. Map pop-ups expose data periods, variables, relationship and timing limitations.
- `sources/`: original NWIS catalog and IV responses, plus the site search. Newly retrieved NLDI responses reside in each reservoir's `sources/` folder. Original Canistear/Oak Ridge source files remain intact.

Recent USGS values are provisional and subject to revision. This is a reproducible screening analysis; no station-specific hourly telemetry configuration or production GARR readiness has been established.
