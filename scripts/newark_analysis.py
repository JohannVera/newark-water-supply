"""Reproduce Newark NLDI basins, station inventory and timing evidence. Run from clone."""
from pathlib import Path
import io,json,datetime,html,time,argparse
from concurrent.futures import ThreadPoolExecutor
import requests,pandas as pd,geopandas as gpd,folium
ROOT=Path(__file__).resolve().parents[1]
CONFIG={'canistear':('Canistear','01382100',6.08),'oak_ridge':('Oak Ridge','01382200',27.3),'charlotteburg':('Charlotteburg','01382380',56.2),'clinton':('Clinton','01382300',10.5),'echo_lake':('Echo Lake','01382400',4.35)}
CRS=32618
LOG=[]
def fetch(url,params,out):
    out.parent.mkdir(parents=True,exist_ok=True)
    r=requests.get(url,params=params,timeout=60);r.raise_for_status()
    out.write_text(r.text,encoding='utf-8')
    LOG.append({'url':r.url,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'file':str(out.relative_to(ROOT))})
    return r

def rdb(text):
    lines=[l for l in text.splitlines() if l and not l.startswith('#')]
    if len(lines)<2: raise ValueError('Invalid RDB response')
    return pd.read_csv(io.StringIO('\n'.join([lines[0]]+lines[2:])),sep='\t',dtype=str).fillna('')

def basin(key):
    name,site,area=CONFIG[key]; out=ROOT/'data'/key;raw=out/'sources'
    # Reuse existing validated boundaries; do not overwrite their source snapshots.
    target=out/'watershed.geojson'
    if target.exists():
        b=gpd.read_file(target).to_crs(CRS);method='reused existing NLDI basin'
    else:
        j=fetch(f'https://api.water.usgs.gov/nldi/linked-data/nwissite/USGS-{site}/basin',{'simplified':'false'},raw/'nldi_basin.geojson').json()
        b=gpd.GeoDataFrame.from_features(j['features'],crs=4326).to_crs(CRS)
        b=gpd.GeoDataFrame({'name':[name]},geometry=[b.geometry.union_all()],crs=CRS)
        b.to_crs(4326).to_file(target,driver='GeoJSON');method='new NLDI unsimplified basin retrieval'
    assert len(b)==1 and b.is_valid.all() and not b.geometry.is_empty.any()
    geom=b.geometry.iloc[0];a=geom.area/1e6
    report={'reservoir':name,'outlet_site':site,'area_km2':a,'published_area_sqmi':area,'difference_pct':100*(a/2.589988110336/area-1),'method':method,'boundary_valid':bool(geom.is_valid)}
    (out/'analysis_validation.json').write_text(json.dumps(report,indent=2))
    return key,b,report

