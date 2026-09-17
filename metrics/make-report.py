import json,statistics,pathlib,datetime,os
root=pathlib.Path(__file__).resolve().parent
b=json.loads((root/'before-http.json').read_text()); a=json.loads((root/'after-http.json').read_text()); c=json.loads((root/'after-compute.json').read_text()); br=json.loads((root/'browser.json').read_text())
med=lambda rs,k:statistics.median(r[k] for r in rs)
asset=lambda x,p:next(k for k in x['requests'] if p(k))
bjs=asset(b,lambda p:p.endswith('.js'));ajs=asset(a,lambda p:'/index-' in p and p.endswith('.js'))
size=lambda x,p:med(x['requests'][p],'size_download')
percent=lambda old,new:f'{100*(1-new/old):.1f}% less'
u=json.loads((root/'usage.json').read_text());u['codex']['last_weekly_used_percent']=70
for path in pathlib.Path('/Users/tushar/.codex/sessions').rglob('*'+os.environ['CODEX_THREAD_ID']+'*'):
 for line in path.open():
  try:e=json.loads(line)
  except:continue
  p=e.get('payload',{})
  if e.get('type')=='event_msg' and p.get('type')=='token_count' and p.get('info'):u['codex']['session_token_usage']=p['info']['total_token_usage']
u['codex']['scope']='Session token counters include repeated context and cached input. They are not unique text or a billing estimate. Account usage readings were taken during this task and include other tasks.'
(root/'usage.json').write_text(json.dumps(u,indent=2))
lines=['# TypeRacer: deployment, speed and bug report','',f'Measured {datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}.','',
'Live app: https://typeracer.tusharreddy.com/  ',
'Home page: https://tusharreddy.com/  ',
'Cloudflare Worker: `typeracer`. Production version: `81430f5a-a42d-43bf-928a-b86c32e2b97b`.  ',
'Home-page link commit: `fdb007e`. Its Cloudflare Pages production deployment is `11e18a68-a821-43e8-b028-4369e5d5a089`.','',
'## Main results','',
'| Measure | Fly version | Cloudflare version | Change |','|---|---:|---:|---|',
f'| Initial JavaScript, transferred | {size(b,bjs):,.0f} bytes | {size(a,ajs):,.0f} bytes | {percent(size(b,bjs),size(a,ajs))} |',
f'| Sample CSV download | {size(b,"/sample-data.csv"):,.0f} bytes | {size(a,"/sample-data.csv.gz"):,.0f} bytes | {percent(size(b,"/sample-data.csv"),size(a,"/sample-data.csv.gz"))} |',
f'| Sample to first chart, warm median | {statistics.median(br["before_ms"]):,.0f} ms | {statistics.median(br["after_ms"]):,.0f} ms | {percent(statistics.median(br["before_ms"]),statistics.median(br["after_ms"]))} |',
f'| HTML time to first byte, median | {med(b["requests"]["/"],"time_starttransfer")*1000:.1f} ms | {med(a["requests"]["/"],"time_starttransfer")*1000:.1f} ms | Same machine and network |',
'| Analytics API requests for full dashboard | 21 | 0 | Data stays in browser |',
'| Repeated CSV uploads for full dashboard | 21 copies | 0 | No analytics server |',
'| npm audit findings, full dependency tree | 22 | 0 | 2 critical and 13 high findings removed |','',
'Warm browser runs, alternating origins: Fly '+str(br['before_ms'])+' ms; Cloudflare '+str(br['after_ms'])+' ms. These include tool overhead. Sample size: 34,617 races. The final median improvement is about 66%; an earlier build measured 69%.','',
'## Method and limits','',
'HTTP measurements use five separate curl requests per asset, compression enabled, from this Mac. The old site was measured before edits. The new-domain curl test used a Cloudflare IP from public DNS because the local resolver retained a negative DNS result. HTTPS hostname and certificate checks remained enabled. DNS time is therefore not comparable. Browser access used the normal domain and succeeded. Small sample sizes do not establish global or long-term performance.','',
'Browser tests used the Codex in-app browser without CPU or network throttling. Warm sample tests include CSV retrieval, local/server calculations and first-chart display, but exclude the initial page download. A final first-use sample check took 568 ms after the chart bundle had been loaded by restore. No comparable cold browser baseline was captured.','',
'LCP, INP, CLS, Lighthouse score, peak browser memory, mobile CPU timing, global latency, load capacity and billing changes were not measured. No values are estimated for them. Mobile layout was checked at 390 CSS pixels (375 pixels of page content after the scrollbar).','',
'## Network details','',
'All sizes below are transferred response-body bytes. Headers are excluded. JavaScript beyond the entry file is loaded on demand.','',
'| Version / resource | Bytes | TTFB median, ms | Total min / median / max, ms |','|---|---:|---:|---:|']
for name,x in [('Fly',b),('Cloudflare',a)]:
 for p,rs in x['requests'].items():
  times=[r['time_total']*1000 for r in rs]
  lines.append(f'| {name}: `{p}` | {med(rs,"size_download"):,.0f} | {med(rs,"time_starttransfer")*1000:.1f} | {min(times):.1f} / {statistics.median(times):.1f} / {max(times):.1f} |')
