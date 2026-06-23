/**
 * Step 6 — Assemble the offline Windows release folder.
 * Output: dist/ScrapOptimisation/
 *
 * Usage:
 *   npm run dist
 *   SKIP_NODE_BUNDLE=1 npm run dist   # skip bundling node.exe (faster local check)
 */
import { spawnSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "dist", "ScrapOptimisation");
const KALMAN_DIR = path.join(ROOT, "backend", "src", "modules", "kalman script");
const SOLVER_CONFIG_FILES = [
  "Scrap_Cost_Chemistry_Limits.xlsx",
  "Scrap_Chem_Input_Variables.xlsx",
  "Recom_Scrap_Input_3 1.xlsx",
  "Grade_Specifications.xlsx",
  "CHG_Mapping_Ref.xlsx",
];
const TARGET_PLATFORM = process.env.TARGET_PLATFORM ?? "win32";
const TARGET_ARCH = process.env.TARGET_ARCH ?? "x64";

const log = (msg) => console.log(`[dist] ${msg}`);
const resolveNpmInvocation = (args) => {
  if (process.env.npm_execpath) {
    return { cmd: process.execPath, args: [process.env.npm_execpath, ...args] };
  }
  if (process.platform === "win32") {
    return { cmd: path.join(path.dirname(process.execPath), "npm.cmd"), args };
  }
  return { cmd: "npm", args };
};
const run = (cmd, args, opts = {}) => {
  const { cmd: executable, args: finalArgs } =
    cmd === "npm" ? resolveNpmInvocation(args) : { cmd, args };
  const result = spawnSync(executable, finalArgs, { stdio: "inherit", ...opts });
  if (result.status !== 0) {
    throw new Error(`Command failed: ${cmd} ${args.join(" ")}`);
  }
};

const copyDir = (src, dest) => {
  if (!fs.existsSync(src)) return;
  fs.mkdirSync(dest, { recursive: true });
  fs.cpSync(src, dest, { recursive: true });
};

const copyFile = (src, dest) => {
  if (!fs.existsSync(src)) return false;
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
  return true;
};

const rmDir = (dir) => {
  if (fs.existsSync(dir)) fs.rmSync(dir, { recursive: true, force: true });
};

// Prisma CLI and other build-only packages are not needed at runtime (client is bundled in dist/server.js).
const PRODUCTION_PRUNE = ["prisma", path.join("@prisma", "dev"), path.join("@prisma", "studio-core")];

const pruneProductionModules = (backendOut) => {
  const nodeModules = path.join(backendOut, "node_modules");
  for (const pkg of PRODUCTION_PRUNE) {
    const target = path.join(nodeModules, pkg);
    if (!fs.existsSync(target)) continue;
    rmDir(target);
    log(`Pruned dev-only package: ${pkg.replace(/\\/g, "/")}`);
  }
};

const bundleLocalNodeExe = (destDir) => {
  const nodeSrc = process.env.NODE_BIN ?? process.execPath;
  if (!fs.existsSync(nodeSrc)) {
    throw new Error(`Local Node binary not found: ${nodeSrc}`);
  }

  const nodeDest = path.join(destDir, "node.exe");
  fs.copyFileSync(nodeSrc, nodeDest);
  log(`Bundled local node.exe from ${nodeSrc} (${process.version})`);
  return process.version;
};

const bundleSolverSupportFiles = (outDir) => {
  const uploadsSrc = path.join(KALMAN_DIR, "uploads");
  const uploadsDest = path.join(outDir, "uploads");
  let copied = 0;
  for (const name of SOLVER_CONFIG_FILES) {
    if (copyFile(path.join(uploadsSrc, name), path.join(uploadsDest, name))) {
      copied += 1;
      log(`Bundled solver config: uploads/${name}`);
    }
  }
  if (copied === 0) {
    log("WARNING: No solver config workbooks found — Kalman /run will fail in the installed app.");
  }
  fs.mkdirSync(path.join(outDir, "outputs"), { recursive: true });
};

const findSolverExe = () => {
  const candidates = [
    path.join(ROOT, "solver.exe"),
    path.join(ROOT, "backend", "src", "modules", "kalman script", "dist", "solver.exe"),
    process.env.SOLVER_EXE,
  ].filter(Boolean);

  return candidates.find((p) => fs.existsSync(p)) ?? null;
};

const writeProductionEnv = (configDir) => {
  const envContent = `# ScrapOptimisation — production defaults
NODE_ENV=production
PORT=3000
DATABASE_URL=file:./prisma/dev.db
FLASK_BASE_URL=http://127.0.0.1:5000
SOLVER_AUTO_START=true
LOG_LEVEL=info
`;
  fs.writeFileSync(path.join(configDir, "app.env.example"), envContent);
};

