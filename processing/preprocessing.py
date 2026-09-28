# processing/preprocessing.py
"""
Controlled Radiometric Operations and Explicit Quality Masking Engine.
Ensures invalid values remain explicitly excluded from downstream calculations.
"""
import numpy as np

def construct_authoritative_quality_mask(raw_power, water_matrix, meta, config):
    """
    Builds a scientific quality mask based on data validity checks.
    Rejects bad data cleanly without manufacturing false ground values.
    """
    # 1. Finite and numeric range check
    valid_data_mask = np.isfinite(raw_power)
    
    fill = meta["fill_value"]
    if not np.isnan(fill):
        valid_data_mask &= (raw_power != fill)
        
    # Enforce technical sensor bounding attributes
    valid_data_mask &= (raw_power >= meta["valid_min"]) & (raw_power <= meta["valid_max"])
    valid_data_mask &= (raw_power >= config["min_valid_linear_power"])
    
    # 2. Ancillary data masking: Filter extreme water-body contamination zones
    valid_data_mask &= (water_matrix <= config["max_allowed_water_fraction"])
    
    return valid_data_mask

def convert_linear_power_to_db(raw_power, quality_mask):
    """
    Transforms linear scattering factors into Decibels.
    Invalid data points are left as NaNs to protect the pipeline.
    """
    db_matrix = np.full(raw_power.shape, np.nan, dtype=np.float32)
    
    # Process only pixels that passed the quality mask logic
    processing_mask = quality_mask & (raw_power > 0.0)
    db_matrix[processing_mask] = 10.0 * np.log10(raw_power[processing_mask])
    
    return db_matrix
