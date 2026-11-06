import { readFileSync, writeFileSync } from 'node:fs';

const clientPath = new URL('../frontend/static/js/api.js', import.meta.url);
const source = readFileSync(clientPath, 'utf8');
const moduleMarker = /\nexport \{\};\s*$/;

if (!moduleMarker.test(source)) {
  throw new Error('Expected the generated API client to end with a TypeScript module marker.');
}

writeFileSync(clientPath, source.replace(moduleMarker, '\n'));
