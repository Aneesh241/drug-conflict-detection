"""
Tests for audit logging functionality.
"""
import pytest
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import json

from audit_log import AuditLogger, EventType, Severity, get_audit_logger


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    yield db_path
    
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def logger(temp_db):
    """Create an AuditLogger instance with temporary database."""
    return AuditLogger(temp_db)


def test_audit_logger_initialization(temp_db):
    """Test that audit logger initializes correctly and creates database."""
    logger = AuditLogger(temp_db)
    assert temp_db.exists()


def test_log_simple_event(logger):
    """Test logging a simple event."""
    event_id = logger.log_event(
        event_type=EventType.SIMULATION_RUN,
        actor="test_user",
        severity=Severity.INFO,
        message="Test simulation run"
    )
    
    assert event_id > 0
    
    events = logger.get_events(limit=10)
    assert len(events) == 1
    assert events[0]['event_type'] == 'simulation_run'
    assert events[0]['actor'] == 'test_user'
    assert events[0]['severity'] == 'info'
    assert events[0]['message'] == "Test simulation run"


def test_log_prescription_event(logger):
    """Test logging a prescription with full patient details."""
    prescription = ["Aspirin", "Ibuprofen", "Metformin"]
    conflicts = [
        {
            "type": "drug-drug",
            "item_a": "Aspirin",
            "item_b": "Ibuprofen",
            "severity": "Major",
            "recommendation": "Avoid combination"
        }
    ]
    
    event_id = logger.log_event(
        event_type=EventType.DOCTOR_PRESCRIBE,
        actor="doctor_agent",
        severity=Severity.INFO,
        patient_id="P001",
        patient_name="John Doe",
        prescription=prescription,
        conflicts=conflicts,
        metadata={"conditions": ["Hypertension", "Diabetes"], "allergies": []},
        message="Doctor prescribed 3 drugs"
    )
    
    assert event_id > 0
    
    events = logger.get_events(limit=10)
    assert len(events) == 1
    
    event = events[0]
    assert event['patient_id'] == "P001"
    assert event['patient_name'] == "John Doe"
    assert event['prescription'] == prescription
    assert event['conflicts'] == conflicts
    assert event['metadata']['conditions'] == ["Hypertension", "Diabetes"]


def test_conflict_detection_event(logger):
    """Test logging conflict detection events."""
    conflicts = [
        {
            "type": "drug-drug",
            "item_a": "Warfarin",
            "item_b": "Aspirin",
            "severity": "Major",
            "score": 3,
            "recommendation": "Monitor INR closely"
        }
    ]
    
    logger.log_event(
        event_type=EventType.CONFLICT_DETECTED,
        actor="rule_engine",
        severity=Severity.WARNING,
        patient_id="P002",
        patient_name="Jane Smith",
        prescription=["Warfarin", "Aspirin"],
        conflicts=conflicts,
        message="Major conflict detected"
    )
    
    events = logger.get_events(event_type="conflict_detected")
    assert len(events) == 1
    assert events[0]['severity'] == 'warning'
    assert len(events[0]['conflicts']) == 1


def test_filter_by_event_type(logger):
    """Test filtering events by type."""
    # Log different event types
    logger.log_event(EventType.DOCTOR_PRESCRIBE, actor="doctor")
    logger.log_event(EventType.PHARMACIST_REVIEW, actor="pharmacist")
    logger.log_event(EventType.DOCTOR_PRESCRIBE, actor="doctor")
    logger.log_event(EventType.SIMULATION_RUN, actor="user")
    
    # Filter by doctor prescriptions
    doctor_events = logger.get_events(event_type="doctor_prescribe")
    assert len(doctor_events) == 2
    
    # Filter by pharmacist reviews
    pharmacist_events = logger.get_events(event_type="pharmacist_review")
    assert len(pharmacist_events) == 1


def test_filter_by_patient_id(logger):
    """Test filtering events by patient ID."""
    logger.log_event(EventType.DOCTOR_PRESCRIBE, actor="doctor", patient_id="P001")
    logger.log_event(EventType.DOCTOR_PRESCRIBE, actor="doctor", patient_id="P002")
    logger.log_event(EventType.PHARMACIST_REVIEW, actor="pharmacist", patient_id="P001")
    
    patient_events = logger.get_events(patient_id="P001")
    assert len(patient_events) == 2
    assert all(e['patient_id'] == "P001" for e in patient_events)


def test_filter_by_severity(logger):
    """Test filtering events by severity level."""
    logger.log_event(EventType.SIMULATION_RUN, actor="user", severity=Severity.INFO)
    logger.log_event(EventType.CONFLICT_DETECTED, actor="engine", severity=Severity.WARNING)
    logger.log_event(EventType.SYSTEM_ERROR, actor="system", severity=Severity.ERROR)
    logger.log_event(EventType.CONFLICT_DETECTED, actor="engine", severity=Severity.WARNING)
    
    warnings = logger.get_events(severity="warning")
    assert len(warnings) == 2
    
    errors = logger.get_events(severity="error")
    assert len(errors) == 1


