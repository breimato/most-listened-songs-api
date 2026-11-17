import { readFileSync, writeFileSync, existsSync, mkdtempSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';
import { Client } from 'basic-ftp';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const envPath = resolve(root, '.env.deploy.local');

function loadDeployEnv() {
  if (!existsSync(envPath)) {
    throw new Error('Falta frontend/.env.deploy.local');
  }
  const env = {};
  for (const line of readFileSync(envPath, 'utf8').split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const indexOfEquals = trimmed.indexOf('=');
    if (indexOfEquals === -1) continue;
    env[trimmed.slice(0, indexOfEquals).trim()] = trimmed.slice(indexOfEquals + 1).trim();
  }
  return env;
}

const apiUrl = (process.argv[2] || '').trim().replace(/\/$/, '');
if (!apiUrl) {
  console.error('Uso: node scripts/upload-runtime-config.mjs <https://tunnel-url>');
  process.exit(1);
}

const deployConfig = loadDeployEnv();
const tempDir = mkdtempSync(join(tmpdir(), 'canciones-runtime-'));
const localFile = join(tempDir, 'runtime-config.json');
writeFileSync(localFile, `${JSON.stringify({ apiUrl }, null, 2)}\n`, 'utf8');

const ftpClient = new Client(60_000);
const port = Number(deployConfig.FTP_PORT || 21);
const secure = deployConfig.FTP_SECURE === 'true';
const remoteDir = (deployConfig.FTP_REMOTE_DIR || '')
  .replace(/\\/g, '/')
  .replace(/^\/+|\/+$/g, '');

await ftpClient.access({
  host: deployConfig.FTP_HOST,
  user: deployConfig.FTP_USER,
  password: deployConfig.FTP_PASSWORD,
  port,
  secure,
});

await ftpClient.cd('/');
if (remoteDir) {
  await ftpClient.ensureDir(remoteDir);
}
await ftpClient.uploadFrom(localFile, 'runtime-config.json');
ftpClient.close();

console.log(`runtime-config.json → apiUrl=${apiUrl}`);
