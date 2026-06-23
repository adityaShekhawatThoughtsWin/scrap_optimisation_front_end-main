/**
 * Build solver.exe with PyInstaller (Windows only).
 * Usage: node scripts/build-solver.mjs
 */
import { spawnSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { patchScipyForPyInstaller } from "./patch-scipy-for-pyinstaller.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const kalmanDir = path.resolve(__dirname, "..", "src", "modules", "kalman script");
const spec = path.join(kalmanDir, "solver.spec");
const output = path.join(kalmanDir, "dist", "solver.exe");

if (process.platform !== "win32") {
  console.log("solver.exe must be built on Windows with PyInstaller.");
  console.log(`Spec file: ${spec}`);
  process.exit(0);
}

if (!fs.existsSync(spec)) {
  console.error(`Missing spec: ${spec}`);
  process.exit(1);
}

const venvPy = path.join(kalmanDir, "venv", "Scripts", "python.exe");
const py = process.env.PYTHON_PATH ?? (fs.existsSync(venvPy) ? venvPy : "python");

if (!fs.existsSync(venvPy) && !process.env.PYTHON_PATH) {
  console.error(
    "Python venv not found.\n" +
      "  Run from repo root: npm run setup\n" +
      "  Or: cd backend/src/modules/kalman script && python -m venv venv && venv\\Scripts\\pip install -r requirements.txt"
  );
  process.exit(1);
}

const versionCheck = spawnSync(
  py,
  ["-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"],
  { encoding: "utf8" }
);
const pyVersion = versionCheck.stdout?.trim();
if (pyVersion === "3.12.0") {
  console.warn(
    "WARNING: Python 3.12.0 has a known PyInstaller/scipy bug. Prefer Python 3.12.1+ when creating the venv."
  );
}

const check = spawnSync(py, ["-c", "import pulp; import PyInstaller; import scipy; import sklearn"], {
  cwd: kalmanDir,
  stdio: "pipe",
  encoding: "utf8",
});
if (check.status !== 0) {
  console.error(
    "Python environment is missing PuLP or PyInstaller.\n" +
      `  Python: ${py}\n` +
      "  Fix: cd backend/src/modules/kalman script && venv\\Scripts\\activate && pip install -r requirements.txt"
  );
  if (check.stderr) console.error(check.stderr.trim());
  process.exit(1);
}

const requiredUploads = [
  "Scrap_Cost_Chemistry_Limits.xlsx",
  "Scrap_Chem_Input_Variables.xlsx",
  "Recom_Scrap_Input_3 1.xlsx",
];
const uploadsDir = path.join(kalmanDir, "uploads");
const missingUploads = requiredUploads.filter((name) => !fs.existsSync(path.join(uploadsDir, name)));
if (missingUploads.length > 0) {
  console.error(
    "Missing Kalman config workbooks in uploads/:\n" +
      missingUploads.map((name) => `  - ${name}`).join("\n") +
      "\nPOST /run will return 422 until these files exist and are bundled."
  );
  process.exit(1);
}

console.log(`Building solver.exe with ${py} (${pyVersion ?? "unknown version"})`);
if (!patchScipyForPyInstaller(py)) {
  process.exit(1);
}

const result = spawnSync(py, ["-m", "PyInstaller", "--clean", "solver.spec"], {
  cwd: kalmanDir,
  stdio: "inherit",
});

if (result.status !== 0) {
  process.exit(result.status ?? 1);
}

console.log(`Built ${output}`);