def _clip(value, low=0, high=100):
    return max(low, min(high, value))


def robustness_score(wfe, drawdown_score, consistency, parameter_stability, risk_adjusted_score):
    return round(
        0.35 * wfe
        + 0.20 * drawdown_score
        + 0.15 * consistency
        + 0.20 * parameter_stability
        + 0.10 * risk_adjusted_score,
        2,
    )


def compute_robustness(avg_wfe, max_drawdown_pct, wfa_df, base_return_pct, variant_returns_pct, sharpe_ratio):
    wfe = _clip(avg_wfe) if avg_wfe > 0 else 0
    drawdown = _clip(100 - max_drawdown_pct)

    if wfa_df.empty:
        consistency = 0
    else:
        consistency = _clip(100 * (wfa_df["out_sample_return"] > 0).sum() / len(wfa_df))

    if variant_returns_pct:
        gaps = [abs(base_return_pct - r) for r in variant_returns_pct]
        stability = _clip(100 - (sum(gaps) / len(gaps)) * 2)
    else:
        stability = 50

    risk_adj = _clip((sharpe_ratio or 0) * 50)

    components = {
        "wfe": wfe,
        "drawdown": drawdown,
        "consistency": consistency,
        "parameter_stability": stability,
        "risk_adjusted": risk_adj,
    }

    total = robustness_score(
        wfe=components["wfe"],
        drawdown_score=components["drawdown"],
        consistency=components["consistency"],
        parameter_stability=components["parameter_stability"],
        risk_adjusted_score=components["risk_adjusted"],
    )

    return total, components
