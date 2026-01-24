import pandas as pd
from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report


def main():
    ROOT = Path(__file__).resolve().parents[3]
    DATASET_PATH = ROOT / "data" / "dataset.csv"

    df = pd.read_csv(DATASET_PATH)

    df["label"] = ((df["used_shortener"] == 1) | (df["redirect_count"] >= 2)).astype(int)

    X = df.drop(columns=["analysis_id", "url", "label"])
    y = df["label"]

    n = len(df)
    if n < 5:
        raise ValueError(
            f"Need at least 5 samples to train/test split; got {n}. Run more /analyze and re-export dataset.csv")

    # If all labels are identical, stratify will fail and training is meaningless
    if df["label"].nunique() < 2:
        raise ValueError(
            "All labels are the same (all 0 or all 1). Add more diverse URLs or use a different temporary label rule.")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.3,
        random_state=42
    )

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    # Evaluate
    preds = model.predict(X_test)
    print("=== Classification report ===")
    print(classification_report(y_test, preds))


if __name__ == "__main__":
    main()
