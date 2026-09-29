# main.py
"""
Central Orchestration Engine for Version 1.1.5 Production Release.
Executes multi-temporal NISAR radar-backscatter change detection with integrated 
open-access Sentinel-2 STAC optical cross-validation.
"""
import os
import numpy as np
from scipy.ndimage import binary_erosion

from config import CONFIG
from data_io.nisar_reader import run_diagnostic_inspection, print_scientific_product_report, read_raw_data_matrices
from processing.validation import validate_dataset_compatibility
from processing.preprocessing import construct_authoritative_quality_mask, convert_linear_power_to_db
from processing.temporal import build_time_series_cube, analyze_vector_virtual_sensor_trends
from processing.anomaly import isolate_statistical_anomalies
from processing.optical_validation import cross_validate_regions_with_sentinel
from spatial.regions import group_anomalies_into_regions
from spatial.geospatial import export_matrix_to_geotiff
from visualization.plots import generate_static_scientific_plots
from visualization.map import generate_cluster_interactive_map

def orchestrate_pipeline():
    print(f"🚀 NISAR Multi-Temporal Virtual Sensor Pipeline v{CONFIG['software_version']} Initialized.\n")
    
    if not os.path.exists(CONFIG["output_root"]):
        os.makedirs(CONFIG["output_root"], exist_ok=True)
        
    # =====================================================================
    # PHASE 1: TECHNICAL INSPECTION & CHRONOLOGICAL METADATA REORDERING
    # =====================================================================
    raw_observations = []
    for idx, path in enumerate(CONFIG["input_files"], start=1):
        print(f"📋 Querying authoritative telemetry records on data asset {idx}/{len(CONFIG['input_files'])}...")
        meta = run_diagnostic_inspection(path)
        raw_observations.append(meta)
        
    # Order the collection chronologically based on true telemetry sensing records
    raw_observations.sort(key=lambda x: x["acquisition_datetime"])
    
    print("\n📅 Chronological Telemetry Sensing Timeline Confirmed:")
    for idx, obs in enumerate(raw_observations):
        print(f"   • Slot {idx+1}: Sensing Start: {obs['sensing_start']} -> {obs['filename']}")
        
    # Print the single scientific audit report from the primary baseline metadata
    print_scientific_product_report(raw_observations[0])
    
    # Validate cross-dataset spatial bounds and projection geometry consistency
    validate_dataset_compatibility(raw_observations)
    
    # =====================================================================
    # PHASE 2: RADIOMETRIC DATA PREPROCESSING & DATA CUBE GENERATION
    # =====================================================================
    db_stack = []
    lat_grid, lon_grid = None, None
    dates_list = [obs["sensing_start"][:10] for obs in raw_observations]
    
    print("\n🛡️ Initializing explicit data quality control mask arrays...")
    for obs in raw_observations:
        lat_grid, lon_grid, raw_power, water_matrix = read_raw_data_matrices(
            obs["path"], obs["grid_base_path"],
            CONFIG["target_frequency"], CONFIG["target_polarization"]
        )
        
        # Build quality filters using attributes mined from metadata
        q_mask = construct_authoritative_quality_mask(raw_power, water_matrix, obs, CONFIG)
        
        # Apply safe logarithmic mapping exclusively within the valid mask domain
        db_layer = convert_linear_power_to_db(raw_power, q_mask)
        db_stack.append(db_layer)
        
    time_series = build_time_series_cube(db_stack, dates_list)
    print(f"📊 3D Labeled Virtual Sensor Data Cube constructed. Array configuration: {time_series['cube'].shape}")
    
    # =====================================================================
    # PHASE 3: MULTI-TEMPORAL VECTOR TRAJECTORY TRACKING
    # =====================================================================
    temporal_package = analyze_vector_virtual_sensor_trends(time_series)
    
    total_change_key = f"change_{dates_list[-1]}_minus_{dates_list[0]}"
    backscatter_change_db = temporal_package["pairwise"][total_change_key]
    
    # =====================================================================
    # PHASE 4: ADAPTIVE GRID CLEANING & ANOMALY SEPARATION
    # =====================================================================
    pixel_spacing = float(raw_observations[0]["pixel_spacing_x"])
    required_distance = float(CONFIG["border_cleaning_distance_meters"])
    calculated_iterations = max(1, int(required_distance / abs(pixel_spacing)))
    
    print(f"\n🔍 Border processing metric resolution: {abs(pixel_spacing):.2f} meters per pixel.")
    print(f"🔍 Applying adaptive boundary cleaning erosion layer ({calculated_iterations} iterations)...")
    
    valid_data_mask = np.isfinite(backscatter_change_db)
    clean_domain_mask = binary_erosion(valid_data_mask, iterations=calculated_iterations)
    
    # Extract anomalies based on dynamic variance distributions (Updated for V1.1 Dual-Sided CONFIG)
    anomaly_mask, stats = isolate_statistical_anomalies(
        backscatter_change_db, clean_domain_mask, CONFIG
    )
    
    print(f"📈 Threshold Cutoffs Locked:")
    print(f"   • High Tail Cutoff (Gain):  +{stats['cutoff_high']:.3f} dB")
    print(f"   • Low Tail Cutoff (Drop)  :  {stats['cutoff_low']:.3f} dB")
    print(f"   • Baseline background distribution median: {stats['median']:.3f} dB")
    
    # =====================================================================
    # PHASE 5: SPATIAL CANDIDATE TARGET EXTRACTION
    # =====================================================================
    df_regions, cluster_matrix = group_anomalies_into_regions(
        anomaly_mask, backscatter_change_db, time_series["cube"],
        lat_grid, lon_grid, CONFIG, pixel_spacing
    )
    
    # =====================================================================
    # PHASE 5.5: SENTINEL-2 OPTICAL CROSS-VALIDATION LAYER
    # =====================================================================
    df_regions = cross_validate_regions_with_sentinel(df_regions, CONFIG)
    
    # =====================================================================
    # PHASE 6: GEOGRAPHICALLY SEPARATED LAYER EXPORTS
    # =====================================================================
    print("\n💾 Commencing georeferenced asset generation routine...")
    epsg_code = raw_observations[0]["crs_epsg"]
    nodata = CONFIG["nodata_value"]
    root = CONFIG["output_root"]
    
    generate_static_scientific_plots(root, "01_raw_measurement.png", backscatter_change_db, lat_grid, lon_grid)
    export_matrix_to_geotiff(root, "02_temporal_change.tif", backscatter_change_db, lat_grid, lon_grid, epsg_code, nodata)
    export_matrix_to_geotiff(root, "03_anomaly_mask.tif", anomaly_mask.astype(np.float32), lat_grid, lon_grid, epsg_code, nodata)
    export_matrix_to_geotiff(root, "04_temporal_mean_trend.tif", temporal_package["statistics"]["temporal_mean"], lat_grid, lon_grid, epsg_code, nodata)
    
    if CONFIG["generate_interactive_map"]:
        generate_cluster_interactive_map(root, "05_interactive_map.html", df_regions)
        
    csv_path = os.path.join(root, "06_candidate_regions.csv")
    df_regions.to_csv(csv_path, index=False)
    print(f"   💾 Candidate structural change region attribute database saved to: '{csv_path}'")
    
    print("\n📌 PIPELINE TERMINAL REGION SUMMARY PROFILE:")
    if not df_regions.empty:
        # Adjusted column subset view to accommodate the new validation attributes
        columns_to_show = ["region_id", "area_km2", "centroid_lat", "centroid_lon", "mean_change_db", "max_change_db", "change_direction", "cross_validation_status"]
        print(df_regions[columns_to_show].to_string(index=False))
    else:
        print("⚠️ No valid structural anomaly targets cross the specified dynamic criteria limits.")
        
    print(f"\n🎉 Pipeline frozen. Version {CONFIG['software_version']} outputs written successfully.")

if __name__ == "__main__":
    orchestrate_pipeline()
