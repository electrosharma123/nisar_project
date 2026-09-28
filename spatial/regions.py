# spatial/regions.py
"""
Connected-Component Spatial Target Clustering and Trajectory Profiling Engine.
Groups adjacent pixels into isolated targets and tracks objective temporal changes.
"""
import numpy as np
import pandas as pd
from scipy.ndimage import label, center_of_mass

def group_anomalies_into_regions(anomaly_mask, change_matrix, time_series_cube, lat_2d, lon_2d, config, pixel_spacing_x):
    """
    Clusters anomalous pixels into candidate regions and evaluates signal trajectories neutrally.
    """
    min_size = config["min_cluster_pixel_size"]
    max_export = config["max_regions_to_export"]
    
    connectivity_structure = np.ones((3, 3))
    labeled_matrix, num_features = label(anomaly_mask, structure=connectivity_structure)
    
    print(f"🧩 Connected anomaly components before region filtering: {num_features}")
    
    region_records = []
    num_acquisitions = time_series_cube.shape[0]
    
    for r_id in range(1, num_features + 1):
        region_pixels = (labeled_matrix == r_id)
        pixel_count = int(np.sum(region_pixels))
        
        if pixel_count < min_size:
            continue
            
        c_row, c_col = center_of_mass(region_pixels)
        c_lat = float(lat_2d[int(c_row), int(c_col)])
        c_lon = float(lon_2d[int(c_row), int(c_col)])
        
        # Calculate real-world area mapping to equal-area projections
        area_km2 = (pixel_count * (abs(pixel_spacing_x) ** 2)) / 1e6
        
        region_values = change_matrix[region_pixels]
        mean_delta = float(np.mean(region_values))
        median_delta = float(np.median(region_values))
        max_delta = float(np.max(region_values))
        min_delta = float(np.min(region_values))
        
        # Objective trajectory profile mapping
        profile_history = []
        for t_idx in range(num_acquisitions):
            slice_avg = np.nanmean(time_series_cube[t_idx][region_pixels])
            profile_history.append(slice_avg)
            
        step_diffs = np.diff(profile_history)
        if np.all(step_diffs >= -0.15) or np.all(step_diffs <= 0.15):
            consistency = "TEMPORALLY CONSISTENT"
            duration_desc = f"Consistent directional change across {num_acquisitions} observations"
        else:
            consistency = "TRANSITIONAL"
            duration_desc = "Fluctuating Backscatter Signal"
            
        direction_desc = "BACKSCATTER INCREASE" if mean_delta > 0 else "BACKSCATTER DECREASE"
        
        region_records.append({
            "region_id": r_id,
            "area_km2": area_km2,
            "centroid_lat": c_lat,
            "centroid_lon": c_lon,
            "mean_change_db": mean_delta,
            "median_change_db": median_delta,
            "max_change_db": max_delta,
            "min_change_db": min_delta,
            "temporal_consistency": consistency,
            "change_direction": direction_desc,
            "change_duration": duration_desc,
            "observation_count": num_acquisitions
        })
        
    df_regions = pd.DataFrame(region_records)
    if not df_regions.empty:
        df_regions = df_regions.sort_values(by="max_change_db", ascending=False).head(max_export)
        
    return df_regions, labeled_matrix
