# processing/temporal.py
"""
Multi-Temporal Data Cube Stacking and Virtual Profile Sensor Tracking Engine.
Protects intermediate timeline data and logs rolling pairwise change matrix trends.
"""
import numpy as np
import warnings

def build_time_series_cube(db_stack, dates_list):
    """Encapsulates timelines and data arrays into a structured tracking dictionary."""
    return {
        "dates": dates_list,
        "cube": np.array(db_stack, dtype=np.float32)
    }

def analyze_vector_virtual_sensor_trends(time_series):
    """
    Analyzes pixel parameters across the complete time series to map trends
    and log variance indicators without throwing away intermediate data.
    """
    cube = time_series["cube"]
    dates = time_series["dates"]
    num_dates = len(dates)
    
    temporal_package = {
        "pairwise": {},
        "statistics": {}
    }
    
    print("🧮 Processing multi-temporal rolling steps and variance properties...")
    
    # 1. Calculate Pairwise Incremental Phase Changes
    for i in range(num_dates - 1):
        lbl = f"change_{dates[i+1]}_minus_{dates[i]}"
        temporal_package["pairwise"][lbl] = cube[i+1] - cube[i]
        
    # 2. Calculate Total Excursion Baseline Reference Change
    lbl_total = f"change_{dates[-1]}_minus_{dates[0]}"
    temporal_package["pairwise"][lbl_total] = cube[-1] - cube[0]
    
    # 3. Vector Parameter Mapping Across the Time Series
    # Suppress mathematical warnings caused by empty space/NaN values on the data edge margins
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=RuntimeWarning, message='Mean of empty slice')
        warnings.filterwarnings('ignore', category=RuntimeWarning, message='Degrees of freedom <= 0')
        warnings.filterwarnings('ignore', category=RuntimeWarning, message='All-NaN slice encountered')
        
        temporal_package["statistics"]["temporal_mean"] = np.nanmean(cube, axis=0)
        temporal_package["statistics"]["temporal_std"] = np.nanstd(cube, axis=0)
        
        max_arr = np.nanmax(cube, axis=0)
        min_arr = np.nanmin(cube, axis=0)
        temporal_package["statistics"]["max_absolute_excursion"] = max_arr - min_arr
        
        # Calculate Observed Temporal Slope (linear derivative trend vector over available dates)
        # Formula uses data index mapping intervals as the time proxy
        x_steps = np.arange(num_dates)
        
        def calculate_slope_vector(pixel_axis):
            if np.any(np.isnan(pixel_axis)) or np.all(pixel_axis == 0):
                return np.nan
            return np.polyfit(x_steps, pixel_axis, 1)[0]
            
        slope_map = np.apply_along_axis(calculate_slope_vector, axis=0, arr=cube)
        temporal_package["statistics"]["observed_temporal_slope"] = slope_map
        
    return temporal_package
