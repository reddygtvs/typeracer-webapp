# TypeRacer: deployment, speed and bug report

Measured 2026-09-17T07:12:00+00:00.

Live app: https://typeracer.tusharreddy.com/  
Home page: https://tusharreddy.com/  
Cloudflare Worker: `typeracer`. Production version: `81430f5a-a42d-43bf-928a-b86c32e2b97b`.  
Home-page link commit: `fdb007e`. Its Cloudflare Pages production deployment is `11e18a68-a821-43e8-b028-4369e5d5a089`.

## Main results

| Measure | Fly version | Cloudflare version | Change |
|---|---:|---:|---|
| Initial JavaScript, transferred | 2,174,785 bytes | 79,406 bytes | 96.3% less |
| Sample CSV download | 1,613,939 bytes | 413,366 bytes | 74.4% less |
| Sample to first chart, warm median | 982 ms | 337 ms | 65.7% less |
| HTML time to first byte, median | 243.7 ms | 123.5 ms | Same machine and network |
| Analytics API requests for full dashboard | 21 | 0 | Data stays in browser |
| Repeated CSV uploads for full dashboard | 21 copies | 0 | No analytics server |
| npm audit findings, full dependency tree | 22 | 0 | 2 critical and 13 high findings removed |

Warm browser runs, alternating origins: Fly [1078, 975, 982] ms; Cloudflare [337, 340, 337] ms. These include tool overhead. Sample size: 34,617 races. The final median improvement is about 66%; an earlier build measured 69%.

## Method and limits

HTTP measurements use five separate curl requests per asset, compression enabled, from this Mac. The old site was measured before edits. The new-domain curl test used a Cloudflare IP from public DNS because the local resolver retained a negative DNS result. HTTPS hostname and certificate checks remained enabled. DNS time is therefore not comparable. Browser access used the normal domain and succeeded. Small sample sizes do not establish global or long-term performance.

Browser tests used the Codex in-app browser without CPU or network throttling. Warm sample tests include CSV retrieval, local/server calculations and first-chart display, but exclude the initial page download. A final first-use sample check took 568 ms after the chart bundle had been loaded by restore. No comparable cold browser baseline was captured.

LCP, INP, CLS, Lighthouse score, peak browser memory, mobile CPU timing, global latency, load capacity and billing changes were not measured. No values are estimated for them. Mobile layout was checked at 390 CSS pixels (375 pixels of page content after the scrollbar).

## Network details

All sizes below are transferred response-body bytes. Headers are excluded. JavaScript beyond the entry file is loaded on demand.

| Version / resource | Bytes | TTFB median, ms | Total min / median / max, ms |
|---|---:|---:|---:|
| Fly: `/` | 382 | 243.7 | 148.9 / 243.8 / 258.0 |
| Fly: `/assets/index-DP6_b28q.js` | 2,174,785 | 161.8 | 418.2 / 509.9 / 679.9 |
| Fly: `/assets/index-BJdwCza0.css` | 7,596 | 173.1 | 153.1 / 173.3 / 303.7 |
| Fly: `/sample-data.csv` | 1,613,939 | 176.8 | 398.6 / 621.3 / 702.4 |
| Cloudflare: `/` | 305 | 123.5 | 117.2 / 123.9 / 138.2 |
| Cloudflare: `/assets/Dashboard-Agzcfx-3.js` | 3,851 | 139.1 | 128.4 / 141.2 / 203.4 |
| Cloudflare: `/assets/Plot-BTy9Q1XU.js` | 497,329 | 198.3 | 279.1 / 298.1 / 351.7 |
| Cloudflare: `/assets/analytics.worker-mBimA_4u.js` | 12,535 | 114.3 | 94.5 / 114.9 / 203.2 |
| Cloudflare: `/assets/index-BscEa51f.css` | 5,493 | 141.7 | 106.8 / 141.8 / 221.4 |
| Cloudflare: `/assets/index-Djkqz30s.js` | 79,406 | 141.6 | 146.1 / 177.8 / 231.3 |
| Cloudflare: `/sample-data.csv` | 1,613,939 | 127.7 | 295.2 / 322.9 / 331.0 |
| Cloudflare: `/sample-data.csv.gz` | 413,366 | 138.4 | 224.4 / 239.2 / 366.5 |

The raw CSV remains available as a compatibility fallback. Modern browsers use the 413 KB gzip file. Hashed assets have `Cache-Control: public, max-age=31536000, immutable`. HTML is revalidated. Cloudflare returned HTTP 200 and valid HTTPS.

## Calculation details

The old full-dashboard benchmark took 7.565 seconds for 21 POST requests with concurrency six. This includes network time and server work. The new local Node benchmark took a median 782.6 ms for parsing, statistics and all 20 chart calculations. It excludes browser rendering and worker messaging. These measure different layers, so they are not used as a direct speed ratio.

New CSV parse median: 68.9 ms. Statistics median: 3.3 ms. Seven runs, Node v25.2.1.

