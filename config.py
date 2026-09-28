# config.py
"""
Authoritative Single Point of Truth (SPOT) Configuration Registry.
Contains all system hyperparameters, data paths, and scientific limits.
No hidden numerical thresholds are permitted inside processing submodules.
"""

CONFIG = {
    # Chronologically matching NISAR L3 Descending files from your active local workspace
    # Spans a 6-file clean high-density timeline (Dec 2025 -> Sept 2026) on Track 005_D_083
    "input_files": [
        "NISAR_L3_PR_SME2_008_005_D_083_2005_QPDH_A_20251216T132815_20251216T132838_X05010_N_P_J_001.h5",
        "NISAR_L3_PR_SME2_024_005_D_083_4005_DHDH_A_20260626T132815_20260626T132825_P05023_N_P_J_001.h5",
        "NISAR_L3_PR_SME2_025_005_D_083_4005_DHDH_A_20260708T132814_20260708T132833_P05023_N_P_J_001.h5",
        "NISAR_L3_PR_SME2_026_005_D_083_4005_DHDH_A_20260720T132813_20260720T132832_P05023_N_P_J_001.h5",
        "NISAR_L3_PR_SME2_028_005_D_083_4005_DHDH_A_20260813T132812_20260813T132831_P05023_N_P_J_001.h5",
        "NISAR_L3_PR_SME2_030_005_D_083_2005_QPDH_A_20260906T132812_20260906T132835_P05023_N_P_J_001.h5"
    ],
    
    # Target Sensor Data Layer Selections
    "target_frequency": "frequencyA",
    "target_polarization": "HH",
    
    # Radiometric Filtering Limits
    "min_valid_linear_power": 1e-6,
    
    # Non-Parametric Statistical Anomaly Threshold Selection (Percentile-driven)
    "anomaly_percentile": 99.0,
    "max_outlier_suppression_db": 15.0,
    
    # Metric-based Spatial Processing and Cleaning Bounds
    "border_cleaning_distance_meters": 500.0,
    "min_cluster_pixel_size": 5,
    "max_regions_to_export": 30,
    
    # Data Quality Control Filtering Constraints
    "max_allowed_water_fraction": 0.05,
    
    # Geospatial Output Parameters
    "nodata_value": -9999.0,
    "output_crs": "EPSG:6933",
    
    # Pipeline Output Management
    "generate_interactive_map": True,
    "output_root": "outputs",
    "software_version": "1.0.0"
}
