import numpy as np


prices = np.array([2891.0, 2934.5, 2910.2, 2955.8, 2900.0])

print(prices.shape)
print(prices.dtype)


print(prices[0])       # 2891.0  — first element
print(prices[-1])      # 2900.0  — last element
print(prices[1:4])     # [2934.5, 2910.2, 2955.8]  — slice, end exclusive


prices_usd=prices/83
print(prices_usd)


daily_returns=np.diff(prices)/prices[:-1]*100
print(daily_returns)

above_2920=prices>2920
print(prices[above_2920])

print(f"Mean Price : ₹{prices.mean() : .2f}")
print(f"Max Price : ₹{prices.max() : .2f}")
print(f"Min Prie : ₹{prices.min() : .2f}")
print(f"Std dev : ₹{prices.std() : .2f}")