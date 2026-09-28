# spatial/geospatial.py
"""
Production Raster Coordinate Map Writing Engine.
Exports matrices as GeoTIFF files using exact grid transformations.
"""
import os
import numpy as np
import rasterio
from rasterio.transform import from_origin

def export_matrix_to_geotiff(output_root, filename, data_matrix, lat_2d, lon_2d, epsg_code, nodata_val):
    """
    Writes data matrices out as georeferenced rasters, applying 
    the spatial transformation correctly for a north-up layout.
    """
    if not os.path.exists(output_root):
        os.makedirs(output_root, exist_ok=True)
        
    output_path = os.path.join(output_root, filename)
    num_rows, num_cols = data_matrix.shape
    
    lon_min = float(np.min(lon_2d))
    lon_max = float(np.max(lon_2d))
    lat_max = float(np.max(lat_2d))
    
    pixel_width = (lon_max - lon_min) / (num_cols - 1)
    pixel_height = (lat_max - float(np.min(lat_2d))) / (num_rows - 1)
    
    # Establish correct grid layout transform configuration matching north-up mapping requirements
    spatial_transform = from_origin(lon_min, lat_max, pixel_width, pixel_height)
    
    export_array = np.where(np.isfinite(data_matrix), data_matrix, nodata_val)
    export_array = export_array.astype(np.float32)
    
    with rasterio.open(
        output_path, 'w',
        driver='GTiff',
        height=num_rows, width=num_cols,
        count=1, dtype='float32',
        crs=f'EPSG:{epsg_code}',
        transform=spatial_transform,
        nodata=float(nodata_val)
    ) as dst:
        dst.write(export_array, 1)
        
    print(f"   💾 Saved structural data layer raster to: '{output_path}'")
