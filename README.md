# Smart-Static-Headspace-Calibration-Designer
App that calculates methanol vapor concentrations in sealed headspace vials using the Antoine equation, and the Ideal Gas Law. It brute‑forces vial size and injection volume to match target levels, then outputs calibration tables, randomized run orders, and CSV export via a dark GUI.
## License
Free to use for any purpose; modification and derivative works are prohibited without the author’s written permission (see LICENSE)

What is this?
Calibrating a DT-IMS instrument for trace methanol detection requires a series of precisely known gas-phase standards spanning several orders of magnitude in concentration. Preparing these manually — juggling vapor pressures, vessel volumes, syringe sizes, and randomized run orders — is tedious and error-prone.

This tool automates the entire process. Enter your lab conditions and target concentrations; the app calculates the exact injection volumes you need, picks the best vessel for each standard, and hands you a ready-to-run measurement sequence — all from a clean desktop GUI.

No spreadsheets. No guesswork.

The Science
Static headspace standards work by injecting a known volume of saturated methanol vapor from a sealed vial into a larger measurement vessel. The gas-phase concentration in that vessel is then:

C_actual = C_headspace × (V_injection / V_vessel)
Getting C_headspace right is the critical step. This tool calculates it using:

Antoine Equation — gives the saturation vapor pressure P* of methanol at your lab temperature
Raoult's Law — corrects for diluted stock solutions: P_MeOH = x_MeOH × P*
Ideal Gas Law — converts vapor pressure to a mass concentration (mg/L)
Lab pressure correction — accounts for deviations from standard atmospheric pressure
⚠️ Raoult's Law is ideal. Methanol–water mixtures show positive deviations, so actual headspace concentrations can be 1.5–2× higher than predicted at low mole fractions. Use dilute solutions with caution.

Features
🔢 Smart optimization — brute-forces every 
(injection volume, vessel size)
 combo to find the closest achievable concentration to each target, preferring minimal single-step injections
🧪 Stock solution support — enter your methanol purity (% v/v) and the app converts it to a mole fraction via density-corrected stoichiometry
🌡️ Lab condition corrections — temperature and pressure inputs ensure your standards are accurate for your actual lab environment
🔀 Block randomization — standards are automatically arranged into replicate blocks in random order to prevent systematic measurement drift
⏱️ Time estimation — calculates total experiment duration based on your analysis time per run
📤 CSV export — exports the full run sequence with a metadata header (conditions, headspace concentration, timestamp)
🎨 Dark-themed GUI — clean, readable desktop interface built with standard Python tkinter — no installation required
How It Works
User Inputs
    │
    ▼
Antoine Eq. → Raoult's Law → Ideal Gas Law
    │         (calculates headspace concentration)
    ▼
Optimization Loop
    │  For each target concentration:
    │  Try all vessel sizes × all injection volumes
    │  Score = |actual − target| + tiny preference for smaller injections
    │         + penalty for two-step injections (> 2.5 mL)
    │  → Pick the winner
    ▼
Block-Randomized Run Sequence
    │  Every standard appears once per block, in random order
    ▼
Display in GUI  →  Export as CSV
Code Structure
The code is organized into four clean layers:

Layer	Lines	What it does
Chemistry	42–137	Antoine equation, Raoult's Law, Ideal Gas Law, unit conversions
Optimization	170–280	Brute-forces all (vessel × injection) combos, scores and picks the best fit per target
Randomization	287–363	Block-randomized run sequence + CSV export
GUI	370–900	Tkinter/ttk dark-themed interface — inputs, results tables, buttons
Key calculation chain
Antoine Eq.  →  Raoult's Law  →  Ideal Gas Law  →  C_headspace [mg/L]
     ↓
C_actual = C_headspace × (V_injection / V_vessel)
     ↓
Score = |actual − target| + 0.001 × V_inj + (5.0 if V_inj > 2.5 mL)
     ↓
Block-randomized run sequence  →  CSV export
Raoult's Law handles diluted stock solutions via a density-corrected mole fraction
Pressure correction adjusts for labs above or below sea level
Step penalty discourages two-step injections (> 2.5 mL) unless no single-step option can reach the target
Block randomization ensures instrument drift affects all concentration levels equally
Requirements
Python ≥ 3.8
No external packages — pure stdlib (tkinter, math, 
csv
, random, dataclasses)
Usage
bash
python "calibration generator.py"
Input fields
Field	Description
Lab Temperature (°C)	Room temperature where headspace vials are equilibrated
Lab Pressure (mbar)	Ambient atmospheric pressure
Syringe Resolution (mL)	Smallest volume increment your syringe can reliably deliver
Replicates / Blocks	Number of complete repetitions of the calibration set
Analysis Time per Run (s)	Duration of a single IMS measurement
Methanol Purity (% v/v)	Purity of your stock solution (100 = neat methanol)
Liquid Volume in Vial (mL)	Volume of liquid methanol/solution in the sealed source vial
Source Vial Volume (mL)	Total volume of the sealed source vial
Target Concentrations (mg/L)	Comma-separated list of desired gas-phase concentrations
Available vessel sizes
20, 50, 100, 250, 500, 1000, 2000 mL

Example
Settings: 25 °C · 1013 mbar · 0.05 mL syringe · neat methanol
Targets: 0.5, 1, 2, 5, 10, 20, 35, 50 mg/L

The app instantly returns the optimal vessel + injection volume for each level, arranges them into a randomized block sequence, and estimates your total experiment time.

Application Domain
This tool was built for Drift Tube Ion Mobility Spectrometry (DT-IMS) calibration workflows, but the underlying approach (headspace dilution standards) is applicable to any analytical technique that samples from a gas phase — including GC-FID, GC-MS, and photoionization detectors.
