import json,subprocess,re,sys,concurrent.futures,time,pathlib
base=sys.argv[1]; label=sys.argv[2]; root=pathlib.Path(__file__).resolve().parents[1]
resolve=['--resolve',sys.argv[3]] if len(sys.argv)>3 else []
def request(path,body=None):
 cmd=['curl',*resolve,'--compressed','-sS','--max-time','90','-o','/dev/null','-w','%{json}',base+path]
 if body: cmd+=['-H','Content-Type: application/json','--data-binary','@'+str(body)]
 r=subprocess.run(cmd,capture_output=True,text=True); d=json.loads(r.stdout); return {k:d.get(k) for k in ['http_code','time_namelookup','time_connect','time_appconnect','time_starttransfer','time_total','size_download','speed_download']}
html=subprocess.check_output(['curl',*resolve,'-sS',base+'/']).decode(); assets=re.findall(r'(?:src|href)="(/assets/[^\"]+)"',html)
if label.startswith('after'): assets=sorted(set(assets+[f'/assets/{p.name}' for p in (root/'frontend/dist/assets').glob('*.js')]))
result={'resolve_override':resolve,'origin':base,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'requests':{p:[request(p) for _ in range(5)] for p in ['/',*assets,'/sample-data.csv',*(['/sample-data.csv.gz'] if label.startswith('after') else [])]}}
if label=='before':
 body=root/'metrics/request.json'; body.write_text(json.dumps({'csv_data':(root/'frontend/public/sample-data.csv').read_text()}))
 endpoints=['/stats']+['/charts/'+x for x in re.findall(r"id: '([^']+)'",(root/'frontend/src/components/ChartGrid.tsx').read_text())]
 t=time.perf_counter()
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool: result['analytics']=dict(zip(endpoints,pool.map(lambda p:request(p,body),endpoints)))
 result['analytics_wall_seconds']=time.perf_counter()-t;body.unlink()
(root/f'metrics/{label}-http.json').write_text(json.dumps(result,indent=2));print(label, 'saved',len(assets),'assets')
