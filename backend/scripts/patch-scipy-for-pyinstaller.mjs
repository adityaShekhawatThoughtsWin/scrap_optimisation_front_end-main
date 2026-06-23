/**
 * Patch scipy.stats in the build venv before PyInstaller bundles it.
 * Fixes: NameError: name 'obj' is not defined in _distn_infrastructure.py
 */
import { spawnSync } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const kalmanDir = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
  "src",
  "modules",
  "kalman script"
);

export const patchScipyForPyInstaller = (pythonExe) => {
  const script = `
import pathlib
import re
import scipy

target = pathlib.Path(scipy.__file__).parent / "stats" / "_distn_infrastructure.py"
text = target.read_text(encoding="utf-8")
if "globals().pop('obj'" in text:
    print("scipy.stats already patched")
elif re.search(r"^del obj\\s*$", text, flags=re.MULTILINE):
    patched = re.sub(
        r"^del obj\\s*$",
        "globals().pop('obj', None)  # PyInstaller fix",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    target.write_text(patched, encoding="utf-8")
    print(f"Patched {target}")
else:
    print(f"No del obj patch needed in {target}")
`;

  const result = spawnSync(pythonExe, ["-c", script], {
    cwd: kalmanDir,
    stdio: "inherit",
    encoding: "utf8",
  });
  return result.status === 0;
};