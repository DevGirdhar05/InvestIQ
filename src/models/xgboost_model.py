import numpy as np
import pandas as pd
import xgboost as xgb
import shap
import joblib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
from sklearn.metrics import (
    accuracy_score, roc_auc_score,
    classification_report, confusion_matrix
)
from sklearn.model_selection import TimeSeriesSplit
from sklearn.calibration import calibration_curve


MODELS_DIR = Path(__file__).parent.parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

CHARTS_DIR = Path(__file__).parent.parent.parent / "data" / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)


class PlattCalibratedModel:
    """
    Manual Platt scaling wrapper.
    Defined at module level so joblib can pickle it correctly.
    
    Platt scaling fits a logistic regression on top of raw XGBoost
    scores to convert them into true calibrated probabilities.
    When the model says 0.68, the stock should actually rise ~68%
    of the time — making the number honest to show users.
    """
    def __init__(self, base_model, platt_model):
        self.base_model  = base_model
        self.platt_model = platt_model

    def predict_proba(self, X):
        raw = self.base_model.predict_proba(X)[:, 1].reshape(-1, 1)
        return self.platt_model.predict_proba(raw)
        # returns shape (n, 2) — column 1 is P(UP)

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] > 0.5).astype(int)


def get_xgb_params() -> dict:
    """
    XGBoost hyperparameters — centralised so they are easy to tune.

    Each parameter explained:
    n_estimators=300    : number of trees. More = better fit but slower.
                          300 is a good balance for this dataset size.
    learning_rate=0.05  : shrinks each tree's contribution.
                          Small value = cautious learning = less overfit.
    max_depth=4         : maximum depth of each tree.
                          3-5 is the sweet spot for financial data.
                          Deeper = learns more complex rules BUT also
                          memorises noise. 4 balances both.
    subsample=0.8       : each tree sees only 80% of training rows,
                          chosen randomly. Prevents overfitting —
                          same idea as Random Forest's row sampling.
    colsample_bytree=0.8: each tree sees only 80% of features.
                          Prevents any one feature from dominating.
    min_child_weight=5  : minimum number of samples required in a leaf.
                          Higher = more conservative = less overfit.
    gamma=0.1           : minimum loss reduction required to make a split.
                          Acts as structural regularisation on the tree.
    reg_alpha=0.1       : L1 regularisation on leaf weights.
                          Pushes some weights toward zero (sparse).
    reg_lambda=1.0      : L2 regularisation on leaf weights.
                          Pushes all weights toward zero (smooth).
    eval_metric=logloss : optimise log-loss (cross-entropy).
                          Appropriate for binary classification.
    """
    return {
        "n_estimators"    : 300,
        "learning_rate"   : 0.05,
        "max_depth"       : 4,
        "subsample"       : 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 5,
        "gamma"           : 0.1,
        "reg_alpha"       : 0.1,
        "reg_lambda"      : 1.0,
        "eval_metric"     : "logloss",
        "random_state"    : 42,
        "n_jobs"          : -1
    }


