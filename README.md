<div align="center">
  <h1>💊 Drug Conflict Detection</h1>
  <p><strong>Multi-Agent conflict detection for prescriptions using a severity‑prioritized search.</strong></p>
  <sup><em>Educational & prototype system – NOT for clinical use.</em></sup>
</div>

---

## 1. Overview
This project detects potential conflicts between prescribed drugs and patient conditions/allergies. It uses a light Multi‑Agent System (MESA) with a priority‑based evaluation (severity first) to surface high‑impact issues early. Outputs include a console summary, CSV report, and an interactive Streamlit dashboard.

## 2. Key Features
* **Agents**: `Patient`, `Doctor`, `Pharmacist`, `RuleEngine` (simple orchestrated flow)
* **Severity Prioritization**: Higher severity conflicts processed first (Major → Moderate → Minor)
* **Rule Types**: Drug–Drug and Drug–Condition (includes allergy tokens e.g. `PenicillinAllergy`)
* **Data-Driven**: All inputs are CSV and easily extensible
* **Streamlit UI**: Filtering, manual testing, custom data import
* **CLI Mode**: Fast batch run via `main.py`
* **Extensible Knowledge Base**: Add more rules without changing code

## 3. Architecture (Textual Diagram)
```
                +------------------+
                |  rules.csv       |
                +---------+--------+
                          |
                    build_rules_kb()
                          |
                      RuleEngineAgent
                          |
  patients.csv  -->  DoctorAgent --> prescription (list[str])
        |                       \            
        v                        \           validate()
   PatientAgent  <--------------- PharmacistAgent
        |                                |
        +----------> conflict logs <-----+
                          |
                      output/conflicts.csv + Streamlit dashboard
```

## 4. Project Structure
```
drug_conflict_detection/
├── agents.py          # Agent classes (Patient, Doctor, Pharmacist, RuleEngine)
├── main.py            # CLI entry point
├── model.py           # MESA model wiring & run loop
├── utils.py           # Data loading, rule KB, priority conflict evaluation, plotting helper
├── patients.csv       # Sample patient dataset
├── drugs.csv          # Sample drug catalog
├── rules.csv          # Interaction & contraindication rules
├── output/            # Generated reports (ignored in VCS recommended)
└── requirements.txt   # Dependencies
```

