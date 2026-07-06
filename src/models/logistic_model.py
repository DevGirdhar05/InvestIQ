import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, classification_report,
    confusion_matrix, roc_auc_score
)
import matplotlib.pyplot as plt
import joblib
from pathlib import Path

MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)


def train_logistic(X_train, y_train, X_test, y_test):
    """
    Train logistic regression classifier with full evaluation.

    Why StandardScaler?
    Logistic regression uses gradient descent internally.
    If RSI is 0-100 and MACD is -5 to +5, the gradients are on
    completely different scales — training is unstable.
    StandardScaler transforms each feature to mean=0, std=1.
    Now all features are on equal footing.

    CRITICAL: fit scaler on TRAIN only, transform both train and test.
    If you fit on all data, test set statistics leak into training.
    """
    # ── Step 1: Scale features ────────────────────────────────────
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)   # fit + transform train
    X_test_scaled  = scaler.transform(X_test)         # only transform test

    # ── Step 2: Train the model ───────────────────────────────────
    model = LogisticRegression(
        C=1.0,            # regularisation strength (lower = stronger regularisation)
        max_iter=1000,    # max gradient descent steps
        random_state=42   # reproducibility
    )
    model.fit(X_train_scaled, y_train)

    # ── Step 3: Predictions ───────────────────────────────────────
    y_pred       = model.predict(X_test_scaled)         # hard labels: 0 or 1
    y_pred_proba = model.predict_proba(X_test_scaled)   # shape (N, 2)
    # column 0 = P(DOWN), column 1 = P(UP)
    y_pred_up_prob = y_pred_proba[:, 1]

    # ── Step 4: Evaluate ──────────────────────────────────────────
    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_pred_up_prob)

    print(f"\n{'═'*45}")
    print(f"  LOGISTIC REGRESSION RESULTS")
    print(f"{'═'*45}")
    print(f"  Accuracy : {acc:.4f}  ({acc:.1%})")
    print(f"  ROC-AUC  : {auc:.4f}")
    print(f"\n  Classification Report:")
    print(classification_report(y_test, y_pred,
                                target_names=["DOWN", "UP"]))

    print(f"  Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"               Predicted DOWN  Predicted UP")
    print(f"  Actual DOWN       {cm[0][0]:4d}            {cm[0][1]:4d}")
    print(f"  Actual UP         {cm[1][0]:4d}            {cm[1][1]:4d}")

    # ── Step 5: Feature importance (coefficients) ─────────────────
    print(f"\n  Feature Coefficients (sorted by importance):")
    coef_df = pd.DataFrame({
        "Feature": X_train.columns,
        "Coefficient": model.coef_[0]
    }).sort_values("Coefficient", key=abs, ascending=False)
    print(coef_df.to_string(index=False))

    # ── Step 6: Save model ────────────────────────────────────────
    joblib.dump(model,  MODELS_DIR / "logistic_model.pkl")
    joblib.dump(scaler, MODELS_DIR / "logistic_scaler.pkl")
    print(f"\n  Model saved to {MODELS_DIR}/")

    return model, scaler, {
        "accuracy": acc,
        "roc_auc": auc,
        "y_pred": y_pred,
        "y_pred_proba": y_pred_up_prob
    }