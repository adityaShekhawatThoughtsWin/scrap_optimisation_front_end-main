/**
 * Restore node_modules + Python venv after a clean zip/checkout.
 * Usage: npm run setup
 */
import { spawnSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const KALMAN_DIR = path.join(ROOT, "backend", "src", "modules", "kalman script");
const VENV_PY = path.join(KALMAN_DIR, "venv", "Scripts", "python.exe");

const resolveNpm = (args) => {
  if (process.env.npm_execpath) {
    return { cmd: process.execPath, args: [process.env.npm_execpath, ...args] };
  }
  if (process.platform === "win32") {
    return { cmd: path.join(path.dirname(process.execPath), "npm.cmd"), args };
  }
  return { cmd: "npm", args };
};

const run = (label, cmd, args, opts = {}) => {
  console.log(`\n[setup] ${label}…`);
  const result = spawnSync(cmd, args, { stdio: "inherit", ...opts });
  if (result.status !== 0) {
    throw new Error(`${label} failed`);
  }
};

const runNpm = (label, args, opts = {}) => {
  const npm = resolveNpm(args);
  run(label, npm.cmd, npm.args, opts);
};

const main = () => {
  runNpm("frontend npm ci", ["ci"], { cwd: path.join(ROOT, "frontend") });
  runNpm("backend npm ci", ["ci"], { cwd: path.join(ROOT, "backend") });

  if (!fs.existsSync(VENV_PY)) {
    run("create Python venv", "python", ["-m", "venv", "venv"], { cwd: KALMAN_DIR });
  }

  run("pip install Python deps", VENV_PY, [
    "-m",
    "pip",
    "install",
    "--upgrade",
    "pip",
    "wheel",
    "setuptools",
  ]);
  run("pip install requirements", VENV_PY, [
    "-m",
    "pip",
    "install",
    "-r",
    "requirements.txt",
  ], { cwd: KALMAN_DIR });

  const version = spawnSync(VENV_PY, ["--version"], { encoding: "utf8" });
  console.log(`\n[setup] Done. ${version.stdout?.trim() ?? "Python venv ready"}`);
  console.log("[setup] Next: npm run build:solver --prefix backend");
  console.log("[setup] Then:  npm run installer");
};

main();