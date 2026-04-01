# Smart-Static-Headspace-Calibration-Designer
App that calculates methanol vapor concentrations in sealed headspace vials using the Antoine equation, and the Ideal Gas Law. It brute‑forces vial size and injection volume to match target levels, then outputs calibration tables, randomized run orders, and CSV export via a dark GUI.
## License
Free to use for any purpose; modification and derivative works are prohibited without the author’s written permission (see LICENSE)


> **Precision methanol gas standards for Drift Tube Ion Mobility Spectrometry — designed in seconds, not hours.**

---

## What is this?

Calibrating a DT-IMS instrument for trace methanol detection requires a series of precisely known gas-phase standards spanning several orders of magnitude in concentration. Preparing these manually — juggling vapor pressures, vessel volumes, syringe sizes, and randomized run orders — is tedious and error-prone.

**This tool automates the entire process.** Enter your lab conditions and target concentrations; the app calculates the exact injection volumes you need, picks the best vessel for each standard, and hands you a ready-to-run measurement sequence — all from a clean desktop GUI.

No spreadsheets. No guesswork.

---

C_actual = C_headspace × (V_injection / V_vessel)


Getting `C_headspace` right is the critical step. This tool calculates it using:

1. **Antoine Equation** — saturation vapor pressure of methanol at your lab temperature
2. **Raoult's Law** — corrects for diluted stock solutions: `P_MeOH = x_MeOH × P*`
3. **Ideal Gas Law** — converts vapor pressure to mg/L
4. **Lab pressure correction** — accounts for deviations from standard atmospheric pressure

> ⚠️ Raoult's Law is ideal. Methanol–water mixtures show positive deviations, so actual headspace concentrations can be 1.5–2× higher than predicted at low mole fractions.

---

## Features

- 🔢 **Smart optimization** — finds the closest achievable concentration to each target by testing every vessel × injection combination
- 🧪 **Stock solution support** — enter purity (% v/v) and the app converts it to mole fraction automatically
- 🌡️ **Lab condition corrections** — temperature and pressure inputs keep your standards accurate
- 🔀 **Block randomization** — standards arranged in replicate blocks in random order to prevent measurement drift
- ⏱️ **Time estimation** — calculates total experiment duration
- 📤 **CSV export** — full run sequence with metadata header
- 🎨 **Dark-themed GUI** — built with standard Python `tkinter`, no installation required

---

## Code Structure

| Layer | Lines | What it does |
|---|---|---|
| **Chemistry** | 42–137 | Antoine equation, Raoult's Law, Ideal Gas Law, unit conversions |
| **Optimization** | 170–280 | Brute-forces all (vessel × injection) combos, picks best fit per target |
| **Randomization** | 287–363 | Block-randomized run sequence + CSV export |
| **GUI** | 370–900 | Tkinter/ttk dark-themed interface — inputs, results tables, buttons |

**Optimization scoring** (lower = better):

score = |actual − target| + 0.001 × V_inj + (5.0 penalty if V_inj > 2.5 mL)
The penalty discourages two-step injections unless no single-step option can reach the target.

---

## Requirements

- Python ≥ 3.8
- **No external packages** — pure stdlib (`tkinter`, `math`, [csv](cci:1://file:///d:/Documents/Documents/Antigravity/calibration%20generator.py:323:0-362:14), `random`, `dataclasses`)

---

## Usage

```bash
python "calibration generator.py"
