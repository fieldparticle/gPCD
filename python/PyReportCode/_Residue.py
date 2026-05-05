import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# Sample data
data = {
    'Advertising_Budget': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # Advertising budget in thousands
    'Sales_Revenue': [1000, 2500, 3500, 4500, 6000, 8000, 11000, 15000, 22000, 30000]  # Sales revenue in dollars
}

df = pd.DataFrame(data)

X = df[['Advertising_Budget']]
y = df['Sales_Revenue']

model = LinearRegression().fit(X, y)
y_pred = model.predict(X)

residuals = y - y_pred
residual_variance = np.var(residuals)

print(f"Residual Variance: {residual_variance}")