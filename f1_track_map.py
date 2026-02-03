import tkinter as tk
from tkinter import ttk, messagebox
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import pandas as pd
import os

# 1. Setup FastF1 Cache
cache_dir = 'f1_cache'
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)
fastf1.Cache.enable_cache(cache_dir)
fastf1.plotting.setup_mpl(template='fastf1')

class F1TrackApp:
    def __init__(self, root):
        self.root = root
        self.root.title("F1 Solid 3D Track Map")
        self.root.geometry("1100x900")
        
        # --- GUI Layout ---
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Track Selection (Searchable)
        ttk.Label(control_frame, text="Select Track:").pack(side=tk.LEFT, padx=5)
        
        self.track_var = tk.StringVar()
        self.track_combo = ttk.Combobox(control_frame, textvariable=self.track_var, width=30)
        
        self.all_tracks = sorted([
            "Bahrain", "Saudi Arabia", "Australia", "Japan", "China", "Miami",
            "Emilia Romagna", "Monaco", "Canada", "Spain", "Austria", "Great Britain",
            "Hungary", "Belgium", "Netherlands", "Italy", "Azerbaijan", "Singapore",
            "USA", "Mexico", "Brazil", "Las Vegas", "Qatar", "Abu Dhabi",
            "France", "Portugal", "Turkey", "Russia", "Germany", "Hockenheim", "Nurburgring"
        ])
        self.track_combo['values'] = self.all_tracks
        self.track_combo.current(0)
        self.track_combo.pack(side=tk.LEFT, padx=5)
        self.track_combo.bind('<KeyRelease>', self.filter_track_list)
        
        # Load Button
        self.btn_load = ttk.Button(control_frame, text="Generate Solid 3D Map", command=self.plot_track)
        self.btn_load.pack(side=tk.LEFT, padx=10)
        
        # Status Label
        self.status_lbl = ttk.Label(control_frame, text="Ready", foreground="white")
        self.status_lbl.pack(side=tk.LEFT, padx=10)

        # Plot Frame
        self.plot_frame = tk.Frame(self.root, bg='black')
        self.plot_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        self.canvas = None
        self.toolbar = None

    def filter_track_list(self, event):
        typed_text = self.track_var.get()
        if typed_text == '':
            data = self.all_tracks
        else:
            data = [item for item in self.all_tracks if typed_text.lower() in item.lower()]
        self.track_combo['values'] = data

    def plot_track(self):
        track_name = self.track_var.get()
        self.status_lbl.config(text=f"Searching for {track_name}...", foreground="orange")
        self.root.update()

        # --- 1. Smart Session Loader ---
        session = None
        found_year = None
        
        for year in range(2025, 2018, -1):
            try:
                self.status_lbl.config(text=f"Checking {year}...", foreground="orange")
                self.root.update()
                
                temp_session = fastf1.get_session(year, track_name, 'Q')
                if temp_session.event.EventDate.year <= 2025: 
                    temp_session.load(telemetry=True, laps=True, weather=False, messages=False)
                    if len(temp_session.laps) > 0:
                        session = temp_session
                        found_year = year
                        break
            except Exception:
                continue 

        if not session:
            self.status_lbl.config(text=f"Not found: {track_name}", foreground="red")
            messagebox.showerror("Error", f"Could not find data for {track_name}.")
            return

        self.status_lbl.config(text=f"Processing {track_name} geometry...", foreground="cyan")
        self.root.update()

        try:
            lap = session.laps.pick_fastest()
            full_tel = lap.get_telemetry()
            
            # --- 2. Calculate Geometry ---
            step = 5 
            tel = full_tel.iloc[::step].reset_index(drop=True)

            x = np.array(tel['X'].values)
            y = np.array(tel['Y'].values)
            z = np.array(tel['Z'].values)

            # Close the loop manually to ensure the polygon is watertight
            # We append the first point to the end of the arrays
            x = np.append(x, x[0])
            y = np.append(y, y[0])
            z = np.append(z, z[0])

            # Gradient Calculations
            dx = np.gradient(x)
            dy = np.gradient(y)
            len_vec = np.sqrt(dx**2 + dy**2)
            len_vec[len_vec == 0] = 1.0 
            nx = -dy / len_vec
            ny = dx / len_vec
            
            track_width = 250 
            track_thickness = 40
            
            # Create the 4 rails of the ribbon
            x_left = x + nx * track_width
            y_left = y + ny * track_width
            x_right = x - nx * track_width
            y_right = y - ny * track_width
            
            z_top = z
            z_bottom = z - track_thickness

            # --- 3. Build Solid Polygons ---
            verts = []
            colors = []
            
            # Sector logic needs to account for the loop closure (len(x) changed)
            def get_idx(time_val): return (tel['SessionTime'] - time_val).abs().idxmin()
            idx_s1 = get_idx(lap['Sector1SessionTime'])
            idx_s2 = get_idx(lap['Sector2SessionTime'])

            for i in range(len(x) - 1):
                # Handle Sector Colors
                # If we are at the appended closing point, use the last known color (S3)
                if i >= len(tel): 
                    c = 'red' 
                elif i < idx_s1: c = 'yellow'
                elif i < idx_s2: c = 'cyan'
                else: c = 'red'

                wall_color = self.darken_color(c)

                # 1. TOP FACE (Road)
                verts.append([
                    (x_left[i], y_left[i], z_top[i]),
                    (x_right[i], y_right[i], z_top[i]),
                    (x_right[i+1], y_right[i+1], z_top[i+1]),
                    (x_left[i+1], y_left[i+1], z_top[i+1])
                ])
                colors.append(c)
                
                # 2. BOTTOM FACE (Floor) - This was missing!
                verts.append([
                    (x_left[i], y_left[i], z_bottom[i]),
                    (x_right[i], y_right[i], z_bottom[i]),
                    (x_right[i+1], y_right[i+1], z_bottom[i+1]),
                    (x_left[i+1], y_left[i+1], z_bottom[i+1])
                ])
                colors.append(wall_color) # Make bottom dark like walls
                
                # 3. LEFT WALL
                verts.append([
                    (x_left[i], y_left[i], z_top[i]),
                    (x_left[i+1], y_left[i+1], z_top[i+1]),
                    (x_left[i+1], y_left[i+1], z_bottom[i+1]),
                    (x_left[i], y_left[i], z_bottom[i])
                ])
                colors.append(wall_color)

                # 4. RIGHT WALL
                verts.append([
                    (x_right[i], y_right[i], z_top[i]),
                    (x_right[i+1], y_right[i+1], z_top[i+1]),
                    (x_right[i+1], y_right[i+1], z_bottom[i+1]),
                    (x_right[i], y_right[i], z_bottom[i])
                ])
                colors.append(wall_color)

            # --- 4. Plotting ---
            self.clear_plot()
            fig = plt.figure(figsize=(8, 6), facecolor='black')
            ax = fig.add_subplot(111, projection='3d')
            ax.set_facecolor('black')
            ax.axis('off')
            ax.grid(False)

            # Add Track Mesh
            poly = Poly3DCollection(verts, facecolors=colors, edgecolors='none', alpha=1)
            ax.add_collection3d(poly)

            # --- 5. Add Corner Labels ---
            circuit_info = session.get_circuit_info()
            if circuit_info is not None:
                for _, corner in circuit_info.corners.iterrows():
                    txt = str(corner['Number'])
                    dist = corner['Distance']
                    idx = (full_tel['Distance'] - dist).abs().idxmin()
                    cx = full_tel.loc[idx, 'X']
                    cy = full_tel.loc[idx, 'Y']
                    cz = full_tel.loc[idx, 'Z']
                    ax.text(cx, cy, cz + 150, txt, color='white', fontsize=9, 
                            fontweight='bold', ha='center', va='center')

            # --- 6. Set Limits & Aspect ---
            ax.set_xlim(x.min(), x.max())
            ax.set_ylim(y.min(), y.max())
            ax.set_zlim(z_bottom.min(), z_top.max())
            
            x_range = x.max() - x.min()
            y_range = y.max() - y.min()
            max_range = max(x_range, y_range)
            ax.set_box_aspect((x_range/max_range, y_range/max_range, 0.2))

            ax.set_title(f"{track_name} ({found_year})", color='white')
            
            self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
            self.toolbar.update()
            
            self.status_lbl.config(text=f"Loaded {track_name}", foreground="green")

        except Exception as e:
            self.status_lbl.config(text="Error", foreground="red")
            messagebox.showerror("Error", str(e))
            import traceback
            traceback.print_exc()

    def darken_color(self, color_name):
        mapping = {'yellow': '#AA8800', 'cyan': '#008888', 'red': '#880000'}
        return mapping.get(color_name, 'gray')

    def clear_plot(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        if self.toolbar:
            self.toolbar.destroy()
            self.toolbar = None
        plt.close('all')

if __name__ == "__main__":
    root = tk.Tk()
    app = F1TrackApp(root)
    root.mainloop()
