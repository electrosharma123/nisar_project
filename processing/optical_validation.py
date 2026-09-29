# processing/optical_validation.py
"""
Open-Access Sentinel-2 STAC Cross-Validation Engine.
Queries multi-spectral optical cubes to confirm vegetation canopy removal
and cross-validate radar change detection candidate regions via NDVI anomalies.
Implements robust HTML error trapping and alternative backup server failover routing.
"""
import numpy as np
import pandas as pd
from pystac_client import Client
import planetary_computer
import stackstac
import warnings

def cross_validate_regions_with_sentinel(df_regions, config):
    """
    Connects to STAC Client Endpoint to query pre- and post-event Sentinel-2 scenes.
    Natively switches to backup endpoint servers if primary HTML gateway blocks access.
    """
    # Initialize all validation columns immediately to protect the main orchestrator print index mapping
    if not df_regions.empty:
        df_regions["sentinel_pre_ndvi"] = np.nan
        df_regions["sentinel_post_ndvi"] = np.nan
        df_regions["sentinel_ndvi_shift"] = np.nan
        df_regions["cross_validation_status"] = "PENDING STAC EVALUATION"
        
    if df_regions.empty or not config["run_optical_validation"]:
        print("⚠️ Skipping Optical Validation Layer as configured or database is empty.")
        if not df_regions.empty:
            df_regions["cross_validation_status"] = "SKIPPED VIA CONFIG LAYER"
        return df_regions
        
    stac_client = None
    active_url = config["stac_api_url"]
    is_backup = False
    
    print("\n🛰 ... Establishing connection to Open-Access STAC Client Endpoint ...")
    try:
        # Attempt primary connection
        stac_client = Client.open(active_url)
        # Quick check call to verify the endpoint is giving valid JSON data rather than HTML errors
        _ = stac_client.get_collections()
    except Exception as primary_err:
        print(f"⚠️ Primary STAC Endpoint blocked or down (HTML parsing error). Triggering backup routing failover...")
        try:
            active_url = config["stac_backup_url"]
            is_backup = True
            stac_client = Client.open(active_url)
        except Exception as backup_err:
            print(f"💥 Critical: All STAC networks blocked or offline. Defaulting to unverified radar metrics.")
            df_regions["cross_validation_status"] = "NETWORKS OFFLINE FALLBACK"
            return df_regions
            
    print(f"✅ Connected successfully to Data Service Catalog: '{active_url}'")
    updated_records = []
    
    # Establish collection name mappings depending on chosen server data dictionaries
    collection_name = "sentinel-2-l2a" if not is_backup else "sentinel-2-l2a"
    
    for idx, row in df_regions.iterrows():
        lat = row["centroid_lat"]
        lon = row["centroid_lon"]
        
        # Build a small spatial bounding box buffer around centroid (approx 1 km)
        bbox = [lon - 0.005, lat - 0.005, lon + 0.005, lat + 0.005]
        print(f" 🔍 Running cloud-cleared multi-spectral fetch query for Region #{int(row['region_id'])}...")
        
        record = row.to_dict()
        
        try:
            # Query Post-Event Window (September 2026 Monsoon Window)
            search_post = stac_client.search(
                collections=[collection_name],
                bbox=bbox,
                datetime="2026-09-01/2026-09-30",
                query={"eo:cloud_cover": {"lt": config["sentinel_max_cloud_cover_percent"]}}
            )
            items_post = list(search_post.get_items())
            
            # Query Pre-Event Window (Dry season control frame - June 2026)
            search_pre = stac_client.search(
                collections=[collection_name],
                bbox=bbox,
                datetime="2026-05-01/2026-06-15",
                query={"eo:cloud_cover": {"lt": 15.0}}
            )
            items_pre = list(search_pre.get_items())
            
            if items_post and items_pre:
                # Sign assets only if using the primary Planetary Computer network
                if not is_backup:
                    signed_items_post = [planetary_computer.sign(item) for item in items_post]
                    signed_items_pre = [planetary_computer.sign(item) for item in items_pre]
                else:
                    signed_items_post = items_post
                    signed_items_pre = items_pre
                
                # Stack the multi-spectral assets into xarray cubes using unified coordinate keys
                cube_post = stackstac.stack(signed_items_post, assets=["B04", "B08"], bounds=bbox).compute()
                cube_pre = stackstac.stack(signed_items_pre, assets=["B04", "B08"], bounds=bbox).compute()
                
                # Calculate NDVI profiles cleanly while ignoring projection warning alerts
                def compute_ndvi(cube):
                    nir = cube.sel(band="B08").values.astype(np.float32)
                    red = cube.sel(band="B04").values.astype(np.float32)
                    
                    with warnings.catch_warnings():
                        warnings.filterwarnings('ignore', category=RuntimeWarning, message='invalid value encountered in divide')
                        denom = nir + red
                        denom[denom == 0] = np.nan
                        return (nir - red) / denom
                
                ndvi_pre = np.nanmean(compute_ndvi(cube_pre))
                ndvi_post = np.nanmean(compute_ndvi(cube_post))
                ndvi_delta = ndvi_post - ndvi_pre
                
                record["sentinel_pre_ndvi"] = float(ndvi_pre)
                record["sentinel_post_ndvi"] = float(ndvi_post)
                record["sentinel_ndvi_shift"] = float(ndvi_delta)
                
                # CROSS-VALIDATION CRITERIA DECISION RULE:
                if row["change_direction"] == "BACKSCATTER DECREASE" and ndvi_delta <= config["ndvi_anomaly_threshold"]:
                    record["cross_validation_status"] = "VERIFIED CANOPY STRIPPING (HIGH CONFIDENCE)"
                elif row["change_direction"] == "BACKSCATTER INCREASE" and abs(ndvi_delta) < 0.1:
                    record["cross_validation_status"] = "VERIFIED INTACT SURFACE MOISTURE ANOMALY"
                else:
                    record["cross_validation_status"] = "UNVERIFIED SURFACE UPDATE (SPECTRAL MISMATCH)"
            else:
                record["cross_validation_status"] = "INSUFFICIENT DATA (CLOUD COVER BLOCK)"
                
        except Exception as err:
            record["cross_validation_status"] = f"SERVER FALLBACK ERROR: {str(err)[:15]}"
            
        updated_records.append(record)
        
    return pd.DataFrame(updated_records)
