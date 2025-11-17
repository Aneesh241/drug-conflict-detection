# Drug Conflict Detection using MESA Agents

A Multi-Agent System (MAS) built with MESA to detect drug-drug and drug-condition conflicts using a Best-First Search (BFS) engine.

## Features
- Agents: Patient, Doctor, Pharmacist, RuleEngine
- BFS-based conflict detection prioritized by severity
- CSV inputs for patients, drugs, and rules
- Console and CSV reports
- Optional visualization of conflicts and severity distribution

## Project Structure
```
drug_conflict_detection/
├── agents.py            # Agent class definitions
├── main.py              # Entry point to run the simulation
├── model.py             # MESA model and scheduler wiring
├── utils.py             # BFS, data loaders, logging
├── visualization.py     # Optional graphs (matplotlib/seaborn)
├── patients.csv         # Example patient data
├── drugs.csv            # Example drug catalog (simple)
├── rules.csv            # Interaction rules and contraindications
├── output/              # Generated reports
└── requirements.txt
```

## Quickstart (Windows PowerShell)

1) Create and activate a Python 3.10+ environment (optional but recommended):
```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
```

2) Install dependencies:
```powershell
pip install -r requirements.txt
```

3) Run the simulation:
```powershell
python main.py
```

4) View results:
- Console summary
- CSV report at `output/conflicts.csv`

5) Optional: plot severity distribution
```powershell
python -c "import pandas as pd; from visualization import plot_severity_distribution; df=pd.read_csv('output/conflicts.csv'); plot_severity_distribution(df)"
```

## Data Contracts
- patients.csv: `id,name,conditions,allergies` where list-like fields are `;`-separated.
- drugs.csv: `drug,condition,category,replacements`
- rules.csv: `type,item_a,item_b,severity,recommendation,notes`
  - `type` in {`drug-drug`, `drug-condition`}
  - severity in {`Major`, `Moderate`, `Minor`}

## Notes
- The included example ensures at least one detectable conflict (e.g., Ibuprofen vs Hypertension).
- Extend the rules and drugs tables to reflect real-world datasets.
