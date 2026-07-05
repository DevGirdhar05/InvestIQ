import pandas as pd


def bollinger_bands(
    series: pd.Series,
    window: int = 20,
    num_std: float = 2.0
) -> pd.DataFrame:
    """
    Bollinger Bands — dynamic price range based on volatility.

    Args:
        series  : Close price Series
        window  : Rolling window for SMA and StdDev. Default 20.
        num_std : Number of standard deviations for band width. Default 2.

    Returns DataFrame with:
        BB_Middle : SMA(window)
        BB_Upper  : Middle + num_std × rolling std
        BB_Lower  : Middle − num_std × rolling std
        BB_Width  : (Upper − Lower) / Middle  — normalised bandwidth
        BB_Pct    : Where price sits within the band (0=lower, 1=upper)
    """
    middle = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()

    upper = middle + num_std * std
    lower = middle - num_std * std

    # Band width — how volatile is the stock right now?
    width = (upper - lower) / middle

    # %B — where is price within the band?
    # 0 = at lower band, 0.5 = at middle, 1 = at upper band
    # Values outside 0–1 mean price has broken out of the band
    pct_b = (series - lower) / (upper - lower)

    return pd.DataFrame({
        "BB_Middle": middle,
        "BB_Upper": upper,
        "BB_Lower": lower,
        "BB_Width": width,
        "BB_Pct": pct_b
    }, index=series.index)