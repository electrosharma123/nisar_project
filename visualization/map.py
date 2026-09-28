# visualization/map.py
"""
Interactive Map Vectorization Layer.
Transforms region analysis arrays into click-responsive map indicators
and automatically forces the map viewport to fit the active cluster geometry.
"""
import folium

def generate_cluster_interactive_map(output_root, filename, df_regions):
    """Drops precise crosshair warning markers over candidate change zones."""
    import os
    
    if df_regions.empty:
        print("⚠️ Region tracking database is empty. Skipping web map generation.")
        return
        
    output_path = os.path.join(output_root, filename)
    
    # Calculate exact geometric bounds of our new active regions
    center_lat = float(df_regions["centroid_lat"].mean())
    center_lon = float(df_regions["centroid_lon"].mean())
    
    # Force map initialization directly over the current coordinates
    m = folium.Map(location=[center_lat, center_lon], zoom_start=9, control_scale=True)
    
    # Drop map crosshairs dynamically
    for _, row in df_regions.iterrows():
        popup_content = f"""
        <div style='font-family: Arial, sans-serif; width: 260px; font-size:12px; line-height:1.4;'>
            <h4 style='margin:0 0 5px 0; color:#c9302c;'>Surface-Change Zone #{int(row['region_id'])}</h4>
            <hr style='margin:4px 0; border:0; border-top:1px solid #ccc;'>
            <b>Coverage Area Extent:</b> {row['area_km2']:.4f} km²<br>
            <b>Mean Intensity Change:</b> {row['mean_change_db']:.2f} dB<br>
            <b>Peak Intensity Spike:</b> +{row['max_change_db']:.2f} dB<br>
            <b>Temporal Trajectory Profile:</b> <span style='color:#c9302c;'>{row['temporal_consistency']}</span><br>
            <b>Dynamic Signal Trend:</b> {row['change_direction']}<br>
            <b>Duration Classification:</b> {row['change_duration']}<br>
            <b>Centroid Coordinates:</b> {row['centroid_lat']:.4f}°N, {row['centroid_lon']:.4f}°E
        </div>
        """
        
        folium.Marker(
            location=[row["centroid_lat"], row["centroid_lon"]],
            popup=folium.Popup(popup_content, max_width=320),
            icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")
        ).add_to(m)
        
    # FORCE FIT: Automatically re-adjust the map view bounds to encompass all pins
    # This prevents the map from freezing or masking pins on regional switches
    points = df_regions[['centroid_lat', 'centroid_lon']].values.tolist()
    m.fit_bounds(points)
        
    m.save(output_path)
    print(f"   🗺️ Interactive spatial mapping vector web layer saved to: '{output_path}'")
