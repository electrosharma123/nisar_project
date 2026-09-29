# processing/anomaly.py
"""
Applies dual-sided non-parametric statistical partitioning to automatically isolate 
both extreme backscatter increases (gains) and decreases (attenuations).
"""
import numpy as np

def isolate_statistical_anomalies(change_matrix, domain_mask, config):
    """
    Identifies statistical anomalies by tracking variance across the valid domain mask.
    Saves separate partitions for upper and lower distribution tails.
    """
    valid_pixels = np.isfinite(change_matrix) & domain_mask
    valid_data_points = change_matrix[valid_pixels]
    
    if valid_data_points.size == 0:
        raise ValueError("Operational processing domain is completely masked. Check erosion settings.")
        
    median_val = float(np.median(valid_data_points))
    p95_val = float(np.percentile(valid_data_points, 95))
    
    # DUAL-SIDED EXTRACTION: Compute dynamic cutoffs for both tails of the distribution
    p_high = config["anomaly_percentile_high"]
    p_low = config["anomaly_percentile_low"]
    
    cutoff_high_db = float(np.percentile(valid_data_points, p_high))
    cutoff_low_db = float(np.percentile(valid_data_points, p_low))
    
    stats_summary = {
        "median": median_val,
        "p95": p95_val,
        "cutoff_high": cutoff_high_db,
        "cutoff_low": cutoff_low_db
    }
    
    # Isolate anomalies across both boundaries, suppressing extreme sensor glitch thresholds
    suppression_limit = config["max_outlier_suppression_db"]
    
    high_anomaly = (change_matrix >= cutoff_high_db) & (change_matrix <= suppression_limit)
    low_anomaly = (change_matrix <= cutoff_low_db) & (change_matrix >= -suppression_limit)
    
    # Combine both tails into a single master boolean mask
    anomaly_mask = np.isfinite(change_matrix) & (high_anomaly | low_anomaly) & domain_mask
    
    return anomaly_mask, stats_summary
