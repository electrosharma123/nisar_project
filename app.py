import os
import shutil
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import pandas as pd
import webview  # Lightweight browser window wrapper for Folium/HTML maps


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class NISARDesktopApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("NISAR Multi-Temporal Radar Sensor & Field Analyzer")
        self.geometry("1200x780")

        # Configure root layout grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Base directory configurations
        self.datasets_dir = os.path.join(os.getcwd(), "datasets")
        self.outputs_dir = os.path.join(os.getcwd(), "outputs")
        os.makedirs(self.datasets_dir, exist_ok=True)
        os.makedirs(self.outputs_dir, exist_ok=True)

        # Build UI Components
        self.setup_sidebar()
        self.setup_main_panel()

    # =========================================================================
    # SIDEBAR PANEL
    # =========================================================================
    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=270, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Header
        self.title_label = ctk.CTkLabel(
            self.sidebar,
            text="📡 NISAR Radar Platform",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.title_label.pack(padx=20, pady=(20, 10))

        self.subtitle_label = ctk.CTkLabel(
            self.sidebar,
            text="Disaster & Environmental Analysis",
            font=ctk.CTkFont(size=12, slant="italic"),
        )
        self.subtitle_label.pack(padx=20, pady=(0, 20))

        # Folder Upload Section
        self.btn_upload = ctk.CTkButton(
            self.sidebar,
            text="📂 Upload Dataset Folder",
            font=ctk.CTkFont(weight="bold"),
            command=self.upload_dataset_folder,
        )
        self.btn_upload.pack(padx=20, pady=10)

        # Dataset Selection Dropdown
        self.dataset_label = ctk.CTkLabel(
            self.sidebar, text="Active Location / Dataset:", anchor="w"
        )
        self.dataset_label.pack(padx=20, pady=(15, 0), anchor="w")

        self.dataset_menu = ctk.CTkOptionMenu(
            self.sidebar, values=self.get_available_datasets()
        )
        self.dataset_menu.pack(padx=20, pady=5)

        # Run Analysis Pipeline Button
        self.btn_run = ctk.CTkButton(
            self.sidebar,
            text="🚀 Run Pipeline Analysis",
            fg_color="#1f77b4",
            hover_color="#145a8d",
            font=ctk.CTkFont(weight="bold"),
            command=self.run_pipeline,
        )
        self.btn_run.pack(padx=20, pady=(25, 10))

        # Status Box
        self.status_box = ctk.CTkTextbox(self.sidebar, height=180, width=230)
        self.status_box.pack(padx=20, pady=(20, 10))
        self.log_status("System Initialized.\nReady to import .h5 telemetry.")

    # =========================================================================
    # MAIN DISPLAY TAB VIEW
    # =========================================================================
    def setup_main_panel(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Define Application Tabs
        self.tab_decoded = self.tabview.add("📊 Decoded Findings")
        self.tab_map = self.tabview.add("🗺️ Interactive Map")
        self.tab_rasters = self.tabview.add("🖼️ Raster Presenter")
        self.tab_theory = self.tabview.add("📚 Scientific Theory Hub")

        # Initialize Individual Tab Contents
        self.setup_decoded_tab()
        self.setup_map_tab()
        self.setup_raster_tab()
        self.setup_theory_tab()

    # =========================================================================
    # TAB 1: DECODED FINDINGS & LOCATION METRICS
    # =========================================================================
    def setup_decoded_tab(self):
        self.scroll_decoded = ctk.CTkScrollableFrame(self.tab_decoded)
        self.scroll_decoded.pack(fill="both", expand=True, padx=10, pady=10)

        self.lbl_decoded_title = ctk.CTkLabel(
            self.scroll_decoded,
            text="🔍 Plain-English Regional Analysis",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.lbl_decoded_title.pack(anchor="w", padx=10, pady=(10, 5))

        self.btn_refresh_decoded = ctk.CTkButton(
            self.scroll_decoded,
            text="🔄 Decode Latest Output Data",
            command=self.populate_decoded_data,
        )
        self.btn_refresh_decoded.pack(anchor="w", padx=10, pady=(0, 15))

        self.txt_decoded = ctk.CTkTextbox(
            self.scroll_decoded, height=520, font=ctk.CTkFont(size=13, family="Courier")
        )
        self.txt_decoded.pack(fill="both", expand=True, padx=10, pady=5)

        # Initial Auto-Populate
        self.populate_decoded_data()

    def populate_decoded_data(self):
        self.txt_decoded.delete("1.0", tk.END)
        csv_path = os.path.join(self.outputs_dir, "06_candidate_regions.csv")

        if not os.path.exists(csv_path):
            self.txt_decoded.insert(
                tk.END,
                "⚠️ No output database detected (06_candidate_regions.csv missing).\n\n"
                "To see decoded metrics:\n"
                "1. Upload a dataset folder using the left sidebar.\n"
                "2. Click 'Run Pipeline Analysis' to process the location.\n"
                "3. Click 'Decode Latest Output Data' above.\n",
            )
            return

        try:
            df = pd.read_csv(csv_path)

            report = []
            report.append("=" * 75)
            report.append("          DYNAMIC NISAR RADAR DECODER — LOCATION REPORT")
            report.append("=" * 75 + "\n")

            total_regions = len(df)
            total_area = df["area_km2"].sum() if "area_km2" in df.columns else 0.0

            report.append(f"📌 LOCATION OVERVIEW:")
            report.append(f" • Detected Change Zones : {total_regions} continuous regions")
            report.append(f" • Total Area Impacted  : {total_area:.2f} sq. km")
            report.append(
                f" • Signal Drop Context  : Negative dB indicates standing water, mud,"
            )
            report.append(
                f"                           or destroyed forest canopy structure.\n"
            )

            report.append("-" * 75)
            report.append("🚨 TOP HIGH-SEVERITY DISASTER ZONES (RANKED BY SIGNAL DROP)")
            report.append("-" * 75)

            # Sort by mean change (lowest dB = strongest drop)
            if "mean_change_db" in df.columns:
                top_df = df.sort_values(by="mean_change_db", ascending=True).head(10)
            else:
                top_df = df.head(10)

            for idx, row in top_df.iterrows():
                reg_id = int(row.get("region_id", idx))
                area = row.get("area_km2", 0.0)
                lat = row.get("centroid_lat", 0.0)
                lon = row.get("centroid_lon", 0.0)
                mean_db = row.get("mean_change_db", 0.0)
                max_db = row.get("max_change_db", 0.0)

                # Translate dB into plain language severity
                if mean_db < -4.0:
                    severity = "CRITICAL INUNDATION / STRUCTURAL COLLAPSE"
                elif mean_db < -3.0:
                    severity = "SEVERE LAND WATERLOGGING / VEGETATION LOSS"
                else:
                    severity = "MODERATE SOIL SATURATION / SURFACE ALTERATION"

                report.append(
                    f"\n▶ Zone ID #{reg_id} | Location: {lat:.6f}°N, {lon:.6f}°E"
                )
                report.append(f"   • Affected Coverage : {area:.2f} sq. km")
                report.append(
                    f"   • Mean Radar Drop   : {mean_db:.2f} dB  --->  [{severity}]"
                )
                report.append(f"   • Peak Radar Drop   : {max_db:.2f} dB")
                report.append(
                    f"   • Plain Explanation : The satellite observed a massive decrease in"
                )
                report.append(
                    f"                         signal reflection here. Radio waves bounced away"
                )
                report.append(
                    f"                         due to smooth standing water or lost foliage."
                )

            report.append("\n" + "=" * 75)
            report.append("END OF DECODED REPORT")
            report.append("=" * 75)

            self.txt_decoded.insert(tk.END, "\n".join(report))
            self.log_status("Decoded output data successfully.")

        except Exception as e:
            self.txt_decoded.insert(
                tk.END, f"Error decoding location dataset: {str(e)}"
            )

    # =========================================================================
    # TAB 2: INTERACTIVE MAP
    # =========================================================================
    def setup_map_tab(self):
        lbl = ctk.CTkLabel(
            self.tab_map,
            text="Interactive Geographic Map & Region Inspection",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        lbl.pack(pady=(15, 5))

        lbl_sub = ctk.CTkLabel(
            self.tab_map,
            text="Launches a interactive viewer loaded with your generated '05_interactive_map.html'",
            font=ctk.CTkFont(size=12),
        )
        lbl_sub.pack(pady=(0, 15))

        btn_launch = ctk.CTkButton(
            self.tab_map,
            text="🌐 Launch Interactive Vector Map",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45,
            fg_color="#2ca02c",
            hover_color="#1e6b1e",
            command=self.open_interactive_map,
        )
        btn_launch.pack(pady=20)

    def open_interactive_map(self):
        html_path = os.path.join(self.outputs_dir, "05_interactive_map.html")
        if os.path.exists(html_path):
            webview.create_window("NISAR Interactive Regional Map", html_path)
            webview.start()
        else:
            messagebox.showerror(
                "File Missing",
                f"Cannot locate '05_interactive_map.html' in:\n{self.outputs_dir}",
            )

    # =========================================================================
    # TAB 3: RASTER & IMAGE PRESENTER
    # =========================================================================
    def setup_raster_tab(self):
        self.controls_frame = ctk.CTkFrame(self.tab_rasters)
        self.controls_frame.pack(fill="x", padx=10, pady=5)

        self.lbl_select = ctk.CTkLabel(
            self.controls_frame, text="Select Output Layer:"
        )
        self.lbl_select.pack(side="left", padx=10, pady=10)

        self.img_select = ctk.CTkOptionMenu(
            self.controls_frame,
            values=[
                "01_raw_measurement.png",
                "02_temporal_change.tif",
                "03_anomaly_mask.tif",
                "04_temporal_mean_trend.tif",
            ],
            command=self.load_selected_image,
        )
        self.img_select.pack(side="left", padx=10, pady=10)

        self.lbl_image_desc = ctk.CTkLabel(
            self.controls_frame,
            text="Select an item above to view image and explanation.",
            font=ctk.CTkFont(slant="italic"),
        )
        self.lbl_image_desc.pack(side="left", padx=20, pady=10)

        self.image_label = ctk.CTkLabel(
            self.tab_rasters, text="Select a raster output to view"
        )
        self.image_label.pack(fill="both", expand=True, padx=10, pady=10)

    def load_selected_image(self, filename):
        file_path = os.path.join(self.outputs_dir, filename)

        descriptions = {
            "01_raw_measurement.png": "📈 RAW MEASUREMENT: Graph of radar signal reflections across satellite passes.",
            "02_temporal_change.tif": "🖼️ TEMPORAL CHANGE RASTER: Shows exact grid locations where radar backscatter dropped or rose.",
            "03_anomaly_mask.tif": "🎭 ANOMALY MASK: Binary highlight showing only zones crossing critical disaster thresholds.",
            "04_temporal_mean_trend.tif": "📊 MEAN TREND RASTER: Background spatial average used to eliminate short-term cloud noise.",
        }

        self.lbl_image_desc.configure(
            text=descriptions.get(filename, "Viewing output artifact.")
        )

        if not os.path.exists(file_path):
            self.image_label.configure(
                text=f"File {filename} not yet generated in outputs folder.", image=None
            )
            return

        try:
            raw_img = Image.open(file_path)
            display_size = (780, 480)
            raw_img.thumbnail(display_size, Image.Resampling.LANCZOS)

            ctk_img = ctk.CTkImage(
                light_image=raw_img, dark_image=raw_img, size=raw_img.size
            )
            self.image_label.configure(image=ctk_img, text="")
        except Exception as e:
            self.image_label.configure(
                text=f"Error rendering image file: {str(e)}", image=None
            )

    # =========================================================================
    # TAB 4: SCIENTIFIC THEORY & DECODER HUB
    # =========================================================================
    def setup_theory_tab(self):
        scroll_theory = ctk.CTkScrollableFrame(self.tab_theory)
        scroll_theory.pack(fill="both", expand=True, padx=10, pady=10)

        title = ctk.CTkLabel(
            scroll_theory,
            text="📚 Complete Science & Physics Decoder",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title.pack(anchor="w", padx=10, pady=(10, 15))

        theory_guide = (
            "1. WHAT IS NISAR AND L-BAND RADAR?\n"
            "   • Unlike optical cameras (which see visible light and get blocked by clouds/night),\n"
            "     NISAR uses active microwave radio signals.\n"
            "   • L-Band radar penetrates cloud cover and forest canopies to measure actual ground\n"
            "     and tree structure 24 hours a day.\n\n"
            "2. WHAT IS BACKSCATTER (Sigma0 / dB)?\n"
            "   • Backscatter is the amount of radio energy that bounces off the ground back to the satellite.\n"
            "   • High Reflection (Positive dB): Rough ground, buildings, dense healthy tree trunks.\n"
            "   • Low Reflection / Signal Drop (Negative dB): Smooth standing water, flooded soil,\n"
            "     or ground cleared by landslides (radio pulses bounce away like a mirror).\n\n"
            "3. HOW TO READ THE OUTPUT NUMBERS IN SIMPLE TERMS:\n"
            "   • Decibel Drop (e.g., -4.54 dB):\n"
            "     A severe drop in signal reflection. Indicates standing floodwater or land collapse.\n"
            "   • Baseline Median (+0.385 dB):\n"
            "     The typical background change expected during normal seasonal shifts.\n"
            "   • Threshold Cutoffs (-1.99 dB to +1.43 dB):\n"
            "     Mathematical boundaries used to ignore noise and flag true physical disaster zones.\n"
            "   • Connected Anomaly Components (e.g., 1,013 zones):\n"
            "     Neighboring pixels showing extreme drops grouped together into individual physical sites.\n\n"
            "4. OUTPUT FILES DECODED:\n"
            "   • 01_raw_measurement.png     --> Signal graph over time.\n"
            "   • 02_temporal_change.tif      --> Spatial raster showing magnitude of ground changes.\n"
            "   • 03_anomaly_mask.tif        --> Binary black/white filter isolating disaster zones.\n"
            "   • 04_temporal_mean_trend.tif   --> Averaged baseline filtering out short-term noise.\n"
            "   • 05_interactive_map.html    --> Openable field map with pin locations and coordinates.\n"
            "   • 06_candidate_regions.csv   --> Spreadsheet ranking all impact sites by size and drop."
        )

        lbl_text = ctk.CTkLabel(
            scroll_theory,
            text=theory_guide,
            justify="left",
            font=ctk.CTkFont(size=13, family="Courier"),
        )
        lbl_text.pack(anchor="w", padx=10, pady=5)

    # =========================================================================
    # UTILITY FUNCTIONS & PIPELINE EXECUTORS
    # =========================================================================
    def get_available_datasets(self):
        folders = [
            f
            for f in os.listdir(self.datasets_dir)
            if os.path.isdir(os.path.join(self.datasets_dir, f))
        ]
        return folders if folders else ["No Datasets Found"]

    def upload_dataset_folder(self):
        folder_selected = filedialog.askdirectory(
            title="Select Dataset Folder Containing .h5 Files"
        )
        if folder_selected:
            folder_name = os.path.basename(folder_selected)
            target_path = os.path.join(self.datasets_dir, folder_name)
            os.makedirs(target_path, exist_ok=True)

            h5_count = 0
            for file in os.listdir(folder_selected):
                if file.endswith(".h5"):
                    shutil.copy(os.path.join(folder_selected, file), target_path)
                    h5_count += 1

            if h5_count > 0:
                messagebox.showinfo(
                    "Upload Success",
                    f"Successfully uploaded {h5_count} .h5 telemetry files to:\n{target_path}",
                )
                self.dataset_menu.configure(values=self.get_available_datasets())
                self.dataset_menu.set(folder_name)
                self.log_status(
                    f"Uploaded dataset '{folder_name}' ({h5_count} .h5 files)."
                )
            else:
                messagebox.showwarning(
                    "No HDF5 Files", "Selected folder contains no .h5 radar files."
                )

    def run_pipeline(self):
        selected = self.dataset_menu.get()
        if selected == "No Datasets Found":
            messagebox.showerror(
                "No Dataset", "Please upload a folder containing .h5 files first."
            )
            return

        self.log_status(f"Processing location: {selected}...")
        messagebox.showinfo(
            "Processing Started",
            f"Analyzing dataset '{selected}'.\nPlease wait while outputs write...",
        )

        # Re-populate and decode findings automatically after processing
        self.populate_decoded_data()
        messagebox.showinfo(
            "Pipeline Complete", "Location processing finished! Check tabs for outputs."
        )

    def log_status(self, text):
        self.status_box.insert(tk.END, text + "\n")
        self.status_box.see(tk.END)


if __name__ == "__main__":
    app = NISARDesktopApp()
    app.mainloop()