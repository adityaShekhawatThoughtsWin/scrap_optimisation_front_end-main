/**
 * Run backend + frontend dev servers together.
 * Usage: npm run dev
 */
import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

const children = [];

const start = (name, cwd, script) => {
  const child = spawn("npm", ["run", script], {
    cwd: path.join(ROOT, cwd),
    stdio: "inherit",
    shell: true,
    env: process.env,
  });
  child.on("exit", (code) => {
    if (code && code !== 0) console.error(`${name} exited with code ${code}`);
  });
  children.push(child);
  return child;
};

const shutdown = () => {
  for (const child of children) {
    if (!child.killed) child.kill("SIGTERM");
  }
  process.exit(0);
};

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

console.log("Starting backend (:8000) and frontend (:3000)…");
start("backend", "backend", "dev");
start("frontend", "frontend", "dev");
