import { readdir, readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const frontend = path.join(root, 'frontend');
const tokenFile = path.join(frontend, 'static', 'css', 'tokens.css');
const files = [];

async function collect(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      await collect(fullPath);
    } else if (/\.(?:css|html|js)$/i.test(entry.name)) {
      files.push(fullPath);
    }
  }
}

await collect(frontend);

const findings = [];
const colorUtility = /\b(?:bg|text|border|fill|stroke)-(?:red|blue|green|gray|grey|white|black|slate|zinc|neutral|stone|amber|orange|yellow|purple|pink|indigo|emerald|teal|cyan)-(?:\d{2,3}|white|black)\b/g;
const emoji = /\p{Extended_Pictographic}/u;

function addFindings(file, source, expression, message, selectorCheck = null) {
  for (const match of source.matchAll(expression)) {
    if (selectorCheck && !selectorCheck(match)) continue;
    const line = source.slice(0, match.index).split(/\r?\n/).length;
    findings.push(`${path.relative(root, file)}:${line}: ${message}`);
  }
}

for (const file of files) {
  const source = await readFile(file, 'utf8');
  const isTokens = path.resolve(file) === path.resolve(tokenFile);
  if (!isTokens) {
    addFindings(file, source, /#[\da-f]{3,8}\b/gi, 'raw hex colour; use a design token');
    addFindings(file, source, /\b(?:rgb|rgba|hsl|hsla)\s*\(/gi, 'raw RGB/HSL colour; use a design token');
  }

  if (/\.(?:css|html)$/i.test(file)) {
    addFindings(file, source, /(?:linear|radial|conic)-gradient\s*\(/gi, 'gradient is not allowed');
    addFindings(file, source, /text-transform\s*:\s*uppercase\b/gi, 'uppercase text transformation is not allowed');
    addFindings(file, source, /font-weight\s*:\s*(?:[7-9]00|[1-9]\d{3}|bold|bolder)\b/gi, 'font weight must not exceed 600');
    addFindings(
      file,
      source,
      /([^{}]+)\{([^{}]*\bborder-radius\s*:\s*9999px\b[^{}]*)\}/gi,
      '9999px radius is reserved for avatars',
      match => !/avatar/i.test(match[1])
    );
  }

  addFindings(file, source, colorUtility, 'Tailwind colour utility is not allowed');
  if (emoji.test(source)) addFindings(file, source, /\p{Extended_Pictographic}/gu, 'emoji is not allowed in UI strings');
}

if (findings.length) {
  console.error(`Design lint failed with ${findings.length} violation(s):`);
  for (const finding of findings) console.error(`- ${finding}`);
  process.exitCode = 1;
} else {
  console.log(`Design lint passed (${files.length} frontend files checked).`);
}
