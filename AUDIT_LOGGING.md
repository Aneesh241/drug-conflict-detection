# Audit Logging System Documentation

## Overview
Comprehensive audit logging system tracking all events, actions, and changes within the Drug Conflict Detection System.

## Features
- **Event Tracking**: Prescriptions, conflicts, agent actions, user interactions
- **SQLite Backend**: Fast, indexed database storage
- **Web Interface**: View, filter, export through Streamlit
- **Patient History**: Complete audit trail per patient
- **Export Options**: JSON and CSV export
- **Automatic Cleanup**: Configurable retention policies

## Event Types
- `DOCTOR_PRESCRIBE` - Doctor agent prescriptions
- `PHARMACIST_REVIEW` - Pharmacist validation
- `CONFLICT_DETECTED` - Individual conflicts
- `USER_MANUAL_TEST` - Manual testing
- `SIMULATION_RUN` - System simulations
- `DATA_IMPORTED` - Data uploads

## Usage

### Basic Logging
```python
from audit_log import get_audit_logger, EventType, Severity

logger = get_audit_logger()

logger.log_event(
    event_type=EventType.SIMULATION_RUN,
    actor="user",
    severity=Severity.INFO,
    message="Simulation completed"
)
```

### Logging Prescriptions
```python
logger.log_event(
    event_type=EventType.DOCTOR_PRESCRIBE,
    actor="doctor_agent",
    patient_id="P001",
    patient_name="John Doe",
    prescription=["Aspirin", "Metformin"],
    metadata={"conditions": ["Hypertension"], "allergies": []},
    message="Prescribed 2 drugs"
)
```

### Querying Logs
```python
# Get recent events
events = logger.get_events(limit=100)

# Filter by type
conflicts = logger.get_events(event_type="conflict_detected")

# Get patient history
history = logger.get_patient_history("P001", limit=50)

# Export to JSON
logger.export_to_json("audit_export.json", limit=1000)
```

## Web Interface
1. Run: `streamlit run app.py`
2. Navigate to **Audit Logs** page
3. Use filters (event type, severity, date range)
4. View tabs: All Events, Conflicts Only, Patient History
5. Export as JSON or CSV

## Database Schema
```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    event_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    severity TEXT NOT NULL,
    actor TEXT NOT NULL,
    patient_id TEXT,
    patient_name TEXT,
    prescription TEXT,  -- JSON array
    conflicts TEXT,     -- JSON array
    metadata TEXT,      -- JSON object
    message TEXT
);
```

## Testing
```bash
pytest tests/test_audit_log.py -v  # 17 tests
```

## Best Practices
- Use appropriate severity levels (INFO, WARNING, ERROR, CRITICAL)
- Include patient IDs when available
- Log complete prescriptions for traceability
- Schedule periodic cleanup (`clear_old_logs()`)
- Export important logs for archival

## API Reference
See inline documentation in `audit_log.py` for complete API details.
