import sqlite3
import json
import os
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pcb_bom.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create projects table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        width INTEGER NOT NULL,
        height INTEGER NOT NULL,
        scale_factor REAL,
        reference_box_json TEXT,
        build_volume INTEGER DEFAULT 1000,
        created_at TEXT NOT NULL
    )
    """)
    
    # Create detections table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS detections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT NOT NULL,
        designator TEXT,
        component_class TEXT NOT NULL,
        bbox_json TEXT NOT NULL,
        marking_text TEXT,
        visual_notes TEXT,
        confidence TEXT NOT NULL,
        package TEXT,
        measured_width REAL,
        measured_height REAL,
        package_status TEXT DEFAULT 'unresolved',
        manually_added INTEGER DEFAULT 0,
        is_deleted INTEGER DEFAULT 0,
        FOREIGN KEY (project_id) REFERENCES projects (id)
    )
    """)
    
    # Create sourcing_cache table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sourcing_cache (
        key TEXT PRIMARY KEY,
        manufacturer TEXT,
        part_number TEXT,
        description TEXT,
        distributor TEXT,
        distributor_part_number TEXT,
        price_breaks_json TEXT,
        datasheet_url TEXT,
        product_page_url TEXT,
        match_basis TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()

# Project helper functions
def insert_project(project_id: str, filename: str, filepath: str, width: int, height: int, created_at: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO projects (id, filename, filepath, width, height, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (project_id, filename, filepath, width, height, created_at)
    )
    conn.commit()
    conn.close()

def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        data = dict(row)
        if data["reference_box_json"]:
            data["reference_box"] = json.loads(data["reference_box_json"])
        else:
            data["reference_box"] = None
        return data
    return None

def get_all_projects() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    result = []
    for row in rows:
        data = dict(row)
        if data["reference_box_json"]:
            data["reference_box"] = json.loads(data["reference_box_json"])
        else:
            data["reference_box"] = None
        result.append(data)
    return result

def update_project_calibration(project_id: str, scale_factor: float, reference_box: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE projects SET scale_factor = ?, reference_box_json = ? WHERE id = ?",
        (scale_factor, json.dumps(reference_box), project_id)
    )
    conn.commit()
    conn.close()

def update_project_volume(project_id: str, build_volume: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE projects SET build_volume = ? WHERE id = ?",
        (build_volume, project_id)
    )
    conn.commit()
    conn.close()

# Detection helper functions
def insert_detections(project_id: str, detections: List[Dict[str, Any]]):
    conn = get_db_connection()
    cursor = conn.cursor()
    for det in detections:
        cursor.execute(
            """INSERT INTO detections 
            (project_id, designator, component_class, bbox_json, marking_text, visual_notes, confidence, package, measured_width, measured_height, package_status, manually_added, is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                project_id,
                det.get("designator"),
                det["component_class"],
                json.dumps(det["bbox"]),
                det.get("marking_text"),
                det.get("visual_notes"),
                det["confidence"],
                det.get("package"),
                det.get("measured_width"),
                det.get("measured_height"),
                det.get("package_status", "unresolved"),
                det.get("manually_added", 0),
                det.get("is_deleted", 0)
            )
        )
    conn.commit()
    conn.close()

def get_project_detections(project_id: str, include_deleted: bool = False) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if include_deleted:
        cursor.execute("SELECT * FROM detections WHERE project_id = ?", (project_id,))
    else:
        cursor.execute("SELECT * FROM detections WHERE project_id = ? AND is_deleted = 0", (project_id,))
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        data = dict(row)
        data["bbox"] = json.loads(data["bbox_json"])
        data["manually_added"] = bool(data["manually_added"])
        data["is_deleted"] = bool(data["is_deleted"])
        result.append(data)
    return result

def update_detection(detection_id: int, updates: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fields = []
    values = []
    for k, v in updates.items():
        if k == "bbox":
            fields.append("bbox_json = ?")
            values.append(json.dumps(v))
        else:
            fields.append(f"{k} = ?")
            values.append(v)
            
    values.append(detection_id)
    query = f"UPDATE detections SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(query, tuple(values))
    conn.commit()
    conn.close()

def delete_detection(detection_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE detections SET is_deleted = 1 WHERE id = ?", (detection_id,))
    conn.commit()
    conn.close()

def add_manual_detection(project_id: str, detection: Dict[str, Any]) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO detections 
        (project_id, designator, component_class, bbox_json, marking_text, visual_notes, confidence, package, measured_width, measured_height, package_status, manually_added, is_deleted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0)""",
        (
            project_id,
            detection.get("designator"),
            detection["component_class"],
            json.dumps(detection["bbox"]),
            detection.get("marking_text"),
            detection.get("visual_notes"),
            detection["confidence"],
            detection.get("package"),
            detection.get("measured_width"),
            detection.get("measured_height"),
            detection.get("package_status", "unresolved")
        )
    )
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_id

# Sourcing cache helper functions
def get_cached_sourcing(key: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sourcing_cache WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        data = dict(row)
        data["price_breaks"] = json.loads(data["price_breaks_json"])
        return data
    return None

def set_cached_sourcing(key: str, data: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT OR REPLACE INTO sourcing_cache 
        (key, manufacturer, part_number, description, distributor, distributor_part_number, price_breaks_json, datasheet_url, product_page_url, match_basis, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            key,
            data.get("manufacturer"),
            data.get("part_number"),
            data.get("description"),
            data.get("distributor"),
            data.get("distributor_part_number"),
            json.dumps(data.get("price_breaks", [])),
            data.get("datasheet_url"),
            data.get("product_page_url"),
            data["match_basis"],
            data["timestamp"]
        )
    )
    conn.commit()
    conn.close()
