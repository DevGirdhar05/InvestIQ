
import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
from sklearn.metrics import roc_auc_score, accuracy_score
from sklearn.linear_model import LogisticRegression

CHARTS_DIR = Path(__file__).parent.parent.parent / "data" / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

MODELS_DIR = Path(__file__).parent.parent.parent / "models"


def walk_forward_backtest(
    X                 : pd.DataFrame,
    y                 : pd.Series,
    initial_train_size: float = 0.5,
    step_size         : int   = 21,
    min_train_size    : int   = 150
) -> pd.DataFrame:
    """
    Walk-forward backtest — the honest way to evaluate a time-series model.

    Instead of one fixed train/test split, this slides a window forward:
        Window 1: Train on first 50%, test on next 21 days
        Window 2: Train on first 50% + 21 days, test on next 21 days
        Window 3: ...and so on

    step_size=21 means roughly monthly re-evaluation.
    Each window always trains on PAST data only — no future leakage.

    Why 21 days?
    21 trading days ≈ 1 calendar month.
    Monthly evaluation is the standard for systematic strategies.
    Too small (5 days) = too noisy. Too large (60 days) = too few windows.

    Args:
        X                  : Feature DataFrame with DatetimeIndex
        y                  : Label Series (0/1)
        initial_train_size : fraction of data for first training window
        step_size          : days to advance each window
        min_train_size     : minimum training samples before we start

    Returns:
        DataFrame with one row per test window:
        window, test_start, test_end, accuracy, roc_auc
        Plus attrs: all_dates, all_probs, all_actuals, all_preds
    """
    from src.models.xgboost_model import get_xgb_params

    n_samples  = len(X)
    train_end  = int(n_samples * initial_train_size)

    results      = []
    all_dates    = []
    all_probs    = []
    all_actuals  = []
    all_preds    = []

    window_num = 0

    for test_start in range(train_end, n_samples, step_size):
        test_end = min(test_start + step_size, n_samples)

        if test_end <= test_start:
            break

        X_train_wf = X.iloc[:test_start]
        y_train_wf = y.iloc[:test_start]
        X_test_wf  = X.iloc[test_start:test_end]
        y_test_wf  = y.iloc[test_start:test_end]

        if len(X_train_wf) < min_train_size:
            continue
        if len(X_test_wf) == 0:
            break

        # Train fresh model on everything available up to test_start
        # This is exactly what you do in production — monthly retrain
        model = xgb.XGBClassifier(**get_xgb_params())
        model.fit(
            X_train_wf, y_train_wf,
            eval_set=[(X_test_wf, y_test_wf)],
            verbose=False
        )

        y_prob = model.predict_proba(X_test_wf)[:, 1]
        y_pred = (y_prob > 0.5).astype(int)

        # Need at least 2 classes in test window for AUC
        if len(np.unique(y_test_wf)) < 2:
            auc = 0.5
        else:
            auc = roc_auc_score(y_test_wf, y_prob)

        acc = accuracy_score(y_test_wf, y_pred)

        results.append({
            "window"    : window_num,
            "train_size": len(X_train_wf),
            "test_start": X_test_wf.index[0].date(),
            "test_end"  : X_test_wf.index[-1].date(),
            "test_size" : len(X_test_wf),
            "accuracy"  : round(acc, 4),
            "roc_auc"   : round(auc, 4),
            "up_rate"   : round(float(y_test_wf.mean()), 4)
        })

        all_dates.extend(X_test_wf.index.tolist())
        all_probs.extend(y_prob.tolist())
        all_actuals.extend(y_test_wf.tolist())
        all_preds.extend(y_pred.tolist())

        window_num += 1
        print(f"  Window {window_num:02d}: "
              f"{X_test_wf.index[0].date()} → "
              f"{X_test_wf.index[-1].date()} | "
              f"AUC={auc:.3f} | Acc={acc:.3f} | "
              f"n_train={len(X_train_wf)}")

    results_df = pd.DataFrame(results)

    # Store aggregate predictions as DataFrame attrs for later use
    results_df.attrs["all_dates"]   = all_dates
    results_df.attrs["all_probs"]   = all_probs
    results_df.attrs["all_actuals"] = all_actuals
    results_df.attrs["all_preds"]   = all_preds

    return results_df


def identify_market_regime(prices: pd.Series) -> pd.Series:
    """
    Label each day as bull or bear based on SMA200.

    Price above SMA200 = bull market (long-term uptrend)
    Price below SMA200 = bear market (long-term downtrend)

    SMA200 is the industry-standard regime filter used by
    institutional traders worldwide. Simple, interpretable,
    and surprisingly effective at separating conditions.
    """
    sma200 = prices.rolling(window=200).mean()
    regime = pd.Series(
        np.where(prices > sma200, "bull", "bear"),
        index=prices.index
    )
    regime.iloc[:200] = "unknown"
    return regime


