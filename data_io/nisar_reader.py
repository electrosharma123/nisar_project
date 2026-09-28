# data_io/nisar_reader.py
"""
Authoritative Metadata Discovery and Input Matrix Reader Engine for V1.0.
Extracts true sensing bounds, filename components, and data attributes
directly from HDF5 parameters to maintain a rigorous scientific audit trail.
"""
import os
import re
import h5py
import numpy as np

def run_diagnostic_inspection(file_path):
    """
    Queries internal HDF5 metadata paths to distinguish between actual sensing
    intervals and ground-station processing timestamps.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Target data container path does not exist on disk: {file_path}")
        
    meta = {"path": file_path, "filename": os.path.basename(file_path)}
    
    # Extract fallback temporal bounds from filename via regex
    match = re.search(r'_(\d{8}T\d{6})_(\d{8}T\d{6})_', meta["filename"])
    if match:
        meta["filename_sensing_start"] = match.group(1)
        meta["filename_sensing_stop"] = match.group(2)
    else:
        meta["filename_sensing_start"] = "Unknown"
        meta["filename_sensing_stop"] = "Unknown"
        
    with h5py.File(file_path, "r") as f:
        if "science" not in f:
            raise KeyError(f"Root 'science' layer absent. Corrupt or unreadable HDF5 layout: {file_path}")
            
        lsar_grp = f["science/LSAR"]
        product_keys = list(lsar_grp.keys())
        if not product_keys:
            raise KeyError(f"No product family group identified under science/LSAR in file: {file_path}")
            
        product_family = str(product_keys[0])
        meta["product_family"] = product_family
        
        grid_base = f"science/LSAR/{product_family}/grids"
        meta["grid_base_path"] = grid_base
        
        # 1. Authoritative Acquisition Sensing Extents
        metadata_root = f"science/LSAR/{product_family}/metadata/processingInformation/parameters/runConfigurationContents"
        source_metadata_root = f"science/LSAR/{product_family}/metadata/sourceData"
        
        start_path = f"{source_metadata_root}/extents/sensingStartTime"
        stop_path = f"{source_metadata_root}/extents/sensingStopTime"
        proc_path = f"{source_metadata_root}/processingDateTime"
        
        # Extract true sensing timeline parameters from internal telemetry
        if start_path in f and stop_path in f:
            meta["sensing_start"] = f[start_path][()].decode('utf-8') if isinstance(f[start_path][()], bytes) else str(f[start_path][()])
            meta["sensing_stop"] = f[stop_path][()].decode('utf-8') if isinstance(f[stop_path][()], bytes) else str(f[stop_path][()])
        else:
            meta["sensing_start"] = meta["filename_sensing_start"]
            meta["sensing_stop"] = meta["filename_sensing_stop"]
            
        if proc_path in f:
            meta["processing_timestamp"] = f[proc_path][()].decode('utf-8') if isinstance(f[proc_path][()], bytes) else str(f[proc_path][()])
        else:
            meta["processing_timestamp"] = "Unknown"
            
        # Standardize primary acquisition timestamp for sorting rules
        meta["acquisition_datetime"] = meta["sensing_start"]
        
        # 2. Query Data Storage Layer Specifications
        dataset_path = f"{grid_base}/radarData/frequencyA/sigma0HH"
        if dataset_path in f:
            ds = f[dataset_path]
            meta["measurement"] = "Normalized Radar Cross Section (Sigma0)"
            meta["units"] = ds.attrs.get("units", b"linear power").decode('utf-8') if isinstance(ds.attrs.get("units"), bytes) else str(ds.attrs.get("units", "linear power"))
            meta["scale_factor"] = float(ds.attrs.get("scale_factor", 1.0))
            meta["fill_value"] = float(ds.attrs.get("_FillValue", np.nan))
            meta["valid_min"] = float(ds.attrs.get("valid_min", 0.0))
            meta["valid_max"] = float(ds.attrs.get("valid_max", np.inf))
        else:
            raise KeyError(f"Target measurement dataset '{dataset_path}' missing from data file: {file_path}")
            
        # 3. Spatial Reference Resolution
        proj_path = f"{grid_base}/projection"
        if proj_path in f:
            meta["crs_epsg"] = int(f[proj_path][()])
        else:
            raise KeyError(f"Authoritative spatial reference system data missing from container path: {proj_path}")
            
        # 4. Grid Footprint Dimension Mapping
        lat_ds = f[f"{grid_base}/latitude"]
        lon_ds = f[f"{grid_base}/longitude"]
        meta["rows"] = lat_ds.shape[0]
        meta["cols"] = lon_ds.shape[0]
        
        meta["pixel_spacing_x"] = float(f[f"{grid_base}/xCoordinateSpacing"][()]) if f"{grid_base}/xCoordinateSpacing" in f else 1.0
        meta["pixel_spacing_y"] = float(f[f"{grid_base}/yCoordinateSpacing"][()]) if f"{grid_base}/yCoordinateSpacing" in f else 1.0
        
        meta["lon_min_val"] = float(np.min(lon_ds[:]))
        meta["lon_max_val"] = float(np.max(lon_ds[:]))
        meta["lat_min_val"] = float(np.min(lat_ds[:]))
        meta["lat_max_val"] = float(np.max(lat_ds[:]))
        
        qa_base = f"{grid_base}/ancillaryData"
        meta["quality_layers"] = list(f[qa_base].keys()) if qa_base in f else ["None Registered"]
        
    return meta

def print_scientific_product_report(meta):
    """Generates the single authoritative project runtime data audit trail report."""
    print("\n" + "═"*75)
    print("                    NISAR SCIENTIFIC PRODUCT REPORT")
    print("═"*75)
    print(f" • Source File Name     : {meta['filename']}")
    print(f" • Product Family Group : {meta['product_family']} (Soil Moisture Estimator Gridded)")
    print(f" • Layer Measurement    : {meta['measurement']} (sigma0HH)")
    print(f" ─── Temporal Timestamps Registry ──────────────────────────────────────────")
    print(f" • True Sensing Start   : {meta['sensing_start']}")
    print(f" • True Sensing Stop    : {meta['sensing_stop']}")
    print(f" • Processing Ground Time: {meta['processing_timestamp']}")
    print(f" • Filename Time Header : Start: {meta['filename_sensing_start']} | Stop: {meta['filename_sensing_stop']}")
    print(f" ─── Radiometric Properties ────────────────────────────────────────────────")
    print(f" • Stored Space Units   : {meta['units']}")
    print(f" • Data Scale factor    : {meta['scale_factor']}")
    print(f" • Product Fill Value   : {meta['fill_value']}")
    print(f" ─── Geospatial Metadata ───────────────────────────────────────────────────")
    print(f" • Map Reference CRS    : EPSG:{meta['crs_epsg']}")
    print(f" • Resolution Cell Size : X-Spacing: {meta['pixel_spacing_x']:.2f}m | Y-Spacing: {meta['pixel_spacing_y']:.2f}m")
    print(f" • Grid Array Size      : Rows (Y): {meta['rows']} x Columns (X): {meta['cols']}")
    print(f" • Geographic Overlap   : Lat: {meta['lat_min_val']:.4f}°N to {meta['lat_max_val']:.4f}°N")
    print(f"                           Lon: {meta['lon_min_val']:.4f}°E to {meta['lon_max_val']:.4f}°E")
    print(f" • Quality Layers Found : {', '.join(meta['quality_layers'])}")
    print("═"*75 + "\n")

def read_raw_data_matrices(file_path, grid_base_path, freq, pol):
    """Natively reads linear power matrices and coordinate bounding frameworks from HDF5 arrays."""
    with h5py.File(file_path, "r") as f:
        lat_ds = f[f"{grid_base_path}/latitude"]
        lon_ds = f[f"{grid_base_path}/longitude"]
        
        lats = lat_ds[:]
        lons = lon_ds[:]
        lon_2d, lat_2d = np.meshgrid(lons, lats)
            
        power_key = f"{grid_base_path}/radarData/{freq}/sigma0{pol}"
        raw_power = f[power_key][:]
        
        water_path = f"{grid_base_path}/ancillaryData/waterbodyFraction"
        water_fraction = f[water_path][:] if water_path in f else np.zeros(raw_power.shape)
        
    return lat_2d, lon_2d, raw_power, water_fraction