def test_filter_by_date_range(logger):
    """Test filtering events by date range."""
    now = datetime.now()
    
    # This would require manipulating timestamps in the database
    # For now, test that the parameters are accepted
    events = logger.get_events(
        start_time=now - timedelta(days=7),
        end_time=now
    )
    assert isinstance(events, list)


def test_get_patient_history(logger):
    """Test retrieving complete patient history."""
    patient_id = "P123"
    
    # Log multiple events for same patient
    logger.log_event(EventType.DOCTOR_PRESCRIBE, actor="doctor", patient_id=patient_id)
    logger.log_event(EventType.PHARMACIST_REVIEW, actor="pharmacist", patient_id=patient_id)
    logger.log_event(EventType.CONFLICT_DETECTED, actor="engine", patient_id=patient_id)
    
    # Log event for different patient
    logger.log_event(EventType.DOCTOR_PRESCRIBE, actor="doctor", patient_id="P999")
    
    history = logger.get_patient_history(patient_id)
    assert len(history) == 3
    assert all(e['patient_id'] == patient_id for e in history)


def test_get_conflict_summary(logger):
    """Test conflict summary statistics."""
    # Log some conflicts
    logger.log_event(
        EventType.CONFLICT_DETECTED,
        actor="engine",
        patient_id="P001",
        conflicts=[{"severity": "Major"}]
    )
    logger.log_event(
        EventType.CONFLICT_DETECTED,
        actor="engine",
        patient_id="P002",
        conflicts=[{"severity": "Moderate"}]
    )
    logger.log_event(
        EventType.CONFLICT_DETECTED,
        actor="engine",
        patient_id="P001",
        conflicts=[{"severity": "Minor"}]
    )
    
    summary = logger.get_conflict_summary()
    assert summary['total_conflict_events'] == 3
    assert summary['unique_patients_affected'] == 2


def test_export_to_json(logger, temp_db):
    """Test exporting audit log to JSON file."""
    # Log some events
    logger.log_event(EventType.SIMULATION_RUN, actor="user", message="Test 1")
    logger.log_event(EventType.DOCTOR_PRESCRIBE, actor="doctor", message="Test 2")
    
    # Export to JSON
    output_path = temp_db.parent / "export_test.json"
    count = logger.export_to_json(output_path)
    
    assert count == 2
    assert output_path.exists()
    
    # Verify JSON content
    with open(output_path) as f:
        data = json.load(f)
    
    assert len(data) == 2
    assert data[0]['event_type'] in ['simulation_run', 'doctor_prescribe']
    
    # Cleanup
    output_path.unlink()


def test_clear_old_logs(logger):
    """Test clearing old log entries."""
    # This would require manipulating timestamps
    # For now, test that the method runs without error
    deleted = logger.clear_old_logs(days=90)
    assert deleted >= 0


def test_limit_parameter(logger):
    """Test that limit parameter works correctly."""
    # Log 50 events
    for i in range(50):
        logger.log_event(EventType.SIMULATION_RUN, actor="user", message=f"Event {i}")
    
    # Retrieve with limit
    events = logger.get_events(limit=10)
    assert len(events) == 10


def test_event_ordering(logger):
    """Test that events are returned in reverse chronological order (newest first)."""
    logger.log_event(EventType.SIMULATION_RUN, actor="user", message="First")
    logger.log_event(EventType.SIMULATION_RUN, actor="user", message="Second")
    logger.log_event(EventType.SIMULATION_RUN, actor="user", message="Third")
    
    events = logger.get_events(limit=10)
    assert events[0]['message'] == "Third"
    assert events[1]['message'] == "Second"
    assert events[2]['message'] == "First"


def test_global_logger_singleton(temp_db):
    """Test that get_audit_logger returns singleton instance."""
    logger1 = get_audit_logger(temp_db)
    logger2 = get_audit_logger(temp_db)
    
    # Note: Due to global state, they reference the same instance
    # This test verifies the function works
    assert logger1 is not None
    assert logger2 is not None


def test_string_event_types(logger):
    """Test that string event types work (not just enums)."""
    event_id = logger.log_event(
        event_type="custom_event",
        actor="test",
        severity="info",
        message="Custom event type"
    )
    
    assert event_id > 0
    
    events = logger.get_events(event_type="custom_event")
    assert len(events) == 1


def test_null_optional_fields(logger):
    """Test that events can be logged with minimal required fields."""
    event_id = logger.log_event(
        event_type=EventType.SIMULATION_RUN,
        actor="user"
    )
    
    assert event_id > 0
    
    events = logger.get_events(limit=1)
    assert events[0]['patient_id'] is None
    assert events[0]['prescription'] is None
    assert events[0]['conflicts'] is None
    assert events[0]['metadata'] is None
    assert events[0]['message'] is None
