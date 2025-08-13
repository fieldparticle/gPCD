import numpy as np

import matplotlib.pyplot as plt

from scipy.optimize import curve_fit


# Define the quadratic model

def quadratic_model(x, a, b, c):

    return a * x**2 + b * x + c


# Create synthetic data

x_data = np.linspace(-5, 5, num=40)

y_data = 2 * x_data**2 - 3 * x_data + 5 + np.random.normal(size=x_data.size)


# Fit the model to the data

params, covariance = curve_fit(quadratic_model, x_data, y_data)


# Plot the data and the fitted curve

plt.scatter(x_data, y_data, label='Data')

plt.plot(x_data, quadratic_model(x_data, *params), label='Fitted curve', color='red')

plt.legend()

plt.show()