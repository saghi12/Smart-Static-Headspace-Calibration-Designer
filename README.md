# ⚗️ Smart Static Headspace Calibration Designer

A GUI desktop application designed for analytical chemists to plan, calculate, and schedule static headspace methanol gas calibration standards for **Drift Tube Ion Mobility Spectrometry (DT-IMS)** and Gas Chromatography (GC-MS/GC-FID).

---

## 🌟 Key Features

* **Physics & Thermodynamics Driven**:
  * Calculates saturation vapor pressure of Methanol ($CH_3OH$) across temperatures using the **Antoine Equation** (NIST parameters).
  * Computes gas concentrations ($mg/L$ and $ppm_v$) using the **Ideal Gas Law** with atmospheric pressure correction.
* **Smart Optimization Engine**:
  * Automatically matches target gas concentrations to physical laboratory glassware (`10 mL` to `2000 mL` vessels) and syringe injection volumes.
  * Formats multi-step injections cleanly (e.g., transfers $> 2.5\text{ mL}$).
* **Block Randomization**:
  * Generates randomized run sequences structured into $N$ replicate blocks to eliminate instrumental drift.
* **Dual Export System**:
  * Exports formatted **Excel (`.xlsx`)** workbooks (with separate standards & sequence sheets) via `openpyxl`, with automatic fallback to structured **CSV (`.csv`)**.
* **Zero External Dependencies**:
  * Built using Python's standard library (`tkinter`), requiring no `pip` installs to launch the core GUI.

---

## 🛠️ Installation & Setup

### Prerequisites
* Python `3.8` or higher installed on your system.

### Running the Application

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/smart-headspace-calibration.git
   cd smart-headspace-calibration