const ensureDependencies = () => {
  log("Installing frontend dependencies…");
  run("npm", ["ci"], { cwd: path.join(ROOT, "frontend") });
  log("Installing backend dependencies…");
  run("npm", ["ci"], { cwd: path.join(ROOT, "backend") });
};

const writeManifest = (outDir, nodeVersion = process.version) => {
  const manifest = {
    name: "ScrapOptimisation",
    version: JSON.parse(fs.readFileSync(path.join(ROOT, "package.json"), "utf8")).version,
    nodeVersion,
    target: `${TARGET_PLATFORM}-${TARGET_ARCH}`,
    builtAt: new Date().toISOString(),
  };
  fs.writeFileSync(path.join(outDir, "manifest.json"), JSON.stringify(manifest, null, 2));
};

const main = async () => {
  ensureDependencies();
  log("Building application…");
  run("npm", ["run", "build"], { cwd: ROOT });

  log("Preparing output directory…");
  rmDir(OUT);
  fs.mkdirSync(OUT, { recursive: true });

  const backendOut = path.join(OUT, "backend");
  const launcherOut = path.join(OUT, "launcher");
  const configOut = path.join(OUT, "config");
  const frontendOut = path.join(OUT, "frontend");
  const prismaOut = path.join(OUT, "prisma");

  // Launcher
  copyDir(path.join(ROOT, "launcher"), launcherOut);

  // Backend runtime
  copyDir(path.join(ROOT, "backend", "dist"), path.join(backendOut, "dist"));
  copyDir(path.join(ROOT, "backend", "public"), path.join(backendOut, "public"));
  copyDir(path.join(ROOT, "backend", "prisma"), path.join(backendOut, "prisma"));
  copyFile(path.join(ROOT, "backend", "package.json"), path.join(backendOut, "package.json"));
  copyFile(path.join(ROOT, "backend", "package-lock.json"), path.join(backendOut, "package-lock.json"));
  fs.mkdirSync(path.join(backendOut, "uploaded_files"), { recursive: true });

  // Mirror layout from target architecture (read-only copies for clarity in installer)
  copyDir(path.join(backendOut, "public"), frontendOut);
  copyDir(path.join(backendOut, "prisma"), prismaOut);
  if (fs.existsSync(path.join(backendOut, "prisma", "dev.db"))) {
    copyFile(
      path.join(backendOut, "prisma", "dev.db"),
      path.join(OUT, "database.db")
    );
  }

  fs.mkdirSync(configOut, { recursive: true });
  writeProductionEnv(configOut);

  // Production node_modules (Windows target for offline installer)
  if (TARGET_PLATFORM === "win32" && process.platform !== "win32") {
    log("NOTE: Building Windows bundle from a non-Windows host.");
    log("      For production installers, run `npm run dist` on Windows so native modules (better-sqlite3) match.");
  }

  rmDir(path.join(backendOut, "node_modules"));
  log(`Installing production dependencies (${TARGET_PLATFORM}-${TARGET_ARCH})…`);
  run("npm", ["ci", "--omit=dev"], {
    cwd: backendOut,
    env: {
      ...process.env,
      npm_config_platform: TARGET_PLATFORM,
      npm_config_arch: TARGET_ARCH,
      npm_config_target_platform: TARGET_PLATFORM,
      npm_config_target_arch: TARGET_ARCH,
    },
  });
  pruneProductionModules(backendOut);

  // solver.exe (PyInstaller — build on Windows: npm run build:solver --prefix backend)
  const solverSrc = findSolverExe();
  if (solverSrc) {
    copyFile(solverSrc, path.join(OUT, "solver.exe"));
    log(`Bundled solver.exe from ${solverSrc}`);
    bundleSolverSupportFiles(OUT);
  } else {
    fs.writeFileSync(
      path.join(OUT, "solver.BUILD_REQUIRED.txt"),
      [
        "solver.exe was not found.",
        "",
        "Build on Windows before packaging:",
        "  cd backend",
        "  npm run build:solver",
        "",
        "Then copy dist/solver.exe to the install root and re-run npm run dist.",
      ].join("\n")
    );
    log("solver.exe not found — see solver.BUILD_REQUIRED.txt");
  }

  // Bundled Node runtime (copy local install — set NODE_BIN to override source)
  let bundledNodeVersion = process.version;
  if (process.env.SKIP_NODE_BUNDLE === "1" || process.env.SKIP_NODE_DOWNLOAD === "1") {
    log("SKIP_NODE_BUNDLE=1 — node.exe not bundled");
  } else if (TARGET_PLATFORM === "win32") {
    bundledNodeVersion = bundleLocalNodeExe(OUT);
  } else {
    log(`Skipping node.exe bundle for platform ${TARGET_PLATFORM}`);
  }

  writeManifest(OUT, bundledNodeVersion);
  log(`Release folder ready: ${OUT}`);
};

main().catch((err) => {
  console.error(err.message);
  process.exit(1);
});