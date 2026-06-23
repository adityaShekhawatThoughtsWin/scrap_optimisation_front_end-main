/**
 * Production launcher — starts backend silently, opens default browser, single instance.
 * NOTE: Solver management is currently DISABLED (commented out) — run solver.exe separately
 * To re-enable automatic solver management, uncomment the marked sections below
 * Usage: node launcher/launch.mjs
 * Packaged: {APP_ROOT}/node.exe launcher/launch.mjs
 */
import { spawn, exec } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const APP_ROOT = process.env.APP_ROOT ?? path.resolve(__dirname, "..");
const BACKEND_DIR = path.join(APP_ROOT, "backend");
const BACKEND_ENTRY = path.join(BACKEND_DIR, "dist", "server.js");
const CONFIG_DIR = path.join(APP_ROOT, "config");
const LOCK_FILE = path.join(CONFIG_DIR, "launcher.lock");
const LOG_FILE = path.join(CONFIG_DIR, "launcher.log");

// ========== SOLVER MANAGEMENT (DISABLED - UNCOMMENT TO RE-ENABLE) ==========
// const SOLVER_LOG = path.join(CONFIG_DIR, "solver.log");
// const SOLVER_EXE = () => path.join(APP_ROOT, "solver.exe");
// const SOLVER_HEALTH_URL = "http://127.0.0.1:5000/health";
// ========================================================================

const APP_PORT = process.env.PORT ?? "3000";
const APP_URL = process.env.APP_URL ?? `http://127.0.0.1:${APP_PORT}`;
const HEALTH_URL = `${APP_URL}/api/v1/health`;

const NODE_BIN =
  process.env.NODE_BIN ??
  (process.platform === "win32" && fs.existsSync(path.join(APP_ROOT, "node.exe"))
    ? path.join(APP_ROOT, "node.exe")
    : process.execPath);

let backendProcess = null;
// let solverProcess = null;  // DISABLED - UNCOMMENT TO RE-ENABLE
// let solverLogFd = null;     // DISABLED - UNCOMMENT TO RE-ENABLE
let exiting = false;

const log = (message) => {
  const line = `[${new Date().toISOString()}] ${message}\n`;
  fs.mkdirSync(CONFIG_DIR, { recursive: true });
  fs.appendFileSync(LOG_FILE, line);
  if (process.env.LAUNCHER_VERBOSE === "1") {
    console.log(message);
  }
};

const isProcessAlive = (pid) => {
  if (!pid || pid <= 0) return false;
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
};

const readLock = () => {
  if (!fs.existsSync(LOCK_FILE)) return null;
  try {
    return JSON.parse(fs.readFileSync(LOCK_FILE, "utf8"));
  } catch {
    return null;
  }
};

const writeLock = (pid) => {
  fs.mkdirSync(CONFIG_DIR, { recursive: true });
  fs.writeFileSync(
    LOCK_FILE,
    JSON.stringify({
      pid,
      port: Number(APP_PORT),
      url: APP_URL,
      startedAt: new Date().toISOString(),
    })
  );
};

const clearLock = () => {
  try {
    if (fs.existsSync(LOCK_FILE)) fs.unlinkSync(LOCK_FILE);
  } catch {
    /* ignore */
  }
};

const isBackendReady = async () => {
  try {
    const res = await fetch(HEALTH_URL, { signal: AbortSignal.timeout(2000) });
    if (!res.ok) return false;
    const body = await res.json();
    return body?.status === "UP";
  } catch {
    return false;
  }
};