def regime_performance(
    results_df: pd.DataFrame,
    prices    : pd.Series
) -> dict:
    """
    Split walk-forward predictions by market regime.
    Answers: does the model work in both bull and bear markets?

    A model that only works in bull markets is dangerous —
    it gives confident wrong signals during crashes, exactly
    when users need correct guidance most.
    """
    all_dates   = results_df.attrs["all_dates"]
    all_probs   = results_df.attrs["all_probs"]
    all_actuals = results_df.attrs["all_actuals"]
    all_preds   = results_df.attrs["all_preds"]

    pred_df = pd.DataFrame({
        "prob"  : all_probs,
        "actual": all_actuals,
        "pred"  : all_preds
    }, index=pd.DatetimeIndex(all_dates))

    regime          = identify_market_regime(prices)
    pred_df["regime"] = regime.reindex(pred_df.index,
                                        method="ffill")

    stats = {}
    for r in ["bull", "bear"]:
        subset = pred_df[pred_df["regime"] == r]
        if len(subset) < 10:
            continue

        if len(np.unique(subset["actual"])) < 2:
            auc = 0.5
        else:
            auc = roc_auc_score(subset["actual"], subset["prob"])

        acc = accuracy_score(subset["actual"], subset["pred"])

        stats[r] = {
            "days"    : len(subset),
            "accuracy": round(acc, 4),
            "roc_auc" : round(auc, 4),
            "up_rate" : round(float(subset["actual"].mean()), 4)
        }

    return stats


def compute_risk_metrics(
    all_dates     : list,
    all_probs     : list,
    prices        : pd.Series,
    threshold     : float = 0.55,
    cost_per_trade: float = 0.001
) -> dict:
    """
    Compute strategy risk metrics as if actually trading.

    Args:
        threshold     : only trade when P(UP) > threshold
        cost_per_trade: transaction cost fraction (0.001 = 0.1%)
                        covers brokerage + market impact

    Returns dict with:
        total_return   : overall P&L
        annual_return  : annualised return
        sharpe_ratio   : return per unit of risk (>1 is good)
        max_drawdown   : worst peak-to-trough loss
        win_rate       : fraction of invested days that were positive
        profit_factor  : total gains / total losses
        n_trades       : number of position changes
    """
    dates    = pd.DatetimeIndex(all_dates)
    probs    = np.array(all_probs)

    # Daily market returns for prediction period
    price_series  = prices.reindex(dates)
    daily_returns = price_series.pct_change().fillna(0).values

    # Position: 1 = invested, 0 = cash
    position = (probs > threshold).astype(float)

    # Transaction costs on every position change
    pos_change  = np.abs(np.diff(position, prepend=position[0]))
    trade_costs = pos_change * cost_per_trade

    # Strategy daily returns
    strat_returns = position * daily_returns - trade_costs
    bh_returns    = daily_returns

    # Cumulative performance
    cum_strat = np.cumprod(1 + strat_returns)
    cum_bh    = np.cumprod(1 + bh_returns)

    # Max drawdown
    rolling_max  = np.maximum.accumulate(cum_strat)
    drawdown     = (cum_strat - rolling_max) / rolling_max
    max_drawdown = float(drawdown.min())

    # Sharpe ratio
    mean_ret = strat_returns.mean()
    std_ret  = strat_returns.std()
    sharpe   = float((mean_ret / std_ret) * np.sqrt(252)) \
               if std_ret > 0 else 0.0

    # Win rate and profit factor
    invested      = strat_returns[position.astype(bool)]
    winning       = invested[invested > 0]
    losing        = invested[invested < 0]
    win_rate      = float(len(winning) / len(invested)) \
                    if len(invested) > 0 else 0.0
    profit_factor = float(winning.sum() / abs(losing.sum())) \
                    if len(losing) > 0 and losing.sum() != 0 else 999.0

    # Annualised return
    n_days       = len(strat_returns)
    total_return = float(cum_strat[-1] - 1)
    annual_ret   = float((1 + total_return) ** (252 / n_days) - 1)

    bh_total  = float(cum_bh[-1] - 1)
    bh_annual = float((1 + bh_total) ** (252 / n_days) - 1)

    n_trades = int(pos_change.sum())

    return {
        "total_return"    : round(total_return,  4),
        "annual_return"   : round(annual_ret,    4),
        "sharpe_ratio"    : round(sharpe,         3),
        "max_drawdown"    : round(max_drawdown,   4),
        "win_rate"        : round(win_rate,       4),
        "profit_factor"   : round(profit_factor,  3),
        "n_trades"        : n_trades,
        "days_invested"   : int(position.sum()),
        "bh_total_return" : round(bh_total,      4),
        "bh_annual_return": round(bh_annual,     4),
        "_cum_strat"      : cum_strat,
        "_cum_bh"         : cum_bh,
        "_drawdown"       : drawdown,
        "_dates"          : dates,
        "_position"       : position
    }


