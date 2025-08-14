from pygam import LinearGAM, s
import pandas as pd
import matplotlib.pyplot as plt

# Sample data
data = {
    'study_hours': [3, 4, 6, 8, 10, 12, 15],
    'test_scores': [55, 60, 65, 70, 80, 85, 90]
}
df = pd.DataFrame(data)

# Fit a Generalized Additive Model
gam = LinearGAM(s(0)).fit(df[['study_hours']], df['test_scores'])
y_pred_gam = gam.predict(df[['study_hours']])

# Plot the results
plt.scatter(df['study_hours'], df['test_scores'], color='blue')
plt.plot(df['study_hours'], y_pred_gam, color='red')
plt.title('Generalized Additive Model (GAM) Fit')
plt.xlabel('Study Hours')
plt.ylabel('Test Scores')
plt.show()