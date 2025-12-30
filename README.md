# F1 Track Map Generator

A Python-based GUI application that generates Formula 1 track maps using real telemetry data from the [FastF1](https://github.com/theOehrly/Fast-F1) library. The application visualises the track layout and highlights the three distinct sectors (Sector 1, 2, and 3).

## Screenshot
<img width="1489" height="994" alt="image" src="https://github.com/user-attachments/assets/e5cb66f6-eba5-450d-ab43-d07d7befb4da" />


## Features

- **Interactive GUI:** Built with Tkinter for easy race selection.
- **Dynamic Data:** Fetches data for any race from 2021 onwards.
- **Sector Visualisation:**
  - 🟡 **Sector 1:** Yellow
  - 🔵 **Sector 2:** Cyan
  - 🔴 **Sector 3:** Red
- **Caching:** Automatically caches downloaded data to `f1_cache/` for instant subsequent loads.

## Prerequisites

- Python 3.8 or higher
- Internet connection (to download F1 telemetry data)

## Installation

1. **Clone or Download** this repository.
2. **Install Dependencies:**
   Open your terminal/command prompt in the project folder and run:
   ```bash
   pip install -r requirements.txt
   ```
## Usage

1. Run the script:
```bash
python f1_track_map.py
```
(Replace f1_track_map.py with whatever you named your Python file)

2. Select Options:

    - Choose the Year (e.g., 2024).

    - Choose the Race (the list updates automatically based on the year).

    - Choose the Session (FP1, Qualifying, Race, etc.).
      
3. Click **"Draw Track Map"**
   
