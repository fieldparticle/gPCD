import pandas as pd
from scipy.stats import pearsonr
# Sample data
data = {
    'study_hours': [3, 4, 6, 8, 10, 12, 15],
    'test_scores': [55, 60, 65, 70, 80, 85, 90]
}
df = pd.DataFrame(data)
# Calculate Pearson Correlation Coefficient between 'study_hours' and 'test_scores'
correlation_coefficient, p_value = pearsonr(df['study_hours'], df['test_scores'])
# Display results
print(f"Pearson Correlation Coefficient: {correlation_coefficient}")
print(f"P-Value: {p_value}")