def train_xgboost(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test : pd.DataFrame,
    y_test : pd.Series
) -> tuple:
    """
    Train XGBoost with time-series cross-validation.

    Why no StandardScaler?
    Tree-based models split on feature values not distances.
    RSI=67 and RSI=34 are just split thresholds — absolute scale
    is irrelevant. This is fundamentally different from logistic
    regression which uses gradient descent on raw feature values.

    Returns:
        model   : trained XGBClassifier
        metrics : dict with accuracy, roc_auc, predictions
    """
    params = get_xgb_params()
    model  = xgb.XGBClassifier(**params)

    # ── Time-series cross-validation ──────────────────────────────
    # Standard k-fold CV randomly shuffles — wrong for time-series.
    # TimeSeriesSplit always trains on past, validates on future.
    #
    # With n_splits=5 on 350 training days (~70 days per fold):
    # Fold 1: train days 1-70,   validate 71-140
    # Fold 2: train days 1-140,  validate 141-210
    # Fold 3: train days 1-210,  validate 211-280
    # Fold 4: train days 1-280,  validate 281-350
    # Fold 5: train days 1-350,  validate 351-440 (if available)

    print("Running time-series cross-validation...")
    tscv       = TimeSeriesSplit(n_splits=3)
    cv_auc     = []
    cv_acc     = []

    for fold, (tr_idx, val_idx) in enumerate(tscv.split(X_train)):
        X_fold_tr  = X_train.iloc[tr_idx]
        X_fold_val = X_train.iloc[val_idx]
        y_fold_tr  = y_train.iloc[tr_idx]
        y_fold_val = y_train.iloc[val_idx]

        model.fit(
            X_fold_tr, y_fold_tr,
            eval_set=[(X_fold_val, y_fold_val)],
            verbose=False
        )

        prob = model.predict_proba(X_fold_val)[:, 1]
        pred = (prob > 0.5).astype(int)
        auc  = roc_auc_score(y_fold_val, prob)
        acc  = accuracy_score(y_fold_val, pred)

        cv_auc.append(auc)
        cv_acc.append(acc)
        print(f"  Fold {fold+1}: AUC={auc:.4f}  Acc={acc:.4f}  "
              f"(n_train={len(tr_idx)}, n_val={len(val_idx)})")

    print(f"\n  CV AUC : {np.mean(cv_auc):.4f} "
          f"± {np.std(cv_auc):.4f}")
    print(f"  CV Acc : {np.mean(cv_acc):.4f} "
          f"± {np.std(cv_acc):.4f}")

    # ── Train final model on full training set ─────────────────────
    print("\nTraining final model on full training set...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )

    # ── Evaluate on test set ───────────────────────────────────────
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    acc    = accuracy_score(y_test, y_pred)
    auc    = roc_auc_score(y_test, y_prob)

    print(f"\n{'═'*50}")
    print(f"  XGBOOST RESULTS (horizon=10)")
    print(f"{'═'*50}")
    print(f"  Accuracy  : {acc:.4f}  ({acc:.1%})")
    print(f"  ROC-AUC   : {auc:.4f}")
    print(f"\n  Classification Report:")
    print(classification_report(
        y_test, y_pred, target_names=["DOWN", "UP"]
    ))

    cm = confusion_matrix(y_test, y_pred)
    print(f"  Confusion Matrix:")
    print(f"               Predicted DOWN  Predicted UP")
    print(f"  Actual DOWN       {cm[0][0]:4d}            {cm[0][1]:4d}")
    print(f"  Actual UP         {cm[1][0]:4d}            {cm[1][1]:4d}")

    # ── Save model ─────────────────────────────────────────────────
    joblib.dump(model, MODELS_DIR / "xgboost_model.pkl")
    print(f"\n  Model saved to {MODELS_DIR}/xgboost_model.pkl")

    return model, {
        "accuracy"    : acc,
        "roc_auc"     : auc,
        "y_pred"      : y_pred,
        "y_pred_proba": y_prob,
        "cv_auc_mean" : np.mean(cv_auc),
        "cv_auc_std"  : np.std(cv_auc),
        "cv_auc_folds": cv_auc
    }


def explain_with_shap(
    model  : xgb.XGBClassifier,
    X_train: pd.DataFrame,
    X_test : pd.DataFrame
) -> tuple:
    """
    Compute SHAP values for global and local explainability.

    SHAP (SHapley Additive exPlanations) answers:
    "For this specific prediction, how much did each feature
     contribute, and in which direction?"

    Intuition — cooperative game theory:
    Imagine features as players in a game where the prediction
    is the prize. SHAP computes each player's fair share of
    the prize based on their marginal contribution across all
    possible orderings of players.

    This gives us:
    - Global: which features matter most overall
    - Local: why did the model predict X for this specific day
    """
    print("\nComputing SHAP values...")

    # TreeExplainer is optimised specifically for tree models
    # Much faster than the general KernelExplainer
    explainer   = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    # shap_values shape: (n_test_samples, n_features)
    # Positive value = pushed prediction toward UP
    # Negative value = pushed prediction toward DOWN

    # ── Plot 1: Global summary (beeswarm) ─────────────────────────
    # Each dot = one test sample
    # X position = SHAP value (contribution to prediction)
    # Colour = feature value (red=high, blue=low)
    plt.figure(figsize=(10, 7))
    shap.summary_plot(
        shap_values, X_test,
        plot_type="dot",
        show=False,
        max_display=13
    )
    plt.title("SHAP Feature Importance — XGBoost (horizon=10)",
              fontsize=12, pad=12)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "shap_summary.png",
                dpi=150, bbox_inches="tight")
    plt.close()
    print("  SHAP summary plot saved.")

    # ── Plot 2: Feature importance bar chart ──────────────────────
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    importance_df = pd.DataFrame({
        "feature"   : X_test.columns,
        "importance": mean_abs_shap
    }).sort_values("importance", ascending=True)

    fig, ax = plt.subplots(figsize=(9, 6))
    colours = ["#1565C0" if v > importance_df["importance"].median()
               else "#90CAF9"
               for v in importance_df["importance"]]
    ax.barh(importance_df["feature"],
            importance_df["importance"],
            color=colours, alpha=0.85)
    ax.set_title("Mean |SHAP Value| per Feature",
                 fontsize=12)
    ax.set_xlabel("Mean absolute SHAP value")
    ax.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "shap_importance.png",
                dpi=150, bbox_inches="tight")
    plt.close()
    print("  SHAP importance chart saved.")

    # ── Plot 3: Waterfall for most confident bullish prediction ───
    most_bullish_idx = np.argmax(shap_values.sum(axis=1))

    plt.figure(figsize=(10, 5))
    shap.waterfall_plot(
        shap.Explanation(
            values        = shap_values[most_bullish_idx],
            base_values   = explainer.expected_value,
            data          = X_test.iloc[most_bullish_idx],
            feature_names = X_test.columns.tolist()
        ),
        show=False
    )
    plt.title(
        f"Most Bullish Prediction — "
        f"{X_test.index[most_bullish_idx].date()}",
        fontsize=11
    )
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "shap_waterfall.png",
                dpi=150, bbox_inches="tight")
    plt.close()
    print("  SHAP waterfall chart saved.")

    return explainer, shap_values