def run():
    out=ROOT/'data'/'consolidated';out.mkdir(parents=True,exist_ok=True)
    basins={};reports=[]
    for key in CONFIG:
        print('Basin',key,flush=True);k,b,report=basin(key);basins[k]=b;reports.append(report)
    # One all-status site search across all buffered polygons, followed by exact geometry.
    union=gpd.GeoSeries([b.geometry.iloc[0] for b in basins.values()],crs=CRS).union_all()
    buffered=union.buffer(2000)
    w,s,e,n=gpd.GeoSeries([buffered],crs=CRS).to_crs(4326).total_bounds
    raw=out/'sources'
    sites=rdb(fetch('https://waterservices.usgs.gov/nwis/site/',{'format':'rdb','bBox':f'{w:.7f},{s:.7f},{e:.7f},{n:.7f}','siteStatus':'all','siteOutput':'expanded'},raw/'sites.rdb').text)
    sites=gpd.GeoDataFrame(sites,geometry=gpd.points_from_xy(pd.to_numeric(sites.dec_long_va),pd.to_numeric(sites.dec_lat_va)),crs=4326).to_crs(CRS)
    sites=sites[sites.intersects(buffered)].drop_duplicates('site_no').copy()
    ids=','.join(sites.site_no)
    # Series catalog preserves variable-specific historical availability, including non-IV records.
    catalog=rdb(fetch('https://waterservices.usgs.gov/nwis/site/',{'format':'rdb','sites':ids,'seriesCatalogOutput':'true','siteStatus':'all'},raw/'series_catalog.rdb').text)
    catalog.to_csv(out/'usgs_series_catalog.csv',index=False)
    # Last seven days of IV: observation spacing is not a telemetry interval.
    iv=fetch('https://waterservices.usgs.gov/nwis/iv/',{'format':'json','sites':ids,'period':'P7D','siteStatus':'all'},raw/'instantaneous_values.json').json()
    retrieved=datetime.datetime.now(datetime.timezone.utc)
    metrics=[]
    for ts in iv.get('value',{}).get('timeSeries',[]):
        sid=ts['sourceInfo']['siteCode'][0]['value'];var=ts['variable'];code=var['variableCode'][0]['value']
        vals=[v for group in ts['values'] for v in group['value']]
        good=[v for v in vals if str(v['value'])!=str(var.get('noDataValue',-999999))]
        dates=pd.to_datetime([v['dateTime'] for v in good],utc=True).sort_values().drop_duplicates()
        gaps=pd.Series(dates).diff().dt.total_seconds().dropna()/60
        metrics.append({'site_no':sid,'parameter_cd':code,'variable':var['variableDescription'],'unit':var.get('unit',{}).get('unitCode',''),'valid_observations':len(dates),'first_observation':str(dates.min()) if len(dates) else '', 'last_observation':str(dates.max()) if len(dates) else '', 'modal_interval_minutes':float(gaps.mode().iloc[0]) if len(gaps) else None,'max_gap_minutes':float(gaps.max()) if len(gaps) else None,'latest_age_minutes':(retrieved-dates.max().to_pydatetime()).total_seconds()/60 if len(dates) else None,'retrieved_utc':retrieved.isoformat(),'transmission_frequency':'not station-specifically verified','publication_latency':'not measured; API has observation times, not first-publication times'})
    timing=pd.DataFrame(metrics)
    timing.to_csv(out/'station_timing_by_variable.csv',index=False)
    # All variables and periods from published series metadata, not assumed from site type.
    rows=[]
    for _,site in sites.iterrows():
        sid=site.site_no;sc=catalog[catalog.site_no==sid];tm=timing[timing.site_no==sid] if len(timing) else pd.DataFrame()
        variables=sorted(set(sc.get('parm_cd',pd.Series(dtype=str))))
        periods='; '.join(sorted(set(f"{r.get('data_type_cd','')}:{r.get('parm_cd','')} {r.get('begin_date','')} to {r.get('end_date','')}" for _,r in sc.iterrows())))
        rainfall=tm[tm.parameter_cd=='00045'] if len(tm) else pd.DataFrame()
        rainnote='No valid precipitation IV in seven-day query; historical availability may differ'
        if len(rainfall) and rainfall.valid_observations.sum()>0:rainnote='Precipitation IV present; verify accumulation/reset convention and radar time-step alignment'
        ages=tm.latest_age_minutes.dropna() if len(tm) else pd.Series(dtype=float)
        intervals=sorted(set(tm.modal_interval_minutes.dropna())) if len(tm) else []
        flag='No recent valid IV; not demonstrated for near-real-time use' if not len(ages) else 'Recent IV found; telemetry and delivery SLA unverified'
        if any(x>=60 for x in intervals):flag+='; one or more series has hourly-or-coarser modal observation spacing'
        if len(ages) and ages.min()>60:flag+='; freshest series older than 60 minutes at retrieval'
        row={'site_no':sid,'station_nm':site.station_nm,'site_tp_cd':site.site_tp_cd,'latitude':float(site.dec_lat_va),'longitude':float(site.dec_long_va),'parameter_codes':','.join(variables),'availability_by_series':periods or 'No series returned','observed_modal_intervals_minutes':','.join(map(str,intervals)),'freshest_observation_age_minutes':float(ages.min()) if len(ages) else None,'rainfall_assessment':rainnote,'operational_flag':flag,'transmission_frequency':'Unknown for this station; USGS general guidance often hourly, not a site-specific finding','publication_latency':'Unknown; latest observation age is not publication latency','usgs_url':f'https://waterdata.usgs.gov/monitoring-location/USGS-{sid}/'}
        rows.append(row)
    inventory=pd.DataFrame(rows);inventory.to_csv(out/'usgs_station_inventory.csv',index=False)
    relations=[]
    for key,b in basins.items():
        geom=b.geometry.iloc[0];subset=sites[sites.intersects(geom.buffer(2000))].copy()
        for _,st in subset.iterrows():
            relation={'reservoir':CONFIG[key][0],'key':key,'site_no':st.site_no,'location_type':'inside' if geom.covers(st.geometry) else 'nearby_outside','distance_to_watershed_km':st.geometry.distance(geom)/1000,'relevance':'Spatial inclusion only; variable and hydraulic connectivity require review'}
            if st.site_no==CONFIG[key][1]:relation['relevance']='Reservoir outlet/reference station; reservoir level/storage is not rainfall'
            relations.append(relation)
        rel=pd.DataFrame([r for r in relations if r['key']==key]);rel.merge(inventory,on='site_no').to_csv(ROOT/'data'/key/'station_analysis.csv',index=False)
    relations=pd.DataFrame(relations);relations.to_csv(out/'station_watershed_relationships.csv',index=False)
    # Consolidated polygons include nested catchments; do not add their areas.
    features=[]
    for key,b in basins.items():
        j=json.loads(b.to_crs(4326).to_json());f=j['features'][0];f['properties']=next(x for x in reports if x['reservoir']==CONFIG[key][0]);features.append(f)
    (out/'watersheds.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features}))
    points=gpd.GeoDataFrame(inventory,geometry=gpd.points_from_xy(inventory.longitude,inventory.latitude),crs=4326)
    points.to_file(out/'stations.geojson',driver='GeoJSON')
    make_map(out,basins,sites,inventory,relations,reports)
    pd.DataFrame(reports).to_csv(out/'basin_validation.csv',index=False)
    (out/'provenance.json').write_text(json.dumps({'retrieved_utc':retrieved.isoformat(),'buffer_km':2,'sources':LOG,'existing_boundaries':'Reused from repository; previous raw source responses retained','latency_definition':'Latest age = retrieval UTC minus observation UTC; not transmission or first-publication latency'},indent=2))
    print(pd.DataFrame(reports).to_string(index=False));print('Unique sites:',len(inventory),'IV series:',len(timing),flush=True)

def make_map(out,basins,sites,inventory,relations,reports):
    m=folium.Map(location=[41.08,-74.46],zoom_start=11,tiles='OpenStreetMap')
    colors=['#1565c0','#8e24aa','#e65100','#00897b','#c62828']
    for (key,b),color in zip(basins.items(),colors):
        name,sid,_=CONFIG[key];g=folium.FeatureGroup(name=name+' contributing watershed')
        folium.GeoJson(b.to_crs(4326),style_function=lambda f,c=color:{'color':c,'weight':3,'fillOpacity':.07},tooltip=name+' (upstream basin)').add_to(g);g.add_to(m)
        st=sites[sites.site_no==sid]
        if len(st):
            p=st.iloc[0];folium.Marker([float(p.dec_lat_va),float(p.dec_long_va)],tooltip=name+' reservoir reference station',popup=f'{name}: USGS {sid}. Marker represents reservoir reference station, not water-surface extent.',icon=folium.Icon(color='blue',icon='tint')).add_to(m)
    groups={x:folium.FeatureGroup(name=x) for x in ['Precipitation IV present','Other recent IV','No recent valid IV']}
    for _,p in inventory.iterrows():
        rel=relations[relations.site_no==p.site_no];location='; '.join(rel.reservoir+': '+rel.location_type)
        text=''.join(f'<b>{html.escape(k)}:</b> {html.escape(str(v))}<br>' for k,v in p.items() if k!='usgs_url')
        text+='<b>Watershed relation:</b> '+html.escape(location)+f'<br><a href="{p.usgs_url}" target="_blank">USGS station</a>'
        cat='Precipitation IV present' if p.rainfall_assessment.startswith('Precipitation IV present') else ('No recent valid IV' if p.operational_flag.startswith('No recent') else 'Other recent IV')
        folium.CircleMarker([p.latitude,p.longitude],radius=5,color={'Precipitation IV present':'green','Other recent IV':'blue','No recent valid IV':'gray'}[cat],fill=True,tooltip=p.site_no+' '+p.station_nm,popup=folium.Popup(text,max_width=550)).add_to(groups[cat])
    for g in groups.values():g.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    bounds=gpd.GeoSeries([b.geometry.iloc[0] for b in basins.values()],crs=CRS).to_crs(4326).total_bounds
    m.fit_bounds([[bounds[1],bounds[0]],[bounds[3],bounds[2]]])
    m.get_root().html.add_child(folium.Element('<div style="position:fixed;bottom:15px;left:15px;z-index:9999;background:white;padding:12px;max-width:420px;font:13px Arial"><b>Newark reservoir system — USGS inventory</b><br>Five NLDI upstream basins, including nested watersheds. Reservoir markers indicate reference stations.<br>Nearby = within 2 km outside a basin; connectivity not established.<br>Observation age does not measure publication latency. Telemetry unverified.<br>Internet required for map libraries and tiles.</div>'))
    m.save(out/'newark_system_map.html')
if __name__=='__main__':run()
