import tkinter as tk
from tkinter import ttk, messagebox
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.collections import LineCollection
import pandas as pd
import numpy as np
import os

# 1. Setup FastF1 Cache
cache_dir = 'f1_cache'
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

fastf1.Cache.enable_cache(cache_dir)

# 2. Setup Plotting Style
fastf1.plotting.setup_mpl(template='fastf1')

class F1TrackApp:
    def __init__(self, root):
        self.root = root
        self.root.title("F1 Track Map Generator (Sectors Only)")
        self.root.geometry("1000x800")
        
        # --- GUI Layout ---
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Year Selection
        ttk.Label(control_frame, text="Year:").pack(side=tk.LEFT, padx=5)
        self.year_var = tk.StringVar(value="2024")
        self.year_combo = ttk.Combobox(control_frame, textvariable=self.year_var, width=10)
        self.year_combo['values'] = [str(y) for y in range(2021, 2026)]
        self.year_combo.pack(side=tk.LEFT, padx=5)
        self.year_combo.bind("<<ComboboxSelected>>", self.update_races)

        # Race Selection
        ttk.Label(control_frame, text="Race:").pack(side=tk.LEFT, padx=5)
        self.race_var = tk.StringVar()
        self.race_combo = ttk.Combobox(control_frame, textvariable=self.race_var, width=30)
        self.race_combo.pack(side=tk.LEFT, padx=5)
        
        # Session Selection
        ttk.Label(control_frame, text="Session:").pack(side=tk.LEFT, padx=5)
        self.session_var = tk.StringVar(value="Qualifying")
        self.session_combo = ttk.Combobox(control_frame, textvariable=self.session_var, width=15)
        self.session_combo['values'] = ["FP1", "FP2", "FP3", "Qualifying", "Sprint", "Race"]
        self.session_combo.pack(side=tk.LEFT, padx=5)

        # Load Button
        self.btn_load = ttk.Button(control_frame, text="Draw Track Map", command=self.plot_track)
        self.btn_load.pack(side=tk.LEFT, padx=10)
        
        # Status Label
        self.status_lbl = ttk.Label(control_frame, text="Ready", foreground="green")
        self.status_lbl.pack(side=tk.LEFT, padx=10)

        # Plot Area
        self.plot_frame = tk.Frame(self.root)
        self.plot_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.canvas = None

        # Initialize Data
        self.update_races()

    def update_races(self, event=None):
        """Fetch the race schedule for the selected year."""
        year = int(self.year_var.get())
        try:
            schedule = fastf1.get_event_schedule(year)
            # Filter out pre-season testing if needed
            if 'EventFormat' in schedule.columns:
                races = schedule[schedule['EventFormat'] != 'testing']['EventName'].tolist()
            else:
                races = schedule['EventName'].tolist()
                
            self.race_combo['values'] = races
            if races:
                self.race_combo.current(0)
        except Exception as e:
            self.status_lbl.config(text=f"Schedule Error: {e}", foreground="red")

    def plot_track(self):
        """Main logic to load data and draw the map."""
        self.status_lbl.config(text="Loading data... (this may take a minute)", foreground="orange")
        self.root.update()

        year = int(self.year_var.get())
        race = self.race_var.get()
        session_name = self.session_var.get()
        
        # Map nice names to FastF1 session codes
        session_map = {
            "FP1": "FP1", "FP2": "FP2", "FP3": "FP3",
            "Qualifying": "Q", "Sprint": "S", "Race": "R"
        }
        
        try:
            # Load Session
            session = fastf1.get_session(year, race, session_map.get(session_name, "Q"))
            session.load()
            
            # Get Fastest Lap Telemetry
            lap = session.laps.pick_fastest()
            tel = lap.get_telemetry()
            
            # Prepare X, Y data
            x = np.array(tel['X'].values)
            y = np.array(tel['Y'].values)
            
            # --- Logic for Sectors ---
            # Helper to find closest index in telemetry for a given time
            def get_idx(time_val):
                return (tel['SessionTime'] - time_val).abs().idxmin()

            idx_s1 = get_idx(lap['Sector1SessionTime'])
            idx_s2 = get_idx(lap['Sector2SessionTime'])
            
            # Create segments for plotting
            points = np.array([x, y]).T.reshape(-1, 1, 2)
            segments = np.concatenate([points[:-1], points[1:]], axis=1)

            # Create a color array for sectors
            # 0 = S1 (Yellow), 1 = S2 (Cyan), 2 = S3 (Red)
            tel_idx = tel.index
            sector_colors = []
            
            for i in tel_idx[:-1]: 
                if i < idx_s1:
                    sector_colors.append('yellow') # Sector 1
                elif i < idx_s2:
                    sector_colors.append('cyan')   # Sector 2
                else:
                    sector_colors.append('red')    # Sector 3

            # --- Plotting ---
            self.clear_plot()
            fig, ax = plt.subplots(figsize=(8, 6), facecolor='black')
            ax.set_facecolor('black')
            
            # Plot Sectors
            lc_sectors = LineCollection(segments, colors=sector_colors, linewidths=5)
            ax.add_collection(lc_sectors)

            # Formatting
            ax.set_aspect('equal')
            ax.axis('off')
            
            # Title & Legend (Updated to remove DRS reference)
            title_text = f"{year} {race} - {session_name}\nSectors: Yellow (S1), Cyan (S2), Red (S3)"
            ax.set_title(title_text, color='white', fontsize=12)
            
            # Auto scale limits
            ax.autoscale_view()
            
            # Embed in Tkinter
            self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            
            self.status_lbl.config(text="Map Loaded Successfully", foreground="green")

        except Exception as e:
            self.status_lbl.config(text="Error loading data", foreground="red")
            messagebox.showerror("Error", f"Could not load track data.\nDetails: {e}")
            import traceback
            traceback.print_exc()

    def clear_plot(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        plt.close('all')

if __name__ == "__main__":
    root = tk.Tk()
    app = F1TrackApp(root)
    root.mainloop()