def get_prediction_explanation(
    model     : xgb.XGBClassifier,
    explainer : shap.TreeExplainer,
    X_row     : pd.DataFrame
) -> dict:
    """
    Generate a structured explanation for a single prediction.
    This is exactly what the FastAPI /explain endpoint calls.

    Returns a dict the LLM layer (Week 8) converts to plain English:
    {
        "probability_up"  : 0.72,
        "probability_down": 0.28,
        "confidence"      : "high",
        "top_features"    : [
            {"feature": "rsi_normalized", "shap_value": +0.14,
             "direction": "bullish", "value": -0.28},
            ...
        ]
    }
    """
    prob_up   = float(model.predict_proba(X_row)[0, 1])
    shap_vals = explainer.shap_values(X_row)[0]

    contributions = []
    for feat, sv in zip(X_row.columns, shap_vals):
        contributions.append({
            "feature"   : feat,
            "value"     : round(float(X_row[feat].iloc[0]), 4),
            "shap_value": round(float(sv), 4),
            "direction" : "bullish" if sv > 0 else "bearish",
            "magnitude" : round(abs(float(sv)), 4)
        })

    contributions.sort(key=lambda x: x["magnitude"], reverse=True)

    return {
        "probability_up"  : round(prob_up, 4),
        "probability_down": round(1 - prob_up, 4),
        "confidence"      : (
            "high"   if abs(prob_up - 0.5) > 0.2 else
            "medium" if abs(prob_up - 0.5) > 0.1 else
            "low"
        ),
        "top_features"    : contributions[:5],
        "base_rate"       : round(float(explainer.expected_value), 4)
    }

def calibrate_model(
    model  : xgb.XGBClassifier,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test : pd.DataFrame,
    y_test : pd.Series
):
    from sklearn.linear_model import LogisticRegression

    cal_size = int(len(X_train) * 0.2)
    X_cal    = X_train.iloc[-cal_size:]
    y_cal    = y_train.iloc[-cal_size:]

    raw_cal_scores = model.predict_proba(X_cal)[:, 1].reshape(-1, 1)

    platt = LogisticRegression(random_state=42)
    platt.fit(raw_cal_scores, y_cal)

    # Use top-level class — joblib can pickle this correctly
    calibrated = PlattCalibratedModel(model, platt)

    # ── Calibration curve ─────────────────────────────────────────
    raw_probs = model.predict_proba(X_test)[:, 1]
    cal_probs = calibrated.predict_proba(X_test)[:, 1]

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.plot([0, 1], [0, 1], "k--", lw=1,
            label="Perfect calibration")

    frac_raw, mean_raw = calibration_curve(
        y_test, raw_probs, n_bins=8
    )
    frac_cal, mean_cal = calibration_curve(
        y_test, cal_probs, n_bins=8
    )

    ax.plot(mean_raw, frac_raw, "o-", color="#E53935",
            lw=1.5, label="XGBoost raw")
    ax.plot(mean_cal, frac_cal, "o-", color="#1565C0",
            lw=1.5, label="XGBoost calibrated")

    ax.set_title("Probability Calibration Curve", fontsize=12)
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Fraction of actual positives")
    ax.legend(fontsize=10)
    ax.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "calibration_curve.png",
                dpi=150, bbox_inches="tight")
    plt.close()
    print("  Calibration curve saved.")

    print(f"\n  Calibration check (first 5 test samples):")
    print(f"  {'Raw P(UP)':>10} {'Cal P(UP)':>10} {'Actual':>8}")
    print(f"  {'─'*30}")
    for i in range(min(5, len(X_test))):
        actual = "UP" if y_test.iloc[i] == 1 else "DOWN"
        print(f"  {raw_probs[i]:>10.4f} {cal_probs[i]:>10.4f} "
              f"{actual:>8}")

    joblib.dump(calibrated, MODELS_DIR / "xgboost_calibrated.pkl")
    print("\n  Calibrated model saved.")

    return calibrated