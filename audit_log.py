"""
Audit logging module for Drug Conflict Detection System.

Tracks all events including:
- Prescription creation/modification
- Conflict detection
- Agent actions (Doctor, Pharmacist)
- User interactions
- System events
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class EventType(Enum):
    """Types of events to log."""
    PRESCRIPTION_CREATED = "prescription_created"
    PRESCRIPTION_MODIFIED = "prescription_modified"
    CONFLICT_DETECTED = "conflict_detected"
    DOCTOR_PRESCRIBE = "doctor_prescribe"
    PHARMACIST_REVIEW = "pharmacist_review"
    USER_MANUAL_TEST = "user_manual_test"
    SIMULATION_RUN = "simulation_run"
    DATA_IMPORTED = "data_imported"
    SYSTEM_ERROR = "system_error"


class Severity(Enum):
    """Event severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Represents a single audit event."""
    event_type: str
    timestamp: str
    severity: str
    actor: str  # Who/what triggered the event (doctor_agent, pharmacist_agent, user, system)
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    prescription: Optional[List[str]] = None
    conflicts: Optional[List[Dict]] = None
    metadata: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class AuditLogger:
    """SQLite-based audit logging system."""
    
    def __init__(self, db_path: Path | str = "audit_log.db"):
        """Initialize audit logger with SQLite database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """Create audit log table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                severity TEXT NOT NULL,
                actor TEXT NOT NULL,
                patient_id TEXT,
                patient_name TEXT,
                prescription TEXT,
                conflicts TEXT,
                metadata TEXT,
                message TEXT
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_log(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_event_type ON audit_log(event_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patient_id ON audit_log(patient_id)
        """)
        
        conn.commit()
        conn.close()
    
    def log_event(
        self,
        event_type: EventType | str,
        actor: str,
        severity: Severity | str = Severity.INFO,
        patient_id: Optional[str] = None,
        patient_name: Optional[str] = None,
        prescription: Optional[List[str]] = None,
        conflicts: Optional[List[Dict]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None
    ) -> int:
        """Log an audit event.
        
        Args:
            event_type: Type of event (EventType enum or string)
            actor: Who/what triggered the event
            severity: Event severity level
            patient_id: Optional patient ID
            patient_name: Optional patient name
            prescription: Optional list of prescribed drugs
            conflicts: Optional list of detected conflicts
            metadata: Optional additional metadata
            message: Optional human-readable message
            
        Returns:
            ID of inserted event
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert enums to strings
        event_type_str = event_type.value if isinstance(event_type, EventType) else event_type
        severity_str = severity.value if isinstance(severity, Severity) else severity
        
        # Serialize complex data to JSON
        prescription_json = json.dumps(prescription) if prescription else None
        conflicts_json = json.dumps(conflicts) if conflicts else None
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute("""
            INSERT INTO audit_log (
                event_type, timestamp, severity, actor,
                patient_id, patient_name, prescription,
                conflicts, metadata, message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_type_str,
            datetime.now().isoformat(),
            severity_str,
            actor,
            patient_id,
            patient_name,
            prescription_json,
            conflicts_json,
            metadata_json,
            message
        ))
        
        event_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return event_id
    
    def get_events(
        self,
        event_type: Optional[str] = None,
        patient_id: Optional[str] = None,
        actor: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Query audit events with filters.
        
        Args:
            event_type: Filter by event type
            patient_id: Filter by patient ID
            actor: Filter by actor
            start_time: Filter events after this time
            end_time: Filter events before this time
            severity: Filter by severity level
            limit: Maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        
        if patient_id:
            query += " AND patient_id = ?"
            params.append(patient_id)
        
        if actor:
            query += " AND actor = ?"
            params.append(actor)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        events = []
        for row in rows:
            event = dict(row)
            # Deserialize JSON fields
            if event['prescription']:
                event['prescription'] = json.loads(event['prescription'])
            if event['conflicts']:
                event['conflicts'] = json.loads(event['conflicts'])
            if event['metadata']:
                event['metadata'] = json.loads(event['metadata'])
            events.append(event)
        
        conn.close()
        return events
    
    def get_patient_history(self, patient_id: str, limit: int = 50) -> List[Dict]:
        """Get all events for a specific patient.
        
        Args:
            patient_id: Patient ID
            limit: Maximum number of events
            
        Returns:
            List of events for the patient
        """
        return self.get_events(patient_id=patient_id, limit=limit)
    
    def get_conflict_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get summary statistics of conflicts detected.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            Dictionary with conflict statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT 
                COUNT(*) as total_events,
                COUNT(DISTINCT patient_id) as unique_patients
            FROM audit_log
            WHERE event_type = 'conflict_detected'
        """
        params = []
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        
        summary = {
            'total_conflict_events': row[0],
            'unique_patients_affected': row[1],
            'time_range': {
                'start': start_time.isoformat() if start_time else None,
                'end': end_time.isoformat() if end_time else None
            }
        }
        
        conn.close()
        return summary
    
    def export_to_json(self, output_path: Path | str, **filters) -> int:
        """Export audit log to JSON file.
        
        Args:
            output_path: Path to output JSON file
            **filters: Filter arguments (same as get_events)
            
        Returns:
            Number of events exported
        """
        events = self.get_events(**filters)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(events, f, indent=2)
        
        return len(events)
    
    def clear_old_logs(self, days: int = 90) -> int:
        """Delete audit logs older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of events deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()
        
        cursor.execute("""
            DELETE FROM audit_log WHERE timestamp < ?
        """, (cutoff_iso,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count


# Global logger instance
_global_logger: Optional[AuditLogger] = None


def get_audit_logger(db_path: Path | str = "audit_log.db") -> AuditLogger:
    """Get or create global audit logger instance.
    
    Args:
        db_path: Path to database file
        
    Returns:
        AuditLogger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = AuditLogger(db_path)
    return _global_logger
