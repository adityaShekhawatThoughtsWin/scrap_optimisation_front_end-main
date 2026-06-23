import { spawn, type ChildProcess } from "child_process";
import fs from "fs";
import path from "path";
import axios from "axios";
import { config } from "../config";
import { logger } from "./logger";

let solverProcess: ChildProcess | null = null;
let shuttingDown = false;

const solverPort = (): string => {
  try {
    const url = new URL(config.FLASK_BASE_URL);
    if (url.port) return url.port;
    return url.protocol === "https:" ? "443" : "80";
  } catch {
    return "5000";
  }
};

type SolverLaunch = {
  command: string;
  args: string[];
  cwd: string;
  mode: "executable" | "python";
};

const resolveSolverExe = (): string => {
  if (config.SOLVER_PATH) return config.SOLVER_PATH;
  return path.join(config.APP_ROOT, "solver.exe");
};

const resolveSolverLaunch = (): SolverLaunch => {
  const solverExe = resolveSolverExe();

  if (fs.existsSync(solverExe)) {
    return {
      command: solverExe,
      args: [],
      cwd: path.dirname(solverExe),
      mode: "executable",
    };
  }

  if (config.isProduction && process.platform === "win32") {
    throw new Error(`Solver executable not found: ${solverExe}`);
  }

  return {
    command: config.PYTHON_PATH,
    args: [path.join(config.KALMAN_DIR, "app.py")],
    cwd: config.KALMAN_DIR,
    mode: "python",
  };
};

export const isSolverReachable = async (): Promise<boolean> => {
  try {
    const base = config.FLASK_BASE_URL.replace(/\/$/, "");
    const res = await axios.get(`${base}/health`, {
      timeout: 2000,
      validateStatus: (status) => status < 500,
    });
    return res.status === 200;
  } catch {
    return false;
  }
};

const waitForSolver = async (maxAttempts = 90, intervalMs = 1000): Promise<void> => {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    if (await isSolverReachable()) {
      logger.info({ attempt }, "Solver is ready");
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  throw new Error("Solver did not become ready in time");
};

export const startSolver = async (): Promise<void> => {
  if (solverProcess) return;

  const launch = resolveSolverLaunch();

  if (launch.mode === "executable" && !fs.existsSync(launch.command)) {
    throw new Error(`Solver executable not found: ${launch.command}`);
  }

  if (launch.mode === "python") {
    const appPy = launch.args[0];
    if (!fs.existsSync(appPy)) {
      throw new Error(`Python solver entry not found: ${appPy}`);
    }
  }

  logger.info(
    { command: launch.command, args: launch.args, cwd: launch.cwd, mode: launch.mode },
    "Starting solver process"
  );

  solverProcess = spawn(launch.command, launch.args, {
    cwd: launch.cwd,
    env: {
      ...process.env,
      SOLVER_HEADLESS: "1",
      SOLVER_PORT: solverPort(),
    },
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true,
  });

  solverProcess.stdout?.on("data", (chunk: Buffer) => {
    logger.debug({ solver: chunk.toString().trim() }, "solver stdout");
  });

  solverProcess.stderr?.on("data", (chunk: Buffer) => {
    logger.warn({ solver: chunk.toString().trim() }, "solver stderr");
  });

  solverProcess.on("exit", (code, signal) => {
    logger.info({ code, signal }, "Solver process exited");
    solverProcess = null;
    if (!shuttingDown && config.SOLVER_AUTO_START) {
      logger.error("Solver exited unexpectedly");
    }
  });

  await waitForSolver();
};

export const ensureSolverRunning = async (): Promise<void> => {
  if (await isSolverReachable()) {
    logger.info("Solver already running");
    return;
  }

  if (!config.SOLVER_AUTO_START) {
    logger.warn(
      "Solver is not running. Start it manually (python app.py) or set SOLVER_AUTO_START=true"
    );
    return;
  }

  await startSolver();
};

export const stopSolver = (): void => {
  if (!solverProcess || solverProcess.killed) return;

  shuttingDown = true;
  const proc = solverProcess;

  if (process.platform === "win32") {
    spawn("taskkill", ["/pid", String(proc.pid), "/f", "/t"], { stdio: "ignore" });
  } else {
    proc.kill("SIGTERM");
  }

  solverProcess = null;
};

const registerShutdownHooks = (): void => {
  const onExit = () => {
    stopSolver();
  };

  process.once("SIGINT", onExit);
  process.once("SIGTERM", onExit);
  process.once("exit", onExit);
};

registerShutdownHooks();
