import { readFileSync, existsSync, unlinkSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import { Client } from 'basic-ftp';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const envPath = resolve(root, '.env.deploy.local');

const BUILD_ENV_KEYS = ['VITE_BASE_PATH', 'VITE_WS_URL', 'VITE_API_URL'];

function loadDeployEnv() {
  if (!existsSync(envPath)) {
    console.error('Falta .env.deploy.local (copia desde .env.deploy.example)');
    process.exit(1);
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

function detectPackageManager() {
  if (existsSync(resolve(root, 'pnpm-lock.yaml'))) return 'pnpm';
  if (existsSync(resolve(root, 'yarn.lock'))) return 'yarn';
  return 'npm';
}

function runBuild(deployConfig) {
  const packageManager = detectPackageManager();
  const buildCommand = packageManager === 'yarn' ? ['run', 'build'] : ['run', 'build'];
  const command = packageManager;
  const args = packageManager === 'npm' ? buildCommand : buildCommand;

  return new Promise((resolvePromise, reject) => {
    const environment = { ...process.env };
    for (const key of BUILD_ENV_KEYS) {
      if (deployConfig[key]) environment[key] = deployConfig[key];
    }

    const child = spawn(command, args, {
      cwd: root,
      env: environment,
      stdio: 'inherit',
      shell: true,
    });
    child.on('close', (code) =>
      code === 0 ? resolvePromise() : reject(new Error(`build falló (${code})`)),
    );
  });
}

async function deployFtp(deployConfig) {
  const ftpClient = new Client(60_000);
  ftpClient.ftp.verbose = process.env.FTP_VERBOSE === '1';

  const port = Number(deployConfig.FTP_PORT || 21);
  const secure = deployConfig.FTP_SECURE === 'true';

  await ftpClient.access({
    host: deployConfig.FTP_HOST,
    user: deployConfig.FTP_USER,
    password: deployConfig.FTP_PASSWORD,
    port,
    secure,
  });

  const remoteDir = (deployConfig.FTP_REMOTE_DIR || '')
    .replace(/\\/g, '/')
    .replace(/^\/+|\/+$/g, '');
  const distPath = resolve(root, 'dist');
  // Keep the live tunnel URL published by start-expenses-stack.ps1
  const runtimeConfigPath = join(distPath, 'runtime-config.json');
  if (existsSync(runtimeConfigPath)) {
    unlinkSync(runtimeConfigPath);
  }

  await ftpClient.cd('/');
  console.log(`Subiendo ${distPath} → /${remoteDir || ''}…`);
  await ftpClient.uploadFromDir(distPath, remoteDir || undefined);
  ftpClient.close();
}

const deployConfig = loadDeployEnv();
const requiredKeys = ['FTP_HOST', 'FTP_USER', 'FTP_PASSWORD'];
for (const requiredKey of requiredKeys) {
  if (!deployConfig[requiredKey]) {
    console.error(`Falta ${requiredKey} en .env.deploy.local`);
    process.exit(1);
  }
}

console.log('Build de producción…');
for (const key of BUILD_ENV_KEYS) {
  if (deployConfig[key]) console.log(`  ${key}=${deployConfig[key]}`);
}

await runBuild(deployConfig);
await deployFtp(deployConfig);
console.log('Despliegue FTP completado.');