## 5. Installation (Windows PowerShell)
```powershell
cd "C:\Users\anees\Desktop\SEM 3\AI\Drug Conflict Detection\drug_conflict_detection"
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
If `python` fails, try `py` instead.

## 6. Usage
### A. CLI Simulation
```powershell
python main.py
```
Outputs:
* Console summary (prescriptions & conflict counts)
* CSV report: `output/conflicts.csv`

### B. Streamlit Dashboard
```powershell
streamlit run app.py
```
Sidebar → “Run Simulation” to populate views. Explore conflicts, patients, manual testing, and import custom CSVs.

### C. Optional Plot (Matplotlib/Seaborn)
```powershell
python -c "import pandas as pd; from utils import plot_severity_distribution; df=pd.read_csv('output/conflicts.csv'); plot_severity_distribution(df)"
```

## 7. Data Formats
| File | Columns | Notes |
|------|---------|-------|
| patients.csv | `id,name,conditions,allergies` | `conditions` & `allergies` are `;` separated. `None` values ignored. |
| drugs.csv | `drug,condition,category,replacements` | `replacements` is optional alt drug suggestion. |
| rules.csv | `type,item_a,item_b,severity,recommendation,notes` | `type` ∈ {`drug-drug`,`drug-condition`} severity ∈ {Major, Moderate, Minor}. `recommendation` can have `;` separators. |

## 8. Conflict Evaluation Algorithm

**Best-First Search (A*-style)** systematically explores conflict space, prioritizing high-severity conflicts.

### Key Features
- **State Space Exploration**: SearchState tracks (prescription, conditions, detected_conflicts)
- **Heuristic Guidance**: Cumulative severity score (Major=10, Moderate=5, Minor=1)
- **Visited Tracking**: Prevents revisiting same conflict sets
- **Priority Queue**: Ensures Major conflicts surface before Minor

### Algorithm Steps
1. Initialize with empty conflict set
2. Expand neighbors by adding one detectable conflict
3. Use negative heuristic for max-heap (explore worst states first)
4. Track visited states to avoid redundant exploration
5. Return all conflicts sorted by severity descending

**Detailed documentation**: See [`docs/BFS_IMPLEMENTATION.md`](docs/BFS_IMPLEMENTATION.md)

### Previous Approach
Simple priority queue over candidate pairs (no state exploration). Upgraded to true graph search for extensibility and correctness.

## 9. Agents (Simplified Behavior)
| Agent | Role |
|-------|------|
| PatientAgent | Holds profile (conditions, allergies) & resulting prescription. |
| DoctorAgent | Naive prescriber: first matching drug per condition + forced Ibuprofen to surface demo conflicts. |
| RuleEngineAgent | Wraps knowledge base and performs conflict checks. |
| PharmacistAgent | Validates prescription via RuleEngine and logs conflicts. |

## 10. Extending
| Goal | How |
|------|-----|
| Add new rules | Append rows to `rules.csv` (ensure consistent casing & severity). |
| Support dosage/timing | Extend rule schema (e.g. add `dose`, `interval`) & modify evaluation. |
| ML risk scoring | Add a model that predicts probability of adverse event; incorporate into priority. |
| Rich agent interaction | Implement messaging or negotiation in agent `step()` functions. |
| Replace naive prescribing | Enhance `DoctorAgent.prescribe()` with decision rules or ML ranking. |

## 11. Roadmap (Suggested)
* Expand rule dataset (≥500 entries)
* Dosage & duration conflict checks
* FastAPI/REST backend for integration
* Test suite (pytest) & coverage reports
* Persistent DB layer (PostgreSQL) replacing CSVs
* Authentication for dashboard (multi‑user)
* ML‑assisted severity prediction & alternative recommendations

## 12. Troubleshooting
| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError` (mesa/streamlit) | Re-run `pip install -r requirements.txt` in the active venv. |
| Streamlit exit code 1 | Check virtual env activation; try `streamlit cache clear`; specify alternate port `--server.port 8502`. |
| Empty conflicts CSV | Sample data may produce few conflicts—add more rules or conditions. |
| Plot says dependencies missing | Install: `pip install matplotlib seaborn`. |

## 13. Testing

### Running Tests
```powershell
# All tests (17 tests)
pytest tests/ -v

# Specific test files
pytest tests/test_bfs_search.py -v           # BFS algorithm tests (7)
pytest tests/test_conflict_detection.py -v   # Integration tests (2)
pytest tests/test_doctor_prescribe.py -v     # Doctor agent tests (2)
pytest tests/test_data_models.py -v          # Data validation tests (3)
pytest tests/test_memoization.py -v          # Cache layer tests (3)
```

### Test Coverage
- ✅ **BFS Algorithm**: State space exploration, priority ordering, edge cases
- ✅ **Conflict Detection**: Multi-drug prescriptions, severity sorting
- ✅ **Data Validation**: Pydantic models, semicolon parsing, ID coercion
- ✅ **Doctor Logic**: Risk-aware prescribing, allergy checking, replacements
- ✅ **Memoization Layer**: Cache hits/misses, KB invalidation

### Adding Tests
Place new tests in `tests/` directory. Use fixtures from `conftest.py` for model setup.
## 14. Medical Disclaimer
This repository is for **educational and prototyping purposes only**. It does **not** provide medical advice and must **not** be used for real clinical decision making. Always consult qualified healthcare professionals.

## 15. Contribution Guidelines (Lightweight)
1. Create a feature branch (`git checkout -b feature/name`).
2. Keep changes focused & documented in commit messages.
3. Add/adjust tests when logic changes.
4. Open a Pull Request describing rationale & impact.

## 16. License
If you intend to open source formally, add a LICENSE file (e.g. MIT). Currently no explicit license is bundled.

---
### Quick Command Reference
```powershell
# CLI run
python main.py

# Streamlit dashboard
streamlit run app.py

# Optional plotting
python -c "import pandas as pd; from utils import plot_severity_distribution as p; p(pd.read_csv('output/conflicts.csv'))"
```

### Next Steps
Focus improvements on rule coverage, extensible schema, and test automation.

---
Feel free to open issues or request enhancements.
