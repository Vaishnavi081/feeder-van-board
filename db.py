import sqlite3
import time
import os
import uuid
from typing import Dict, List, Optional
from datetime import datetime
import json

DB_PATH = 'local.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS trips (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            routeId TEXT NOT NULL,
            landmarkId TEXT NOT NULL,
            time TEXT NOT NULL,
            vehicleNumber TEXT,
            note TEXT,
            confirmCount INTEGER DEFAULT 1,
            reportCount INTEGER DEFAULT 0,
            createdAt INTEGER NOT NULL,
            lastConfirmedAt INTEGER NOT NULL,
            deviceId TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_actions (
            deviceId TEXT NOT NULL,
            action TEXT NOT NULL,
            targetId TEXT,
            timestamp INTEGER NOT NULL,
            PRIMARY KEY (deviceId, action, targetId)
        )
    ''')
    # For rate limiting submits
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_submits (
            deviceId TEXT NOT NULL,
            timestamp INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def generate_id():
    return "t_" + uuid.uuid4().hex[:12]

def today_key():
    return datetime.now().strftime("%Y-%m-%d")

# Initialize DB on import
init_db()

class LocalBackend:
    def list_trips(self, date: str):
        conn = get_db()
        rows = conn.execute("SELECT * FROM trips WHERE date = ? ORDER BY time ASC", (date,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def add_trip(self, date: str, trip: dict):
        conn = get_db()
        conn.execute('''
            INSERT INTO trips (
                id, date, routeId, landmarkId, time, vehicleNumber, note,
                confirmCount, reportCount, createdAt, lastConfirmedAt, deviceId
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trip['id'], date, trip['routeId'], trip['landmarkId'], trip['time'],
            trip.get('vehicleNumber', ''), trip.get('note', ''),
            trip.get('confirmCount', 1), trip.get('reportCount', 0),
            trip['createdAt'], trip['lastConfirmedAt'], trip['deviceId']
        ))
        conn.commit()
        conn.close()
        return trip

    def bump_confirm(self, date: str, trip_id: str):
        conn = get_db()
        now = int(time.time() * 1000)
        conn.execute('''
            UPDATE trips
            SET confirmCount = confirmCount + 1, lastConfirmedAt = ?
            WHERE id = ? AND date = ?
        ''', (now, trip_id, date))
        conn.commit()
        row = conn.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def bump_report(self, date: str, trip_id: str):
        conn = get_db()
        conn.execute('''
            UPDATE trips
            SET reportCount = reportCount + 1
            WHERE id = ? AND date = ?
        ''', (trip_id, date))
        conn.commit()
        row = conn.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

class BoardAPI:
    def __init__(self):
        self.backend = LocalBackend()
    
    def today(self):
        return today_key()

    def list_today(self):
        return self.backend.list_trips(self.today())

    def check_rate_limit(self, device_id: str):
        conn = get_db()
        one_hour_ago = int(time.time() * 1000) - (60 * 60 * 1000)
        
        # Clean up old limits
        conn.execute("DELETE FROM user_submits WHERE timestamp < ?", (one_hour_ago,))
        
        count = conn.execute(
            "SELECT COUNT(*) FROM user_submits WHERE deviceId = ?", 
            (device_id,)
        ).fetchone()[0]
        conn.close()
        
        if count >= 5:
            return {"ok": False, "reason": "You've logged 5 vans in the last hour. Please wait a bit before adding more."}
        return {"ok": True}

    def record_submit(self, device_id: str):
        conn = get_db()
        conn.execute(
            "INSERT INTO user_submits (deviceId, timestamp) VALUES (?, ?)",
            (device_id, int(time.time() * 1000))
        )
        conn.commit()
        conn.close()

    def submit_trip(self, route_id, landmark_id, trip_time, vehicle_number, note, device_id):
        trip = {
            'id': generate_id(),
            'routeId': route_id,
            'landmarkId': landmark_id,
            'time': trip_time,
            'vehicleNumber': (vehicle_number or '').upper().strip(),
            'note': (note or '').strip()[:140],
            'confirmCount': 0,  # starts at 0; submitter must confirm like everyone else
            'reportCount': 0,
            'createdAt': int(time.time() * 1000),
            'lastConfirmedAt': int(time.time() * 1000),
            'deviceId': device_id
        }
        self.backend.add_trip(self.today(), trip)
        # Do NOT auto-confirm for submitter — they can tap the button themselves
        return trip

    def delete_trip(self, device_id: str, trip_id: str):
        """Delete a trip only if the requesting device originally submitted it."""
        conn = get_db()
        row = conn.execute(
            "SELECT deviceId FROM trips WHERE id = ? AND date = ?",
            (trip_id, self.today())
        ).fetchone()
        if not row:
            conn.close()
            return {"ok": False, "reason": "Trip not found"}
        if row["deviceId"] != device_id:
            conn.close()
            return {"ok": False, "reason": "You can only delete trips you logged."}
        conn.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
        conn.execute("DELETE FROM user_actions WHERE targetId = ?", (trip_id,))
        conn.commit()
        conn.close()
        return {"ok": True}

    def have_i_confirmed(self, device_id: str, trip_id: str):
        return self._has_action(device_id, 'confirm', trip_id)

    def confirm_trip(self, device_id: str, trip_id: str):
        if self.have_i_confirmed(device_id, trip_id):
            return {"ok": False, "reason": "You've already confirmed this van."}
        
        t = self.backend.bump_confirm(self.today(), trip_id)
        if t:
            self._mark_action_by_me(device_id, 'confirm', trip_id)
            return {"ok": True, "trip": t}
        return {"ok": False, "reason": "Trip not found"}

    def have_i_reported(self, device_id: str, trip_id: str):
        return self._has_action(device_id, 'report', trip_id)

    def report_trip(self, device_id: str, trip_id: str):
        if self.have_i_reported(device_id, trip_id):
            return {"ok": False, "reason": "You've already reported this listing."}
        
        t = self.backend.bump_report(self.today(), trip_id)
        if t:
            self._mark_action_by_me(device_id, 'report', trip_id)
            return {"ok": True, "trip": t}
        return {"ok": False, "reason": "Trip not found"}

    def find_likely_duplicate(self, route_id, landmark_id, trip_time):
        trips = self.list_today()
        h, m = map(int, trip_time.split(':'))
        minutes = h * 60 + m
        
        for t in trips:
            if t['routeId'] != route_id or t['landmarkId'] != landmark_id:
                continue
            th, tm = map(int, t['time'].split(':'))
            t_minutes = th * 60 + tm
            if abs(t_minutes - minutes) <= 20:
                return t
        return None

    def _has_action(self, device_id: str, action: str, target_id: str):
        conn = get_db()
        row = conn.execute(
            "SELECT 1 FROM user_actions WHERE deviceId = ? AND action = ? AND targetId = ?",
            (device_id, action, target_id)
        ).fetchone()
        conn.close()
        return bool(row)

    def _mark_action_by_me(self, device_id: str, action: str, target_id: str):
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO user_actions (deviceId, action, targetId, timestamp) VALUES (?, ?, ?, ?)",
                (device_id, action, target_id, int(time.time() * 1000))
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass # Already exists
        finally:
            conn.close()

Board = BoardAPI()