const showErrorDialog = (message) => {
  if (process.platform !== "win32") return;
  try {
    const safe = message.replace(/'/g, "''").slice(0, 500);
    const cmd = `mshta "javascript:var s=new ActiveXObject('WScript.Shell');s.Popup('${safe}',0,'ScrapOptimisation',16);close()"`;
    exec(cmd, { windowsHide: true });
  } catch {
    /* ignore */
  }
};

const waitForBackend = async (maxAttempts = 180, intervalMs = 500) => {
  for (let i = 0; i < maxAttempts; i++) {
    if (await isBackendReady()) return;
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error(`Backend did not become ready at ${HEALTH_URL}`);
};

const openBrowser = () =>
  new Promise((resolve, reject) => {
    const cmd =
      process.platform === "win32"
        ? `start "" "${APP_URL}"`
        : process.platform === "darwin"
          ? `open "${APP_URL}"`
          : `xdg-open "${APP_URL}"`;

    exec(cmd, (err) => (err ? reject(err) : resolve()));
  });

const resolveDatabaseUrl = () => {
  if (process.env.DATABASE_URL) return process.env.DATABASE_URL;
  const dbPath = path.join(BACKEND_DIR, "prisma", "dev.db");
  return `file:${dbPath}`;
};

// ========== SOLVER FUNCTIONS (DISABLED - UNCOMMENT TO RE-ENABLE) ==========
// const isSolverReady = async () => {
//   try {
//     const res = await fetch(SOLVER_HEALTH_URL, { signal: AbortSignal.timeout(2000) });
//     if (!res.ok) return false;
//     const body = await res.json();
//     return body?.status === "UP";
//   } catch {
//     return false;
//   }
// };
//
// const waitForSolver = async (maxAttempts = 180, intervalMs = 1000) => {
//   for (let i = 0; i < maxAttempts; i++) {
//     if (await isSolverReady()) return;
//     await new Promise((r) => setTimeout(r, intervalMs));
//   }
//   throw new Error(`Solver did not become ready at ${SOLVER_HEALTH_URL}`);
// };
//
// const startSolver = async () => {
//   if (await isSolverReady()) {
//     log("Solver already running");
//     return;
//   }
//
//   const solverExe = SOLVER_EXE();
//   if (!fs.existsSync(solverExe)) {
//     log(`solver.exe not found at ${solverExe} — ML features will be unavailable`);
//     return;
//   }
//
//   fs.mkdirSync(CONFIG_DIR, { recursive: true });
//   solverLogFd = fs.openSync(SOLVER_LOG, "a");
//   log(`Starting solver: ${solverExe}`);
//
//   solverProcess = spawn(solverExe, [], {
//     cwd: APP_ROOT,
//     env: {
//       ...process.env,
//       SOLVER_HEADLESS: "1",
//       SOLVER_PORT: "5000",
//       PYTHONUTF8: "1",
//       PYTHONIOENCODING: "utf-8:replace",
//     },
//     stdio: ["ignore", solverLogFd, solverLogFd],
//     windowsHide: true,
//     detached: false,
//   });
//
//   solverProcess.on("exit", (code, signal) => {
//     log(`Solver exited (code=${code}, signal=${signal})`);
//     solverProcess = null;
//     if (solverLogFd != null) {
//       try {
//         fs.closeSync(solverLogFd);
//       } catch {
//         /* ignore */
//       }
//       solverLogFd = null;
//     }
//   });
//
//   await waitForSolver();
//   log("Solver ready");
// };
//
// const stopSolver = () => {
//   if (!solverProcess || solverProcess.killed) return;
//   const pid = solverProcess.pid;
//   log(`Stopping solver (pid=${pid})`);
//   if (process.platform === "win32") {
//     spawn("taskkill", ["/pid", String(pid), "/f", "/t"], { stdio: "ignore", windowsHide: true });
//   } else {
//     solverProcess.kill("SIGTERM");
//   }
//   solverProcess = null;
// };
// ========================================================================

const resolvePythonPath = () => {
  if (process.env.PYTHON_PATH) return process.env.PYTHON_PATH;
  const venvPython =
    process.platform === "win32"
      ? path.join(BACKEND_DIR, "src", "modules", "kalman script", "venv", "Scripts", "python.exe")
      : path.join(BACKEND_DIR, "src", "modules", "kalman script", "venv", "bin", "python");
  if (fs.existsSync(venvPython)) return venvPython;
  return process.platform === "win32" ? "python" : "python3";
};

const startBackend = () => {
  if (!fs.existsSync(BACKEND_ENTRY)) {
    throw new Error(`Backend entry not found: ${BACKEND_ENTRY}. Run: cd backend && npm run build:all`);
  }

  log(`Starting backend: ${NODE_BIN} ${BACKEND_ENTRY}`);

  backendProcess = spawn(NODE_BIN, [BACKEND_ENTRY], {
    cwd: BACKEND_DIR,
    env: {
      ...process.env,
      NODE_ENV: "production",
      PORT: APP_PORT,
      APP_ROOT,
      DATABASE_URL: resolveDatabaseUrl(),
      PYTHON_PATH: resolvePythonPath(),
      FLASK_BASE_URL: process.env.FLASK_BASE_URL ?? "http://127.0.0.1:5000",
      SOLVER_AUTO_START: "false",
      SOLVER_HEADLESS: "1",
    },
    stdio: "ignore",
    windowsHide: true,
    detached: false,
  });

  backendProcess.on("exit", (code, signal) => {
    log(`Backend exited (code=${code}, signal=${signal})`);
    backendProcess = null;
    if (!exiting) clearLock();
  });

  writeLock(backendProcess.pid);
  return backendProcess;
};

const stopBackend = () => {
  if (!backendProcess || backendProcess.killed) return;

  const pid = backendProcess.pid;
  log(`Stopping backend (pid=${pid})`);

  if (process.platform === "win32") {
    spawn("taskkill", ["/pid", String(pid), "/f", "/t"], { stdio: "ignore", windowsHide: true });
  } else {
    backendProcess.kill("SIGTERM");
  }

  backendProcess = null;
  clearLock();
};

const handleExistingInstance = async () => {
  log("Backend already running — opening browser");
  await openBrowser();
  process.exit(0);
};

const acquireOrReuse = async () => {
  if (await isBackendReady()) {
    await handleExistingInstance();
    return "reuse";
  }

  const lock = readLock();
  if (lock?.pid && isProcessAlive(lock.pid)) {
    log(`Waiting for backend started by pid ${lock.pid}`);
    await waitForBackend();
    await handleExistingInstance();
    return "reuse";
  }

  if (lock) clearLock();
  return "start";
};

const shutdown = () => {
  if (exiting) return;
  exiting = true;
  log("Launcher shutting down");
  stopBackend();
  // stopSolver();  // DISABLED - UNCOMMENT TO RE-ENABLE
  process.exit(0);
};

const main = async () => {
  fs.mkdirSync(CONFIG_DIR, { recursive: true });
  log("Launcher started");

  const action = await acquireOrReuse();
  if (action === "reuse") return;

  // ========== SOLVER STARTUP (DISABLED - UNCOMMENT TO RE-ENABLE) ==========
  log("Solver management disabled — run solver.exe separately");
  // try {
  //   await startSolver();
  // } catch (err) {
  //   log(`Solver failed to start: ${err.message}`);
  //   if (process.env.LAUNCHER_VERBOSE === "1") {
  //     console.error(err);
  //   }
  // }
  // ========================================================================

  startBackend();
  await waitForBackend();
  log("Backend ready");
  await openBrowser();
  log(`Opened ${APP_URL}`);

  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
  process.on("exit", () => {
    if (!exiting) stopBackend();
  });

  // Keep launcher alive so closing it stops the backend
  await new Promise(() => {});
};

main().catch((err) => {
  const message = `Launcher failed: ${err.message}\n\nSee ${LOG_FILE} for details.`;
  log(message);
  console.error(message);
  showErrorDialog(message);
  stopBackend();
  process.exit(1);
});
