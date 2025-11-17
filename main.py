from __future__ import annotations

from pathlib import Path

from model import HealthcareModel
from utils import logger


def main():
    base_dir = Path(__file__).parent
    data_dir = base_dir
    output_dir = base_dir / "output"

    model = HealthcareModel(data_dir=data_dir)
    model.run(steps=1)

    # Save results
    out_csv = output_dir / "conflicts.csv"
    model.save_conflicts_csv(out_csv)

    # Console summary
    df = model.conflicts_dataframe()
    total_conflicts = len(df)
    by_sev = df["severity"].value_counts().to_dict() if total_conflicts else {}

    print("\n=== Simulation Summary ===")
    print(f"Total prescriptions: {model.total_prescriptions}")
    print(f"Conflicts detected: {total_conflicts}")
    if total_conflicts:
        print("By severity:")
        for sev in ["Major", "Moderate", "Minor"]:
            print(f"  - {sev}: {by_sev.get(sev, 0)}")
        print(f"\nReport saved to: {out_csv}")
    else:
        print("No conflicts found.")


if __name__ == "__main__":
    main()
