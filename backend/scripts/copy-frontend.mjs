import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const backendRoot = path.resolve(__dirname, "..");
const frontendDist = path.resolve(backendRoot, "..", "frontend", "dist");
const target = path.join(backendRoot, "public");

if (!fs.existsSync(path.join(frontendDist, "index.html"))) {
  console.error("Frontend build not found. Run: cd frontend && npm run build");
  process.exit(1);
}

fs.rmSync(target, { recursive: true, force: true });
fs.cpSync(frontendDist, target, { recursive: true });
console.log(`Copied ${frontendDist} -> ${target}`);
