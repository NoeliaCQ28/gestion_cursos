import pandas as pd
import numpy as np
from sklearn.decomposition import FactorAnalysis
from sklearn.preprocessing import StandardScaler
import random

def calculate_omega_manual(df):
    try:
        # Standardize the data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df)
        
        # Fit Factor Analysis with 1 factor
        fa = FactorAnalysis(n_components=1, rotation=None)
        fa.fit(X_scaled)
        
        # Get loadings
        loadings = fa.components_.T
        
        # Calculate communalities (h^2)
        communalities = np.sum(loadings**2, axis=1)
        
        # Calculate uniqueness (u^2 = 1 - h^2)
        uniqueness = 1 - communalities
        
        # Calculate Omega
        # Omega = (Sum(loadings))^2 / ((Sum(loadings))^2 + Sum(uniqueness))
        sum_loadings = np.sum(np.abs(loadings)) # Use abs in case of sign flipping, though for consistent items usually positive
        sum_uniqueness = np.sum(uniqueness)
        
        omega = (sum_loadings ** 2) / ((sum_loadings ** 2) + sum_uniqueness)
        
        return omega
    except Exception as e:
        print(f"Error calculating Omega: {e}")
        return None

# Generate simulated data (same logic as app.py)
student_base_scores = [random.uniform(3.5, 5.0) for _ in range(20)]
simulated_data = {}
for i in range(9):
    item_scores = []
    for base_score in student_base_scores:
        noise = random.uniform(-0.6, 0.6)
        score = base_score + noise
        final_score = int(max(1, min(5, round(score))))
        item_scores.append(final_score)
    simulated_data[f'Item{i+1}'] = item_scores

df_reliability = pd.DataFrame(simulated_data)

print("Data shape:", df_reliability.shape)
omega_val = calculate_omega_manual(df_reliability)
print(f"Calculated Omega: {omega_val}")

# Compare with Cronbach's Alpha from pingouin if available
try:
    import pingouin as pg
    cronbach = pg.cronbach_alpha(data=df_reliability)
    print(f"Cronbach's Alpha: {cronbach[0]}")
except:
    print("Could not calculate Cronbach's Alpha")
