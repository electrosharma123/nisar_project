# visualization/plots.py
"""
Data Verification and Chart Generation Module.
Plots coordinate grids natively to verify spatial registration.
"""
import os
import numpy as np
import matplotlib.pyplot as plt

def generate_static_scientific_plots(output_root, filename, change_matrix, lat_2d, lon_2d):
    """Plots total temporal change grids to verify spatial alignment."""
    if not os.path.exists(output_root):
        os.makedirs(output_root, exist_ok=True)
        
    output_path = os.path.join(output_root, filename)
    
    plt.figure(figsize=(12, 9), dpi=150)
    
    lon_min, lon_max = float(np.min(lon_2d)), float(np.max(lon_2d))
    lat_min, lat_max = float(np.min(lat_2d)), float(np.max(lat_2d))
    extent_bounds = [lon_min, lon_max, lat_min, lat_max]
    
    img = plt.imshow(change_matrix, cmap="coolwarm", extent=extent_bounds, vmin=-4.0, vmax=4.0)
    
    cbar = plt.colorbar(img, orientation='vertical', shrink=0.8)
    cbar.set_label(r"Radar Backscatter Delta Change Intensity ($\Delta$dB)", fontsize=11)
    
    plt.title("NISAR Multi-Temporal Surface-Change Candidate Map\nStatistical Anomaly Evaluation Model", fontsize=12, pad=12)
    plt.xlabel("Longitude (Degrees East)", fontsize=10)
    plt.ylabel("Latitude (Degrees North)", fontsize=10)
    plt.grid(True, linestyle=":", alpha=0.4, color="black")
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"   📊 Diagnostic data trend plot generated at: '{output_path}'")