lines+=['','The raw CSV remains available as a compatibility fallback. Modern browsers use the 413 KB gzip file. Hashed assets have `Cache-Control: public, max-age=31536000, immutable`. HTML is revalidated. Cloudflare returned HTTP 200 and valid HTTPS.','',
'## Calculation details','',
f'The old full-dashboard benchmark took {b["analytics_wall_seconds"]:.3f} seconds for 21 POST requests with concurrency six. This includes network time and server work. The new local Node benchmark took a median {statistics.median(r["total_ms"] for r in c["runs"]):.1f} ms for parsing, statistics and all 20 chart calculations. It excludes browser rendering and worker messaging. These measure different layers, so they are not used as a direct speed ratio.','',
f'New CSV parse median: {statistics.median(r["parse_ms"] for r in c["runs"]):.1f} ms. Statistics median: {statistics.median(r["stats_ms"] for r in c["runs"]):.1f} ms. Seven runs, Node {c["runtime"]}.','',
'| Chart | Old API total, ms | New local calculation median, ms |','|---|---:|---:|']
for p,v in b['analytics'].items():
 if p=='/stats':continue
 id=p.split('/')[-1];lines.append(f'| {id} | {v["time_total"]*1000:.1f} | {statistics.median(r["charts"][id] for r in c["runs"]):.2f} |')
lines+=['','## Bug fixes and safeguards','',
'| Issue | Result |','|---|---|',
'| Fractions printed as percentages | Accuracy now converts 0.98 to 98.0%. Chart labels, axes and hover values agree. |',
'| Rounded group values and truncated bar scale | Rank accuracy uses full calculation precision; bars start at zero. Sample ranks show 98.1%, 97.6%, 97.2%, 96.8%, 96.5%. |',
'| First race treated as a previous loss | Excluded from previous-result analysis. No previous result exists. |',
'| Unsupported insight claims | Removed claims about guaranteed wins, ideal rest, text length and causation. New insights use observed data. |',
'| UTC dates displayed in local time | Summary dates and time grouping now both use UTC. |',
'| Storage exceptions reported as analysis failure | Valid data works even when browser storage is unavailable or full. |',
'| Corrupt saved statistics and data | Statistics are recalculated on restore. Invalid stored CSV is cleared and a readable error is shown. |',
'| CSV validation gaps | Empty files, missing columns, invalid numbers, impossible dates and invalid accuracy are rejected. Explicit percentages are supported. Limit: 20 MB. |',
'| Data-change and reset races | Late asynchronous results cannot replace a newer upload or reset. Chart components reset with the dataset. |',
'| Partial-content cache keys | Removed the old unused cache helper that keyed only the first 100 CSV characters. No such cache is used. |',
'| Large-input risks in the migration | Removed quadratic previous-result lookup and spread-based min/max. Tested 150,000 rows. |',
'| Short datasets and constant data | Rolling windows show insufficient-data information. No invented first result or non-finite chart values. Undefined correlation is explained. |',
'| gzip server differences | Handles both browser-decoded gzip and explicit local decompression. |',
'| Sparse mobile rank ticks | Every integer rank can be shown. |','',
'SWE-2 produced the focused calculation patches and the insight module. Review found a missing brace, unsafe large-array operations, a sample/population deviation mismatch, and an empty-group insight error in those changes. These were corrected before the final release.','',
'## Checks','',
'- Production TypeScript build: pass.','- ESLint: pass.','- Nine automated tests: pass.','- Independent Python reference: sample race count, average WPM, best WPM, wins and average accuracy match.','- All 20 chart types: render in the browser.','- Valid CSV upload, invalid accuracy rejection, recovery, sample loading, reset and reload restore: pass.','- Desktop and mobile accuracy chart: labels fit; no horizontal page overflow.','- New domain, HTTPS, Cloudflare cache headers and live home-page link: pass.','- npm audit: zero findings in the current lockfile.','',
'## Operations and remaining limits','',
'Cloudflare serves static assets. CSV parsing and calculations run in a TypeScript Web Worker. No race-data API or database is required. Plotly is loaded only when charts are needed. Rust and WebAssembly are not required for these measurements. All calculations use the full dataset. Plotly can still use substantial browser memory for very large charts. The 20 MB input limit bounds accepted files; it does not promise smooth rendering for every file up to that limit.','',
'The old Fly app remains unchanged for rollback. It may still incur Fly charges. Nothing was deleted. Browser data stored under the old domain does not transfer to the new domain. Upload the CSV again on the new site.','',
'## Agent usage','',
'Raw counters are saved in `usage.json`. Devin CLI is available as `/opt/homebrew/bin/devin`, linked to the installed Devin app. Existing login was reused. SWE-2 is marked Free for this account. Two focused SWE-2 tasks completed; the broad review stalled and was interrupted. A small connection probe also completed.','',
'Codex weekly account usage was 65% at the first reading during this task and 70% at the later reading. This is shared account usage and is not an exact task charge. Session token counters include repeated context and cached input; they are not unique text or a billing estimate. Devin session counters are separate.','',
'Raw files: `before-http.json`, `after-http.json`, `browser.json`, `after-compute.json`, `sample-reference.json`, `before-audit.json`, `after-audit.json`, `usage.json`. Re-run `benchmark.py`, `compute-benchmark.ts`, and `npm test` to check future changes.']
(root/'REPORT.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines[10:23]))
