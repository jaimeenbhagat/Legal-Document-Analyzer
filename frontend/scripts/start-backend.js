/**
 * Backend Process Manager
 * 
 * This script starts the Python FastAPI backend as a child process
 * when Next.js dev server starts. The backend runs on port 8000 internally,
 * but users only interact with port 3000 (Next.js proxies API calls).
 * 
 * Architecture:
 *   User → localhost:3000 → Next.js → (proxy /api/*) → localhost:8000 (Python)
 */

const { spawn } = require('child_process');
const path = require('path');

const PROJECT_ROOT = path.resolve(__dirname, '..', '..');
const BACKEND_PORT = process.env.BACKEND_PORT || 8000;

console.log('🐍 Starting Python backend server...');
console.log(`📁 Project root: ${PROJECT_ROOT}`);

// Start uvicorn with the backend module
const backend = spawn('uvicorn', [
  'backend.main:app',
  '--host', '127.0.0.1',
  '--port', String(BACKEND_PORT),
  '--reload'
], {
  cwd: PROJECT_ROOT,
  stdio: ['inherit', 'pipe', 'pipe'],
  env: {
    ...process.env,
    PYTHONUNBUFFERED: '1'
  }
});

// Prefix backend output
backend.stdout.on('data', (data) => {
  const lines = data.toString().trim().split('\n');
  lines.forEach(line => {
    if (line.trim()) {
      console.log(`[BACKEND] ${line}`);
    }
  });
});

backend.stderr.on('data', (data) => {
  const lines = data.toString().trim().split('\n');
  lines.forEach(line => {
    if (line.trim()) {
      console.error(`[BACKEND] ${line}`);
    }
  });
});

backend.on('error', (err) => {
  console.error('❌ Failed to start backend:', err.message);
  console.error('Make sure Python and uvicorn are installed.');
  process.exit(1);
});

backend.on('close', (code) => {
  if (code !== 0 && code !== null) {
    console.error(`❌ Backend exited with code ${code}`);
  }
});

// Handle process termination
const cleanup = () => {
  console.log('\n🛑 Stopping backend server...');
  backend.kill('SIGTERM');
  setTimeout(() => {
    backend.kill('SIGKILL');
    process.exit(0);
  }, 2000);
};

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
process.on('exit', () => backend.kill());

// Keep the process running
process.stdin.resume();
