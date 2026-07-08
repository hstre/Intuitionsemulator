import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# The kernel + CoreState come from the Joni testbed. Installed (pip) or, for local dev,
# from a sibling checkout / JONI_SRC.
for cand in (os.getenv("JONI_SRC", ""), str(ROOT.parent / "Joni" / "src"), "_joni/src"):
    if cand and (Path(cand) / "joni").is_dir():
        sys.path.insert(0, cand)
        break

# The Hermes plugin directory carries a dash (plugin naming convention); import it under a
# module alias so the tests can exercise the hook exactly as Hermes would call it.
_spec = importlib.util.spec_from_file_location(
    "hermes_plugin_joni_governor", ROOT / "hermes_plugin" / "joni-governor" / "__init__.py")
_mod = importlib.util.module_from_spec(_spec)
sys.modules["hermes_plugin_joni_governor"] = _mod
_spec.loader.exec_module(_mod)
