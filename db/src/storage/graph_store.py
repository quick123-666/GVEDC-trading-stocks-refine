import sqlite3
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

class GraphStore:
    def __init__(self, db_path: str = "db/gvedc.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wings (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                color TEXT,
                icon TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id TEXT PRIMARY KEY,
                wing_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (wing_id) REFERENCES wings(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS halls (
                id TEXT PRIMARY KEY,
                room_id TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT CHECK(type IN ('facts', 'events', 'discoveries', 'preferences')),
                FOREIGN KEY (room_id) REFERENCES rooms(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tunnels (
                id TEXT PRIMARY KEY,
                source_hall_id TEXT NOT NULL,
                target_hall_id TEXT NOT NULL,
                relation_type TEXT,
                weight REAL DEFAULT 1.0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drawers (
                id TEXT PRIMARY KEY,
                hall_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_hash TEXT,
                file_size INTEGER,
                mime_type TEXT
            )
        """)

        conn.commit()
        conn.close()

    def create_wing(self, wing_id: str, name: str, description: str = "", color: str = "", icon: str = "") -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO wings (id, name, description, color, icon) VALUES (?, ?, ?, ?, ?)",
                (wing_id, name, description, color, icon)
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def get_wings(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM wings")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def create_room(self, room_id: str, wing_id: str, name: str, description: str = "") -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO rooms (id, wing_id, name, description) VALUES (?, ?, ?, ?)",
                (room_id, wing_id, name, description)
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def get_rooms(self, wing_id: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        if wing_id:
            cursor.execute("SELECT * FROM rooms WHERE wing_id = ?", (wing_id,))
        else:
            cursor.execute("SELECT * FROM rooms")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def create_hall(self, hall_id: str, room_id: str, name: str, hall_type: str = "facts") -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO halls (id, room_id, name, type) VALUES (?, ?, ?, ?)",
                (hall_id, room_id, name, hall_type)
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def get_halls(self, room_id: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        if room_id:
            cursor.execute("SELECT * FROM halls WHERE room_id = ?", (room_id,))
        else:
            cursor.execute("SELECT * FROM halls")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def add_tunnel(self, tunnel_id: str, source_hall_id: str, target_hall_id: str, relation_type: str = "", weight: float = 1.0) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tunnels (id, source_hall_id, target_hall_id, relation_type, weight) VALUES (?, ?, ?, ?, ?)",
                (tunnel_id, source_hall_id, target_hall_id, relation_type, weight)
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def get_tunnels(self, hall_id: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        if hall_id:
            cursor.execute("SELECT * FROM tunnels WHERE source_hall_id = ? OR target_hall_id = ?", (hall_id, hall_id))
        else:
            cursor.execute("SELECT * FROM tunnels")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def get_hierarchy(self) -> Dict[str, Any]:
        wings = self.get_wings()
        for wing in wings:
            wing['rooms'] = self.get_rooms(wing['id'])
            for room in wing['rooms']:
                room['halls'] = self.get_halls(room['id'])
        return {'wings': wings}
