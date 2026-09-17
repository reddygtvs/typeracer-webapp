# TypeRacer on Cloudflare

Production: https://typeracer.tusharreddy.com/

The React app uses a TypeScript Web Worker for CSV parsing, statistics and chart data. Race data stays in the browser. The Python service is retained as a reference and rollback option. Cloudflare serves static assets. There is no runtime database or analytics API.

## Build and deploy

```sh
cd frontend
npm ci
npm run build
cd ..
wrangler deploy
```

The build compresses the public sample CSV. Modern browsers download the gzip file and decompress it locally. Browsers without DecompressionStream use the CSV file. Plotly's Cartesian bundle and the dashboard load on demand. Charts load near the visible area. Hashed JavaScript and CSS use a one-year immutable cache.

Wrangler uses the existing Cloudflare account and manages the custom domain and certificate. The home-page project is `reddygtvs/homepage-new`; its Cloudflare Pages project is `homepage-new`.

## Data rules

Use the seven columns in the TypeRacer CSV export. Accuracy accepts a fraction from 0 to 1 or an explicit percent value such as `98%`. Dates use UTC. Invalid or empty input is rejected. Input limit: 20 MB. Stored data is local to the browser and domain; it does not transfer from the old Fly domain.

## Rollback

The Fly deployment is unchanged. For a Cloudflare rollback, use `wrangler rollback` and select the prior version. The home-page link change is isolated in commit `fdb007e` and can be reverted. No Fly machine or data was deleted.

## Measurements

See `metrics/REPORT.md` for results, methods and limits. Raw measurements and the scripts are in `metrics/`.
