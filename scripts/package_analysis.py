from pathlib import Path
import json,sys
import pandas as pd,nbformat
from nbclient import NotebookClient
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'scripts'))
import newark_analysis as a
out=root/'data/consolidated'
# Expand standard parameter labels without implying all are currently available.
labels={'00010':'Water temperature (deg C)','00045':'Precipitation (inches)','00060':'Discharge (ft3/s)','00065':'Gage height (ft)','00054':'Reservoir storage (acre-ft)','00062':'Elevation of reservoir water surface (ft NGVD29)','62614':'Lake/reservoir elevation (ft NAVD88)','62615':'Lake/reservoir elevation (ft NGVD29)','63160':'Stream water elevation (ft NAVD88)','72019':'Depth to groundwater (ft below land surface)'}
for path in [out/'usgs_station_inventory.csv',*[root/'data'/k/'station_analysis.csv' for k in a.CONFIG]]:
 d=pd.read_csv(path,dtype={'site_no':str}).fillna('');d['variable_labels']='; '.join([]) if len(d)==0 else d.parameter_codes.map(lambda s:'; '.join(f'{c}: {labels.get(c,"USGS parameter; consult linked parameter code dictionary")}' for c in str(s).split(',') if c))
 d.to_csv(path,index=False)
# Metadata and standard exports for three additions.
import geopandas as gpd
for key in ['charlotteburg','clinton','echo_lake']:
 folder=root/'data'/key;b=gpd.read_file(folder/'watershed.geojson').to_crs(a.CRS)
 buf=b.copy();buf.geometry=b.buffer(2000);buf.to_crs(4326).to_file(folder/'search_buffer.geojson',driver='GeoJSON')
 inv=pd.read_csv(folder/'station_analysis.csv',dtype={'site_no':str}).fillna('');g=gpd.GeoDataFrame(inv,geometry=gpd.points_from_xy(inv.longitude,inv.latitude),crs=4326)
 g.to_file(folder/'usgs_sites.geojson',driver='GeoJSON');b.to_file(folder/'watershed.gpkg',layer='watershed',driver='GPKG')
 meta=json.loads((folder/'analysis_validation.json').read_text());meta.update(method='USGS NLDI unsimplified upstream basin; not a fresh DEM delineation',buffer_km=2,source=f'https://api.water.usgs.gov/nldi/linked-data/nwissite/USGS-{a.CONFIG[key][1]}/basin?simplified=false',published_area_source='https://pubs.usgs.gov/wdr/WDR-NJ-02-1/pdf/vol1ver.1.01.pdf',note='Review reservoir outlet snap and area differences before engineering use; transfers are not included')
 (folder/'metadata.json').write_text(json.dumps(meta,indent=2))
 # Self-contained configuration, imports and readable executed outputs; shared pipeline avoids copying implementations.
 nb=nbformat.v4.new_notebook();name,sid,area=a.CONFIG[key]
 nb.cells=[nbformat.v4.new_markdown_cell(f'# {name} Reservoir contributing watershed and USGS stations\n\nUSGS outlet **{sid}**. Uses the same NLDI unsimplified upstream-basin method, UTM 18N metric operations, and 2 km outside buffer as Modules 6 and 7. This is not a new DEM delineation. Reservoir transfers are excluded. Published reference drainage area: {area} mi². Review the reported difference; do not force a match.\n\nRun from a clone (or clone this repository in Colab first) with `pip install -r requirements.txt`. The executed cells below validate and display the saved snapshot without repeating service queries.'),nbformat.v4.new_code_cell("from pathlib import Path\nimport sys,json,pandas as pd,geopandas as gpd\nROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'scripts/newark_analysis.py').exists())\nsys.path.insert(0,str(ROOT/'scripts'))\nimport newark_analysis as analysis\nKEY="+repr(key)+"\nFOLDER=ROOT/'data'/KEY"),nbformat.v4.new_code_cell("# Reuse cached basin and recompute its geometry and area checks.\nkey,basin,validation=analysis.basin(KEY)\nprint(json.dumps(validation,indent=2))\nassert basin.is_valid.all()"),nbformat.v4.new_code_cell("stations=pd.read_csv(FOLDER/'station_analysis.csv',dtype={'site_no':str}).fillna('')\ndisplay(stations[['site_no','station_nm','location_type','variable_labels','operational_flag']])\nprint(stations.location_type.value_counts().to_string())"),nbformat.v4.new_markdown_cell('## Refresh all five reservoirs and consolidate\nUncomment the next cell to query current USGS metadata and seven days of instantaneous values, update the per-watershed station tables and regenerate the consolidated map. This preserves the existing basin files. The pipeline records exact request URLs, UTC times, and raw responses. Re-run the finishing/export steps only when changing the delivered packaging. Observation spacing and latest observation age do not verify transmission frequency or publication latency.'),nbformat.v4.new_code_cell('# analysis.run()'),nbformat.v4.new_code_cell("from IPython.display import display,IFrame\nprint('Consolidated interactive map:',ROOT/'data/consolidated/newark_system_map.html')\ndisplay(IFrame(src='../../data/consolidated/newark_system_map.html',width='100%',height=650))")]
 nb.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}}
 path=root/'notebooks'/key/f'{name.replace(" ","")}_Watershed_USGS.ipynb';path.parent.mkdir(exist_ok=True)
 env={};exec_count=0
 import contextlib,io
 from IPython.display import display as ipdisplay
 for cell in nb.cells:
  if cell.cell_type!='code':continue
  exec_count+=1;cell.execution_count=exec_count;capture=io.StringIO()
  def display_capture(obj):print(obj.to_string(index=False) if isinstance(obj,pd.DataFrame) else repr(obj))
  source=cell.source.replace('from IPython.display import display,IFrame','from IPython.display import IFrame')
  env['display']=display_capture
  with contextlib.redirect_stdout(capture):exec(source,env)
  cell.outputs=[nbformat.v4.new_output('stream',name='stdout',text=capture.getvalue())] if capture.getvalue() else []
 nbformat.write(nb,path)
# Regenerate enriched map and station layer.
inv=pd.read_csv(out/'usgs_station_inventory.csv',dtype={'site_no':str}).fillna('');relations=pd.read_csv(out/'station_watershed_relationships.csv',dtype={'site_no':str});basins={k:gpd.read_file(root/'data'/k/'watershed.geojson').to_crs(a.CRS) for k in a.CONFIG}
sites=gpd.GeoDataFrame(inv.rename(columns={'latitude':'dec_lat_va','longitude':'dec_long_va'}),geometry=gpd.points_from_xy(inv.longitude,inv.latitude),crs=4326).to_crs(a.CRS)
a.make_map(out,basins,sites,inv,relations,[])
gpd.GeoDataFrame(inv,geometry=gpd.points_from_xy(inv.longitude,inv.latitude),crs=4326).to_file(out/'stations.geojson',driver='GeoJSON')
print('Created and executed 3 notebooks; enriched map complete')
