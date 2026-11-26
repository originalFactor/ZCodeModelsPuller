const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const workdir = 'E:/GitHub/originalFactor/ZCodeModelsPuller';
const outFile = path.join(workdir, 'tmp_publish_out.txt');
const cmdFile = path.join(workdir, 'tmp_publish_cmd.txt');
const MAX_MS = 15 * 60 * 1000;

fs.writeFileSync(outFile, '');
fs.writeFileSync(cmdFile, '');

const command = 'redskillhub-upload publish "E:\\GitHub\\originalFactor\\ZCodeModelsPuller\\skill\\zcode-model-puller" --agent --source original --tag "效率工具" --env prod';
const append = (d) => fs.appendFileSync(outFile, d);
append(`__CMD__ ${command}\n`);

const p = spawn(command, [], { shell: true });
const t0 = Date.now();

p.stdout.on('data', append);
p.stderr.on('data', append);
p.on('error', (e) => append(`__SPAWN_ERROR__ ${e.message}\n`));
p.on('exit', (code) => {
  append(`\n__EXIT__ code=${code}\n`);
  clearInterval(timer);
  process.exit(0);
});

const timer = setInterval(() => {
  if (Date.now() - t0 > MAX_MS) {
    append('\n__TIMEOUT__\n');
    try { p.kill(); } catch {}
    clearInterval(timer);
    process.exit(0);
  }
  let c = '';
  try { c = fs.readFileSync(cmdFile, 'utf8').trim(); } catch {}
  if (c) {
    fs.writeFileSync(cmdFile, '');
    append(`\n__STDIN_SENT__ ${c}\n`);
    p.stdin.write(c + '\n');
  }
}, 800);