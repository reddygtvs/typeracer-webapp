import {readFileSync,writeFileSync} from 'node:fs';
import {performance} from 'node:perf_hooks';
import {parseCSV,stats,chart} from '../frontend/src/utils/analytics.ts';
const csv=readFileSync(new URL('../frontend/public/sample-data.csv',import.meta.url),'utf8');
const ids=[...readFileSync(new URL('../frontend/src/components/ChartGrid.tsx',import.meta.url),'utf8').matchAll(/id: ["']([^"']+)["']/g)].map(m=>m[1]);
const runs=[];
for(let i=0;i<7;i++){
 const start=performance.now();const rows=parseCSV(csv);const parse_ms=performance.now()-start;
 const statStart=performance.now();const result=stats(rows);const stats_ms=performance.now()-statStart;
 const charts:Record<string,number>={};for(const id of ids){const t=performance.now();chart(id,rows);charts[id]=performance.now()-t;}
 runs.push({parse_ms,stats_ms,charts,total_ms:performance.now()-start,stats:result});
}
writeFileSync(new URL(process.env.METRICS_OUTPUT || './after-compute.json',import.meta.url),JSON.stringify({runtime:process.version,method:'Node.js on this Mac; parse + stats + all 20 chart calculations, excludes rendering and worker messaging.',runs},null,2));
console.log(runs.map(r=>r.total_ms));
