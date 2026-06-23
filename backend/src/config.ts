import path from "path";
import { fileURLToPath } from "url";
import "dotenv/config";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const backendRoot = path.resolve(__dirname, "..");

const nodeEnv = process.env.NODE_ENV ?? "development";
const isProduction = nodeEnv === "production";

export const config = {
  backendRoot,
  FLASK_BASE_URL: process.env.FLASK_BASE_URL ?? "http://127.0.0.1:5000",
  PORT: Number(process.env.PORT) || 8000,
  NODE_ENV: nodeEnv,
  isProduction,
  LOG_LEVEL: process.env.LOG_LEVEL ?? "info",
  /** Built React assets copied from frontend/dist (see scripts/copy-frontend.mjs) */
  STATIC_DIR: path.join(backendRoot, "public"),
  /** Install root (parent of backend/ in packaged layout) */
  APP_ROOT: process.env.APP_ROOT ?? path.resolve(backendRoot, ".."),
  SOLVER_PATH: process.env.SOLVER_PATH ?? "",
  PYTHON_PATH: process.env.PYTHON_PATH ?? (process.platform === "win32" ? "python" : "python3"),
  KALMAN_DIR: path.join(backendRoot, "src", "modules", "kalman script"),
  /**
   * Auto-start Flask/solver when not already running.
   * Default: on in production, off in development (manual `python app.py` still works).
   */
  SOLVER_AUTO_START:
    process.env.SOLVER_AUTO_START !== undefined
      ? process.env.SOLVER_AUTO_START === "true"
      : isProduction,
};