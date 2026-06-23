# PyInstaller runtime hook — scipy.stats fails under frozen imports (del obj NameError).
# See: https://github.com/pyinstaller/pyinstaller/issues/7992
 
import os
import sys
 
 
def _configure_stdio_utf8() -> None:
    """Windows cp1252 consoles cannot print emoji in Kalman debug output."""
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
 
 
_configure_stdio_utf8()
 
 
def _patch_distn_infrastructure(path: str) -> None:
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as handle:
        source = handle.read()
    if "globals().pop('obj'" in source:
        return
    patched = source.replace("\ndel obj\n", "\nglobals().pop('obj', None)\n")
    if patched == source:
        return
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(patched)
 
 
if getattr(sys, "frozen", False):
    meipass = getattr(sys, "_MEIPASS", "")
    if meipass:
        _patch_distn_infrastructure(
            os.path.join(meipass, "scipy", "stats", "_distn_infrastructure.py")
        )