| Chart | Old API total, ms | New local calculation median, ms |
|---|---:|---:|
| wpm-distribution | 1219.8 | 3.29 |
| accuracy-distribution | 1348.6 | 2.84 |
| performance-over-time | 1389.3 | 6.58 |
| daily-performance | 1321.5 | 9.07 |
| rolling-average | 1103.6 | 1.94 |
| rank-distribution | 614.7 | 2.97 |
| hourly-performance | 692.4 | 12.41 |
| wpm-vs-accuracy | 1392.5 | 5.30 |
| win-rate-monthly | 892.2 | 3.77 |
| top-texts | 965.0 | 199.62 |
| consistency-score | 1747.0 | 28.55 |
| accuracy-by-rank | 1100.2 | 2.95 |
| cumulative-accuracy | 1536.7 | 1.46 |
| wpm-by-rank-boxplot | 1127.9 | 2.52 |
| racers-impact | 927.0 | 2.77 |
| frequent-texts-improvement | 691.5 | 180.75 |
| top-texts-distribution | 593.9 | 184.82 |
| win-rate-after-win | 2795.6 | 1.70 |
| fastest-slowest-races | 4276.9 | 6.84 |
| time-between-races | 4207.5 | 20.00 |

## Bug fixes and safeguards

| Issue | Result |
|---|---|
| Fractions printed as percentages | Accuracy now converts 0.98 to 98.0%. Chart labels, axes and hover values agree. |
| Rounded group values and truncated bar scale | Rank accuracy uses full calculation precision; bars start at zero. Sample ranks show 98.1%, 97.6%, 97.2%, 96.8%, 96.5%. |
| First race treated as a previous loss | Excluded from previous-result analysis. No previous result exists. |
| Unsupported insight claims | Removed claims about guaranteed wins, ideal rest, text length and causation. New insights use observed data. |
| UTC dates displayed in local time | Summary dates and time grouping now both use UTC. |
| Storage exceptions reported as analysis failure | Valid data works even when browser storage is unavailable or full. |
| Corrupt saved statistics and data | Statistics are recalculated on restore. Invalid stored CSV is cleared and a readable error is shown. |
| CSV validation gaps | Empty files, missing columns, invalid numbers, impossible dates and invalid accuracy are rejected. Explicit percentages are supported. Limit: 20 MB. |
| Data-change and reset races | Late asynchronous results cannot replace a newer upload or reset. Chart components reset with the dataset. |
| Partial-content cache keys | Removed the old unused cache helper that keyed only the first 100 CSV characters. No such cache is used. |
| Large-input risks in the migration | Removed quadratic previous-result lookup and spread-based min/max. Tested 150,000 rows. |
| Short datasets and constant data | Rolling windows show insufficient-data information. No invented first result or non-finite chart values. Undefined correlation is explained. |
| gzip server differences | Handles both browser-decoded gzip and explicit local decompression. |
| Sparse mobile rank ticks | Every integer rank can be shown. |

SWE-2 produced the focused calculation patches and the insight module. Review found a missing brace, unsafe large-array operations, a sample/population deviation mismatch, and an empty-group insight error in those changes. These were corrected before the final release.

## Checks

- Production TypeScript build: pass.
- ESLint: pass.
- Nine automated tests: pass.
- Independent Python reference: sample race count, average WPM, best WPM, wins and average accuracy match.
- All 20 chart types: render in the browser.
- Valid CSV upload, invalid accuracy rejection, recovery, sample loading, reset and reload restore: pass.
- Desktop and mobile accuracy chart: labels fit; no horizontal page overflow.
- New domain, HTTPS, Cloudflare cache headers and live home-page link: pass.
- npm audit: zero findings in the current lockfile.

## Operations and remaining limits

Cloudflare serves static assets. CSV parsing and calculations run in a TypeScript Web Worker. No race-data API or database is required. Plotly is loaded only when charts are needed. Rust and WebAssembly are not required for these measurements. All calculations use the full dataset. Plotly can still use substantial browser memory for very large charts. The 20 MB input limit bounds accepted files; it does not promise smooth rendering for every file up to that limit.

The old Fly app remains unchanged for rollback. It may still incur Fly charges. Nothing was deleted. Browser data stored under the old domain does not transfer to the new domain. Upload the CSV again on the new site.

## Agent usage

Raw counters are saved in `usage.json`. Devin CLI is available as `/opt/homebrew/bin/devin`, linked to the installed Devin app. Existing login was reused. SWE-2 is marked Free for this account. Two focused SWE-2 tasks completed; the broad review stalled and was interrupted. A small connection probe also completed.

Codex weekly account usage was 65% at the first reading during this task and 70% at the later reading. This is shared account usage and is not an exact task charge. Session token counters include repeated context and cached input; they are not unique text or a billing estimate. Devin session counters are separate.

Raw files: `before-http.json`, `after-http.json`, `browser.json`, `after-compute.json`, `sample-reference.json`, `before-audit.json`, `after-audit.json`, `usage.json`. Re-run `benchmark.py`, `compute-benchmark.ts`, and `npm test` to check future changes.
