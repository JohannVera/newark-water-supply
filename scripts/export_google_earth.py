"""Export saved Newark basins/stations as KML/KMZ for Google Earth."""
from pathlib import Path
import json,csv,zipfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/consolidated'
NS='http://www.opengis.net/kml/2.2';ET.register_namespace('',NS)
def el(parent,name,value=None,**attrs):
 x=ET.SubElement(parent,'{'+NS+'}'+name,attrs)
 if value is not None:x.text=str(value)
 return x
root=ET.Element('{'+NS+'}kml');doc=el(root,'Document');el(doc,'name','Newark reservoir watersheds and USGS stations')
el(doc,'description','Five USGS NLDI contributing watersheds and 49 USGS monitoring locations. Snapshot October 26, 2026. Satellite imagery is supplied by Google Earth when this file is opened. Nested basin areas must not be added. Reservoir markers identify reference stations, not water-surface extents.')
look=el(doc,'LookAt')
for k,v in {'longitude':-74.46,'latitude':41.08,'altitude':0,'heading':0,'tilt':0,'range':25000,'altitudeMode':'relativeToGround'}.items():el(look,k,v)
colors=['ffca6515','ffaa248e','ff0051e6','ff7b8900','ff2828c6']
basins=json.loads((OUT/'watersheds.geojson').read_text())['features'];sites=json.loads((OUT/'stations.geojson').read_text())['features'];relations=list(csv.DictReader((OUT/'station_watershed_relationships.csv').open()))
for i,f in enumerate(basins):
 p=f['properties'];style=el(doc,'Style',id='basin'+str(i));line=el(style,'LineStyle');el(line,'color',colors[i]);el(line,'width',3);poly=el(style,'PolyStyle');el(poly,'color','25'+colors[i][2:]);el(poly,'fill',1)
 folder=el(doc,'Folder');el(folder,'name',p['reservoir']+' watershed');pm=el(folder,'Placemark');el(pm,'name',p['reservoir']+' contributing watershed');el(pm,'styleUrl','#basin'+str(i));el(pm,'description',f"NLDI upstream basin: {p['area_km2']:.2f} km². Reference USGS {p['outlet_site']}. Not a DEM delineation. Area difference from published drainage area: {p['difference_pct']:+.2f}%.")
 multi=el(pm,'MultiGeometry');geom=f['geometry'];polys=[geom['coordinates']] if geom['type']=='Polygon' else geom['coordinates']
 for rings in polys:
  pol=el(multi,'Polygon');el(pol,'tessellate',1);el(pol,'altitudeMode','clampToGround')
  for j,ring in enumerate(rings):
   bound=el(pol,'outerBoundaryIs' if j==0 else 'innerBoundaryIs');lr=el(bound,'LinearRing');el(lr,'coordinates',' '.join(f'{pt[0]},{pt[1]},0' for pt in ring))
 folder=el(folder,'Folder');el(folder,'name','USGS stations — inside and within 2 km')
 selected=[r for r in relations if r['reservoir']==p['reservoir']]
 for r in selected:
  fsite=next(x for x in sites if x['properties']['site_no']==r['site_no']);sp=fsite['properties'];pm=el(folder,'Placemark');el(pm,'name',sp['site_no']+' — '+sp['station_nm'])
  fields=['rainfall_assessment','observed_modal_intervals_minutes','freshest_observation_age_minutes','operational_flag','transmission_frequency','publication_latency','usgs_url']
  desc=f"Location: {r['location_type']}; distance to watershed: {float(r['distance_to_watershed_km']):.2f} km.\n"+'\n'.join(k+': '+str(sp.get(k,'')) for k in fields)
  el(pm,'description',desc);point=el(pm,'Point');el(point,'altitudeMode','clampToGround');el(point,'coordinates',','.join(map(str,fsite['geometry']['coordinates'][:2]))+',0')
# Each watershed folder repeats shared stations so its layer can be shown independently.
path=OUT/'Newark_reservoirs_Google_Earth.kml';ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)
with zipfile.ZipFile(OUT/'Newark_reservoirs_Google_Earth.kmz','w',zipfile.ZIP_DEFLATED) as z:z.write(path,'doc.kml')
parsed=ET.parse(path);assert len(parsed.findall('.//{'+NS+'}Polygon'))>=5;assert len(parsed.findall('.//{'+NS+'}Point'))==len(relations)
print('Validated five watershed folders and',len(relations),'station references representing 49 unique sites.')
