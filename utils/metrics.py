def calculate_return(start_value, end_value):
    return ((end_value - start_value) / start_value) * 100


def _annualized_return(total_return_pct, bars):
    if bars <= 0:
        return 0.0
    growth = 1 + total_return_pct / 100
    if growth <= 0:
        return -100.0
    years = bars / 252
    return ((growth ** (1 / years)) - 1) * 100


def walk_forward_efficiency(
    out_sample_return,
    in_sample_return,
    min_in_sample_pct=0.5,
    oos_bars=126,
    is_bars=504,
):
    ann_is = _annualized_return(in_sample_return, is_bars)
    ann_oos = _annualized_return(out_sample_return, oos_bars)

    if abs(ann_is) < min_in_sample_pct:
        if ann_oos > 0:
            return 100.0
        if ann_oos == 0:
            return 50.0
        return 0.0

    if ann_is < 0 and ann_oos > 0:
        return min(200.0, abs(ann_oos / ann_is) * 100)

    ratio = (ann_oos / ann_is) * 100
    return max(-100.0, min(200.0, ratio))


def summarize_wfa_efficiency(efficiency_series):
    if efficiency_series.empty:
        return 0.0
    median = float(efficiency_series.median())
    mean = float(efficiency_series.mean())
    return 0.6 * median + 0.4 * mean
