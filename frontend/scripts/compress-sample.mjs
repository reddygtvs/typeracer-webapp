import { readFileSync, writeFileSync } from "node:fs";
import { gzipSync } from "node:zlib";
const input = new URL("../public/sample-data.csv", import.meta.url);
writeFileSync(
  new URL("../public/sample-data.csv.gz", import.meta.url),
  gzipSync(readFileSync(input), { level: 9 }),
);
