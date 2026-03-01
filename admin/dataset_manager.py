"""
Admin Dataset Manager — upload, parse, store, list, delete datasets.
Supports: CSV, XLSX/XLS, JSON, SQL (INSERT statements or SQLite dump).
Metadata is stored as JSON sidecar files alongside each dataset.
"""

import os
import json
import uuid
import sqlite3
import re
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd

DATASETS_DIR = Path(__file__).parent.parent / "admin_datasets"
DATASETS_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json", ".sql"}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _meta_path(dataset_id: str) -> Path:
    return DATASETS_DIR / f"{dataset_id}.meta.json"


def _data_path(dataset_id: str, ext: str) -> Path:
    return DATASETS_DIR / f"{dataset_id}{ext}"


def _save_meta(meta: dict):
    with open(_meta_path(meta["id"]), "w") as f:
        json.dump(meta, f, indent=2)


def _load_meta(dataset_id: str) -> dict | None:
    p = _meta_path(dataset_id)
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)


# ── Parse uploaded file → DataFrame ───────────────────────────────────────────

def _parse_sql(content: str) -> pd.DataFrame:
    """
    Parse SQL INSERT statements or a simple SQLite dump into a DataFrame.
    Falls back to loading as SQLite DB if INSERT parse yields nothing.
    """
    # Try parsing INSERT INTO ... VALUES (...) statements
    pattern = re.compile(
        r"INSERT\s+INTO\s+\S+\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)",
        re.IGNORECASE,
    )
    rows, columns = [], []
    for m in pattern.finditer(content):
        if not columns:
            columns = [c.strip().strip("`\"'") for c in m.group(1).split(",")]
        vals = [v.strip().strip("'\"") for v in m.group(2).split(",")]
        rows.append(vals)

    if rows and columns:
        return pd.DataFrame(rows, columns=columns)

    # Fallback: treat content as SQLite binary/dump → write to temp DB and read
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp.write(content.encode(errors="ignore"))
        tmp_path = tmp.name
    try:
        conn = sqlite3.connect(tmp_path)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        if tables:
            df = pd.read_sql_query(f"SELECT * FROM {tables[0][0]}", conn)
            conn.close()
            return df
        conn.close()
    except Exception:
        pass
    finally:
        os.unlink(tmp_path)

    raise ValueError("Could not parse SQL content — no INSERT statements or readable tables found.")


def parse_file(filepath: Path, ext: str) -> pd.DataFrame:
    """Parse any supported file into a pandas DataFrame."""
    if ext == ".csv":
        return pd.read_csv(filepath)
    elif ext in (".xlsx", ".xls"):
        return pd.read_excel(filepath)
    elif ext == ".json":
        return pd.read_json(filepath)
    elif ext == ".sql":
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        return _parse_sql(content)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


# ── Public API ─────────────────────────────────────────────────────────────────

def save_dataset(
    file_bytes: bytes,
    filename: str,
    company_name: str,
    period_from: str,
    period_to: str,
    description: str = "",
) -> dict:
    """
    Save an uploaded dataset file + metadata.
    Returns the metadata dict for the new dataset.
    """
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type '{ext}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    dataset_id = uuid.uuid4().hex[:12]
    data_file  = _data_path(dataset_id, ext)

    # Write raw bytes
    data_file.write_bytes(file_bytes)

    # Parse to get row/column counts
    try:
        df       = parse_file(data_file, ext)
        rows     = len(df)
        columns  = list(df.columns)
        col_count = len(columns)
        preview  = df.head(5).to_dict(orient="records")
    except Exception as e:
        data_file.unlink(missing_ok=True)
        raise ValueError(f"Failed to parse file: {e}")

    meta = {
        "id":           dataset_id,
        "company":      company_name.strip(),
        "filename":     filename,
        "ext":          ext,
        "period_from":  period_from,
        "period_to":    period_to,
        "description":  description,
        "rows":         rows,
        "columns":      columns,
        "col_count":    col_count,
        "preview":      preview,
        "uploaded_at":  datetime.now().isoformat(timespec="seconds"),
        "trained":      False,
        "training_at":  None,
        "result_id":    None,
    }
    _save_meta(meta)
    return meta


def list_datasets() -> list[dict]:
    """Return all dataset metadata sorted newest-first."""
    metas = []
    for p in DATASETS_DIR.glob("*.meta.json"):
        try:
            with open(p) as f:
                metas.append(json.load(f))
        except Exception:
            pass
    return sorted(metas, key=lambda m: m["uploaded_at"], reverse=True)


def get_dataset(dataset_id: str) -> dict | None:
    return _load_meta(dataset_id)


def delete_dataset(dataset_id: str) -> bool:
    """Delete dataset file and metadata. Returns True if deleted."""
    meta = _load_meta(dataset_id)
    if not meta:
        return False
    _data_path(dataset_id, meta["ext"]).unlink(missing_ok=True)
    _meta_path(dataset_id).unlink(missing_ok=True)
    # Also remove result if exists
    result_path = Path(__file__).parent.parent / "admin_results" / f"{dataset_id}.json"
    result_path.unlink(missing_ok=True)
    return True


def load_dataframe(dataset_id: str) -> pd.DataFrame:
    """Load a stored dataset as a DataFrame."""
    meta = _load_meta(dataset_id)
    if not meta:
        raise FileNotFoundError(f"Dataset {dataset_id} not found")
    fp = _data_path(dataset_id, meta["ext"])
    return parse_file(fp, meta["ext"])


def mark_trained(dataset_id: str, result_id: str):
    """Update metadata to mark dataset as trained."""
    meta = _load_meta(dataset_id)
    if meta:
        meta["trained"]     = True
        meta["training_at"] = datetime.now().isoformat(timespec="seconds")
        meta["result_id"]   = result_id
        _save_meta(meta)
