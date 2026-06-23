/**
 * Build ScrapOptimisationSetup.exe with Inno Setup 6 (Windows only).
 *
 * Usage:
 *   npm run installer
 *   npm run installer:only   # skip npm run dist
 */
import { spawnSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const DIST = path.join(ROOT, "dist", "ScrapOptimisation");
const ISS = path.join(ROOT, "installer", "ScrapOptimisationSetup.iss");
const RELEASE = path.join(ROOT, "release");
const OUTPUT_EXE = path.join(RELEASE, "ScrapOptimisationSetup.exe");

const log = (msg) => console.log(`[installer] ${msg}`);

const findIscc = () => {
  const localAppData = process.env.LOCALAPPDATA ?? "";
  const candidates = [
    process.env.ISCC_PATH,
    "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe",
    "C:\\Program Files\\Inno Setup 6\\ISCC.exe",
    localAppData ? path.join(localAppData, "Programs", "Inno Setup 6", "ISCC.exe") : null,
  ].filter(Boolean);

  return candidates.find((p) => fs.existsSync(p)) ?? null;
};

const main = () => {
  if (process.platform !== "win32") {
    log("Inno Setup can only be run on Windows.");
    log(`ISS script ready at: ${ISS}`);
    log("On Windows: install Inno Setup 6, then run `npm run installer`");
    process.exit(0);
  }

  if (!fs.existsSync(DIST)) {
    console.error(`Release folder missing: ${DIST}\nRun: npm run dist`);
    process.exit(1);
  }

  if (!fs.existsSync(path.join(DIST, "node.exe"))) {
    console.error("node.exe missing from dist/ScrapOptimisation.\nRun: npm run dist");
    process.exit(1);
  }

  const iscc = findIscc();
  if (!iscc) {
    console.error(
      "Inno Setup compiler (ISCC.exe) not found.\n" +
        "Install from https://jrsoftware.org/isinfo.php\n" +
        "Or set ISCC_PATH to the full path of ISCC.exe"
    );
    process.exit(1);
  }

  fs.mkdirSync(RELEASE, { recursive: true });

  log(`Compiling with ${iscc}`);
  const result = spawnSync(iscc, [ISS], { cwd: path.join(ROOT, "installer"), stdio: "inherit" });

  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }

  if (fs.existsSync(OUTPUT_EXE)) {
    const sizeMb = (fs.statSync(OUTPUT_EXE).size / (1024 * 1024)).toFixed(1);
    log(`Created ${OUTPUT_EXE} (${sizeMb} MB)`);
  } else {
    console.error("Compiler finished but ScrapOptimisationSetup.exe was not found.");
    process.exit(1);
  }
};

main();