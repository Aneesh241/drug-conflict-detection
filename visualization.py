from __future__ import annotations

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


def plot_severity_distribution(conflicts_df: pd.DataFrame):
    if conflicts_df.empty:
        print("No conflicts to plot.")
        return
    plt.figure(figsize=(6, 4))
    order = ["Major", "Moderate", "Minor"]
    counts = conflicts_df["severity"].value_counts()
    data = pd.DataFrame({"severity": counts.index, "count": counts.values})
    data = data.set_index("severity").reindex(order).fillna(0).reset_index()
    sns.barplot(x="severity", y="count", data=data, order=order, palette="Reds")
    plt.title("Conflict Severity Distribution")
    plt.xlabel("Severity")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.show()
