# ⚗️ Smart Static Headspace Calibration Designer

A GUI desktop application designed for analytical chemists to plan, calculate, and schedule static headspace methanol gas calibration standards for **Drift Tube Ion Mobility Spectrometry (DT-IMS)** and Gas Chromatography (GC-MS/GC-FID).

---

## 🌟 Key Features

* **Physics & Thermodynamics Driven**
  * Calculates saturation vapor pressure of methanol ($CH_3OH$) across temperatures using the **Antoine Equation** (NIST parameters).
  * Computes gas concentrations ($mg/L$ and $ppm_v$) using the **Ideal Gas Law** with atmospheric pressure correction.
* **Smart Optimization Engine**
  * Automatically matches target gas concentrations to physical laboratory glassware (`10 mL` to `2000 mL` vessels) and syringe injection volumes.
  * Formats multi-step injections cleanly (e.g., transfers $> 2.5\text{ mL}$).
* **Block Randomization**
  * Generates randomized run sequences structured into $N$ replicate blocks to eliminate instrumental drift.
* **Dual Export System**
  * Exports formatted **Excel (`.xlsx`)** workbooks (with separate standards & sequence sheets) via `openpyxl`, with automatic fallback to structured **CSV (`.csv`)**.
* **Zero External Dependencies**
  * Built using Python's standard library (`tkinter`), requiring no `pip` installs to launch the core GUI.

---

## 🛠️ Installation & Setup

### Prerequisites

* Python `3.8` or higher installed on your system.

### Running the Application

**Clone the repository**:

```bash
git clone https://github.com/your-username/smart-headspace-calibration.git
cd smart-headspace-calibration
```

---

## ⚖️ On Raoult's Law

* The code includes a `mole_fraction` parameter in the headspace calculation.
* This is always set to **1.0** — the source vial is assumed to be **neat methanol**, treating water as an impurity.

> **Note:** methanol–water mixtures show strong positive deviations from ideal Raoult's law.

---

## 📂 Code Layout

```
calibration_generator.py
│
├── Antoine equation & ideal gas law       antoine_vapor_pressure_mmhg()
│                                          headspace_concentration_mg_per_l()
│                                          headspace_concentration_ppmv()
│                                          mg_l_to_ppmv()
│
├── Optimization                           find_best_combination()
│   Finds best (V_inj, vessel) pair        design_calibration()
│   for each target concentration
│
├── Block randomization                    generate_run_sequence()
│
├── Export                                 export_xlsx()  /  export_csv()
│
└── GUI (tkinter)                          CalibrationDesignerApp
```

---

## 🧪 Computational Methodology

**1. Antoine Vapor Pressure Equation**

$$ \log_{10}(P^*) = A - \frac{B}{T + C} $$

Where $A = 8.08097$, $B = 1582.27$, $C = 239.7$

**2. Headspace Concentration ($mg/L$)**

$$ C_{hs} = \frac{P_{MeOH} \cdot M_{MeOH}}{R \cdot T_{K}} \times \left(\frac{P_{std}}{P_{lab}}\right) $$



---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.
