const fs = require('fs');
const p = process.argv[2];
const buf = fs.readFileSync(p);
console.log('BOM:', buf[0] === 0xef && buf[1] === 0xbb && buf[2] === 0xbf);
const content = buf.toString('utf8');
const m = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
console.log('frontmatter found:', !!m);
if (m) {
  for (const line of m[1].split(/\r?\n/)) {
    const i = line.indexOf(':');
    if (i > 0) console.log('key=[' + line.slice(0, i).trim() + '] valueLen=' + line.slice(i + 1).trim().length);
  }
}