def plot_backtest_report(
    results_df: pd.DataFrame,
    metrics   : dict,
    ticker    : str
):
    """
    Four-panel backtest report chart:
    1. Cumulative return: strategy vs buy-and-hold
    2. Drawdown over time
    3. Per-window AUC (consistency check)
    4. Position: when was model invested vs in cash
    """
    dates    = metrics["_dates"]
    cum_strat= metrics["_cum_strat"]
    cum_bh   = metrics["_cum_bh"]
    drawdown = metrics["_drawdown"]
    position = metrics["_position"]

    fig, axes = plt.subplots(4, 1, figsize=(15, 14),
                              gridspec_kw={"hspace": 0.35})
    fig.suptitle(
        f"{ticker} — Walk-Forward Backtest Report",
        fontsize=14, y=0.98
    )

    # Panel 1: Cumulative return
    ax1 = axes[0]
    ax1.plot(dates, cum_strat, color="#1565C0", lw=2,
             label=f"Strategy "
                   f"({metrics['annual_return']:+.1%}/yr, "
                   f"Sharpe={metrics['sharpe_ratio']:.2f})")
    ax1.plot(dates, cum_bh, color="#FF6F00", lw=1.5,
             linestyle="--",
             label=f"Buy & Hold "
                   f"({metrics['bh_annual_return']:+.1%}/yr)")
    ax1.axhline(1.0, color="gray", lw=0.7, alpha=0.5)
    ax1.set_ylabel("Cumulative return")
    ax1.legend(fontsize=10)
    ax1.grid(alpha=0.2)
    ax1.set_title("Strategy vs Buy-and-Hold", fontsize=11)

    # Panel 2: Drawdown
    ax2 = axes[1]
    ax2.fill_between(dates, drawdown * 100, 0,
                     color="#E53935", alpha=0.6)
    ax2.axhline(
        metrics["max_drawdown"] * 100,
        color="#E53935", lw=1, linestyle="--",
        label=f"Max DD: {metrics['max_drawdown']:.1%}"
    )
    ax2.set_ylabel("Drawdown (%)")
    ax2.legend(fontsize=10)
    ax2.grid(alpha=0.2)
    ax2.set_title("Strategy Drawdown", fontsize=11)

    # Panel 3: Per-window AUC
    ax3 = axes[2]
    window_dates = pd.to_datetime(results_df["test_start"])
    bar_colours  = [
        "#43A047" if v > 0.55 else
        "#FF6F00" if v > 0.50 else
        "#E53935"
        for v in results_df["roc_auc"]
    ]
    ax3.bar(range(len(results_df)), results_df["roc_auc"],
            color=bar_colours, alpha=0.85, width=0.6)
    ax3.axhline(0.55, color="#43A047", lw=1,
                linestyle="--", label="Good threshold (0.55)")
    ax3.axhline(0.50, color="#E53935", lw=1,
                linestyle="--", label="Random (0.50)")
    ax3.set_xticks(range(len(results_df)))
    ax3.set_xticklabels(
        [str(d) for d in results_df["test_start"]],
        rotation=30, fontsize=8
    )
    ax3.set_ylabel("ROC-AUC")
    ax3.set_ylim(0.3, 0.95)
    ax3.legend(fontsize=9)
    ax3.grid(axis="y", alpha=0.2)
    ax3.set_title("AUC Per Test Window (green=good, red=poor)",
                  fontsize=11)

    # Panel 4: Position
    ax4 = axes[3]
    ax4.fill_between(dates, position, 0,
                     color="#1565C0", alpha=0.4,
                     label="Invested")
    ax4.fill_between(dates, 1, position,
                     color="#90CAF9", alpha=0.15,
                     label="Cash")
    ax4.set_ylabel("Position")
    ax4.set_ylim(-0.1, 1.3)
    ax4.legend(fontsize=9)
    ax4.grid(alpha=0.2)
    ax4.set_title("Position Over Time", fontsize=11)
    ax4.xaxis.set_major_formatter(
        mdates.DateFormatter("%b '%y")
    )
    plt.setp(ax4.xaxis.get_majorticklabels(), rotation=30)

    plt.savefig(
        CHARTS_DIR / f"{ticker.replace('.','_')}_wf_backtest.png",
        dpi=150, bbox_inches="tight"
    )
    plt.show()
    print(f"Chart saved.")