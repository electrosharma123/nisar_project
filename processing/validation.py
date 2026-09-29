# processing/validation.py
"""
Strict Compatibility Verification Engine. 
Protects matrix math by ensuring geographic alignment and rejecting mismatched shapes.
"""
import sys
import numpy as np

def validate_dataset_compatibility(obs_list):
    """
    Executes cross-examination of data arrays against the spatial configuration of the baseline.
    Raises strict ValueErrors immediately upon detecting target spatial mismatches.
    """
    if len(obs_list) < 2:
        raise ValueError("Multi-temporal virtual tracking cubes require a minimum of two comparable datasets.")
        
    base = obs_list[0]
    print("🔬 Executing authoritative spatial alignment and sensor parameters consistency checks...")
    
    for idx, obs in enumerate(obs_list[1:], start=2):
        # 1. Evaluate Sensor Configuration Integrity
        if obs["product_family"] != base["product_family"]:
            print(f"CRITICAL ERROR: Product lineage family mismatch. Baseline: {base['product_family']} vs File {idx}: {obs['product_family']}", file=sys.stderr)
            sys.exit(1)
            
        if obs["crs_epsg"] != base["crs_epsg"]:
            print(f"CRITICAL ERROR: Reference System CRS Projection Mismatch. Baseline: EPSG:{base['crs_epsg']} vs File {idx}: EPSG:{obs['crs_epsg']}", file=sys.stderr)
            sys.exit(1)
            
        # 2. Evaluate Matrix Footprint Overlap Integrity
        if obs["rows"] != base["rows"] or obs["cols"] != base["cols"]:
            print(f"CRITICAL ERROR: Matrix cell grid dimensions mismatch. Base: ({base['rows']},{base['cols']}) vs File {idx}: ({obs['rows']},{obs['cols']})", file=sys.stderr)
            sys.exit(1)
            
        if not np.isclose(obs["pixel_spacing_x"], base["pixel_spacing_x"]) or \
           not np.isclose(obs["pixel_spacing_y"], base["pixel_spacing_y"]):
            print(f"CRITICAL ERROR: Ground resolution voxel metric cell sizes split at file index {idx}.", file=sys.stderr)
            sys.exit(1)
            
        # 3. Evaluate Geographic Coverage and Alignment Bounding Box Integrity
        lat_tolerance = abs(base["pixel_spacing_y"]) / 111000.0  # Safe geometric alignment conversion to degrees
        lon_tolerance = abs(base["pixel_spacing_x"]) / 111000.0
        
        if not np.isclose(obs["lat_min_val"], base["lat_min_val"], atol=lat_tolerance) or \
           not np.isclose(obs["lon_min_val"], base["lon_min_val"], atol=lon_tolerance):
            print(f"CRITICAL ERROR: Bounding Box geographic alignment shift detected at input file index {idx}. Arrays do not occupy identical space on Earth.", file=sys.stderr)
            sys.exit(1)
            
    print("✅ Geometric alignment, CRS projections, and dimensions passed verification rules.")
