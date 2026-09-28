# processing/anomaly.py
"""
Non-Parametric Statistical Anomaly Classification Engine.
Replaces arbitrary numerical cutoffs with dynamic data variance bounds.
"""
import numpy as np

def isolate_statistical_anomalies(change_matrix, domain_mask, target_percentile, suppression_limit):
    """
    Extracts high-intensity anomalies based on data variance across the valid domain mask.
    Filters out extreme sensor anomalies that exceed the suppression limit.
    """
    valid_pixels = np.isfinite(change_matrix) & domain_mask
    valid_data_points = change_matrix[valid_pixels]
    
    if valid_data_points.size == 0:
        raise ValueError("Target validation processing grid is completely empty. Structural check required.")
        
    median_val = float(np.median(valid_data_points))
    p95_val = float(np.percentile(valid_data_points, 95))
    dynamic_cutoff_db = float(np.percentile(valid_data_points, target_percentile))
    
    stats_summary = {
        "median": median_val,
        "p95": p95_val,
        "cutoff_applied": dynamic_cutoff_db
    }
    
    # Isolate valid anomalies based on statistical variance, keeping invalid pixels properly masked
    anomaly_mask = (
        np.isfinite(change_matrix) &
        (change_matrix >= dynamic_cutoff_db) &
        (change_matrix <= suppression_limit) &
        domain_mask
    )
    
    return anomaly_mask, stats_summary
