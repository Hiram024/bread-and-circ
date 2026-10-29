"""Runtime smoke executed with the fresh app-only environment, not project .venv."""
from pathlib import Path
import importlib.metadata
import io
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
from src import dashboard_api as api
from src.product_contract import load_active

package = load_active(ROOT)
assert package["artifact"]["k"] == 4
health = api.health()
assert health["perfiles"] == 4 and health["observaciones"] == 8541
query = api.observations(limit=3, offset=0)
assert len(query["items"]) == 3
sample = pd.read_csv(io.BytesIO(api.template().body))
classified = api.classify_dataframe(sample)
assert classified.package_version.eq("ccpc-2009-2024-k4-v1").all()
print(json.dumps(dict(health=health, queried_rows=len(query["items"]),
                      classified_profile=int(classified.perfil_id.iloc[0]),
                      versions={p: importlib.metadata.version(p) for p in [
                          "numpy", "pandas", "scipy", "scikit-learn", "joblib", "threadpoolctl", "fastapi", "reportlab"]}),
                 ensure_ascii=False))
