import numpy as np  

prices=np.array([294,294.5,296,295.6])
print(prices)

daily_returns=np.diff(prices)/prices[:-1]*100

print(daily_returns)

above_294=prices>294
print(above_294)

print(prices[above_294])

print(f"Mean Price : ₹{prices.mean()}")
print(f"Max Price : ₹{prices.max()}")
print(f"Min Price : ₹{prices.min()}")
print(f"Standard deviation : ₹{prices.std() : .2f}")