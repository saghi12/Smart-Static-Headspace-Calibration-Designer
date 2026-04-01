"""
Smart Static Headspace Calibration Designer
=============================================
Generates Methanol gas standards for Drift Tube Ion Mobility Spectrometry (DT-IMS)
using static headspace sampling with the Antoine equation and ideal gas law.

Author : Generated for DT-IMS calibration workflow
License: MIT
Python : >= 3.8 (stdlib only – no pip packages required)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import math
import random
import csv
import datetime
from dataclasses import dataclass
from typing import List, Tuple, Optional


# ──────────────────────────────────────────────────────────────────────────────
# Physical / Chemical Constants & Calculations
# ──────────────────────────────────────────────────────────────────────────────

# Antoine coefficients for Methanol (NIST, valid ~15-84 °C)
ANTOINE_A = 8.08097
ANTOINE_B = 1582.27
ANTOINE_C = 239.7

R_GAS = 0.08206          # L·atm / (mol·K)
MOLAR_MASS_MEOH = 32040  # mg/mol  (32.04 g/mol)
MOLAR_MASS_WATER = 18015 # mg/mol  (18.015 g/mol)
DENSITY_MEOH = 0.792      # g/mL at ~20–25 °C
DENSITY_WATER = 0.998     # g/mL at ~20–25 °C
ATM_PER_MMHG = 1.0 / 760.0
STANDARD_PRESSURE_MBAR = 1013.25  # standard atmospheric pressure in mbar

AVAILABLE_VESSELS_ML = [20, 50, 100, 250, 500, 1000, 2000]


def antoine_vapor_pressure_mmhg(t_celsius: float) -> float:
    """Return the saturation vapor pressure of Methanol in mmHg."""
    return 10.0 ** (ANTOINE_A - ANTOINE_B / (t_celsius + ANTOINE_C))


def vol_percent_to_mole_fraction(vol_percent: float) -> float:
    """
    Convert a volumetric percentage (% v/v) of methanol in aqueous
    solution to the liquid-phase mole fraction x_MeOH.

    Assumes densities at ~25 °C (ρ_MeOH = 0.792, ρ_H2O = 0.998).
    """
    if vol_percent >= 100.0:
        return 1.0
    if vol_percent <= 0.0:
        return 0.0

    # In 100 mL solution:
    v_meoh = vol_percent           # mL methanol
    v_water = 100.0 - vol_percent  # mL water

    mass_meoh = v_meoh * DENSITY_MEOH    # grams
    mass_water = v_water * DENSITY_WATER  # grams

    n_meoh = mass_meoh / 32.04    # mol
    n_water = mass_water / 18.015  # mol

    return n_meoh / (n_meoh + n_water)


def headspace_concentration_mg_per_l(
    t_celsius: float,
    p_lab_mbar: float = STANDARD_PRESSURE_MBAR,
    mole_fraction: float = 1.0,
) -> float:
    """
    Calculate the headspace concentration (mg/L) of Methanol vapor
    above a liquid at the given temperature.

    For pure methanol, mole_fraction = 1.0.
    For a stock solution, use Raoult's law:
        P_MeOH = x_MeOH × P*_MeOH
    so that C_hs = x_MeOH × C_hs_pure.

    Note: Raoult's law is ideal.  Methanol-water shows positive
    deviations, so actual headspace concentrations may be 1.5-2×
    higher than predicted at low mole fractions.
    """
    p_star_mmhg = antoine_vapor_pressure_mmhg(t_celsius)
    p_meoh_atm = mole_fraction * p_star_mmhg * ATM_PER_MMHG
    t_kelvin = t_celsius + 273.15
    pressure_correction = STANDARD_PRESSURE_MBAR / p_lab_mbar
    return (p_meoh_atm * MOLAR_MASS_MEOH) / (R_GAS * t_kelvin) * pressure_correction


def headspace_concentration_ppmv(
    t_celsius: float,
    p_lab_mbar: float = STANDARD_PRESSURE_MBAR,
    mole_fraction: float = 1.0,
) -> float:
    """
    Headspace methanol concentration in ppmv (parts per million by volume).

    ppmv = (P_MeOH / P_total) × 10⁶
    """
    p_star_mmhg = antoine_vapor_pressure_mmhg(t_celsius)
    p_meoh_mmhg = mole_fraction * p_star_mmhg
    p_total_mmhg = p_lab_mbar * 760.0 / 1013.25
    return (p_meoh_mmhg / p_total_mmhg) * 1.0e6


def mg_l_to_ppmv(
    conc_mg_l: float,
    t_celsius: float,
    p_lab_mbar: float = STANDARD_PRESSURE_MBAR,
) -> float:
    """
    Convert a gas-phase concentration from mg/L to ppmv.

    ppmv = (C × R × T) / (M × P_atm) × 10⁶
    """
    t_k = t_celsius + 273.15
    p_atm = p_lab_mbar / 1013.25
    return conc_mg_l * R_GAS * t_k / (MOLAR_MASS_MEOH * p_atm) * 1.0e6


def format_time(seconds: float) -> str:
    """Format seconds into a human-readable string."""
    if seconds < 60:
        return f"{seconds:.0f} s"
    minutes = seconds / 60.0
    if minutes < 60:
        return f"{minutes:.1f} min"
    hours = int(minutes // 60)
    remaining_min = int(minutes % 60)
    return f"{hours} h {remaining_min} min"


# ──────────────────────────────────────────────────────────────────────────────
# Data Structures
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class CalibrationPoint:
    standard_id: int
    target_conc: float        # mg/L (desired)
    actual_conc: float        # mg/L (physically achievable)
    actual_ppmv: float        # ppmv (physically achievable)
    injection_vol_ml: float   # mL
    vessel_vol_ml: int        # mL
    injection_label: str      # human-readable injection string


@dataclass
class RunEntry:
    run_order: int
    block: int
    standard_id: int
    final_conc: float         # mg/L
    final_ppmv: float         # ppmv
    injection_action: str
    vessel_volume: int


# ──────────────────────────────────────────────────────────────────────────────
# Smart Optimization – Best combo for user-defined targets
# ──────────────────────────────────────────────────────────────────────────────

def find_best_combination(
    target_conc: float,
    headspace_conc: float,
    syringe_res: float,
    t_celsius: float,
    p_lab_mbar: float,
    max_syringe_vol: float = 5.0,
) -> Optional[CalibrationPoint]:
    """
    Iterate over every valid (injection_volume, vessel) combination and
    return the one whose *actual* concentration is closest to the
    user-specified target.

    Scoring (lower is better):
      primary   = |actual − target|  (closeness to the desired value)
      secondary = injection volume   (prefer less injection; 1 syringe > 2)

    The secondary term is scaled very small so it only breaks ties.
    """
    best: Optional[CalibrationPoint] = None
    best_score = float("inf")

    # Pre-compute syringe volumes (multiples of resolution up to max)
    n_steps = int(round(max_syringe_vol / syringe_res))
    syringe_volumes = [round((i + 1) * syringe_res, 6) for i in range(n_steps)]

    for vessel in AVAILABLE_VESSELS_ML:
        for inj in syringe_volumes:
            actual = headspace_conc * (inj / vessel)

            deviation = abs(actual - target_conc)

            # Prefer single-injection solutions (≤ 2.5 mL).
            # Two-step injections (> 2.5 mL) get a 5 mg/L-equivalent
            # penalty — enough to prefer a larger vessel with one fill,
            # but allows two-step when no single injection across any
            # vessel can reasonably reach the target.
            # Among single-injection combos, prefer less volume.
            step_penalty = 0.0 if inj <= 2.5 else 5.0
            score = deviation + 0.001 * inj + step_penalty

            if score < best_score:
                best_score = score
                actual_rounded = round(actual, 4)
                best = CalibrationPoint(
                    standard_id=0,
                    target_conc=target_conc,
                    actual_conc=actual_rounded,
                    actual_ppmv=round(mg_l_to_ppmv(actual_rounded, t_celsius, p_lab_mbar), 2),
                    injection_vol_ml=round(inj, 4),
                    vessel_vol_ml=vessel,
                    injection_label="",
                )

    return best


def _format_injection(vol_ml: float, syringe_res: float) -> str:
    """Format the injection volume; split into two steps if > 2.5 mL."""
    vol_ml = round(vol_ml, 4)
    if vol_ml <= 2.5:
        return f"{vol_ml:.2f} mL"
    # Two-step injection
    first = 2.5
    second = round(vol_ml - first, 4)
    # Snap second to resolution grid
    second = round(round(second / syringe_res) * syringe_res, 4)
    first = round(vol_ml - second, 4)
    # Ensure first <= 2.5; swap if needed
    if first > 2.5:
        first, second = 2.5, round(vol_ml - 2.5, 4)
    return f"{vol_ml:.2f} mL ({first:.2f} + {second:.2f})"


def design_calibration(
    t_celsius: float,
    targets: List[float],
    syringe_res: float,
    p_lab_mbar: float = STANDARD_PRESSURE_MBAR,
    mole_fraction: float = 1.0,
) -> Tuple[float, float, List[CalibrationPoint]]:
    """
    Main design routine.
    Returns (headspace_conc_mg_l, headspace_conc_ppmv, list_of_CalibrationPoints).
    """
    hs_conc = headspace_concentration_mg_per_l(t_celsius, p_lab_mbar, mole_fraction)
    hs_ppmv = headspace_concentration_ppmv(t_celsius, p_lab_mbar, mole_fraction)

    points: List[CalibrationPoint] = []

    # Blank (standard 0) – always first
    points.append(CalibrationPoint(
        standard_id=0,
        target_conc=0.0,
        actual_conc=0.0,
        actual_ppmv=0.0,
        injection_vol_ml=0.0,
        vessel_vol_ml=0,
        injection_label="Blank (no injection)",
    ))

    for idx, tgt in enumerate(sorted(targets), start=1):
        best = find_best_combination(tgt, hs_conc, syringe_res,
                                     t_celsius, p_lab_mbar)
        if best is None:
            continue
        best.standard_id = idx
        best.injection_label = _format_injection(best.injection_vol_ml, syringe_res)
        points.append(best)

    return hs_conc, hs_ppmv, points


# ──────────────────────────────────────────────────────────────────────────────
# Block Randomization
# ──────────────────────────────────────────────────────────────────────────────

def generate_run_sequence(
    points: List[CalibrationPoint],
    n_blocks: int,
    seed: Optional[int] = None,
) -> List[RunEntry]:
    """
    Create a randomized run sequence with *n_blocks* blocks.
    Each block contains every standard exactly once, in random order.
    """
    if seed is not None:
        random.seed(seed)

    entries: List[RunEntry] = []
    run_counter = 1

    for block_num in range(1, n_blocks + 1):
        block_points = list(points)
        random.shuffle(block_points)
        for pt in block_points:
            entries.append(RunEntry(
                run_order=run_counter,
                block=block_num,
                standard_id=pt.standard_id,
                final_conc=pt.actual_conc,
                final_ppmv=pt.actual_ppmv,
                injection_action=pt.injection_label,
                vessel_volume=pt.vessel_vol_ml,
            ))
            run_counter += 1

    return entries


# ──────────────────────────────────────────────────────────────────────────────
# CSV Export
# ──────────────────────────────────────────────────────────────────────────────

def export_csv(
    filepath: str,
    entries: List[RunEntry],
    t_celsius: float,
    p_lab_mbar: float,
    hs_conc: float,
    hs_ppmv: float,
    n_blocks: int,
    analysis_time_s: float,
    source_desc: str,
) -> None:
    """Write the run sequence to a CSV file with a metadata header."""
    total_time = len(entries) * analysis_time_s
    with open(filepath, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        # ── Metadata header ──
        writer.writerow(["# Smart Static Headspace Calibration Designer"])
        writer.writerow([f"# Generated: {datetime.datetime.now():%Y-%m-%d %H:%M}"])
        writer.writerow([f"# Lab Temperature (°C): {t_celsius:.1f}"])
        writer.writerow([f"# Lab Pressure (mbar): {p_lab_mbar:.1f}"])
        writer.writerow([f"# Headspace Concentration: {hs_conc:.2f} mg/L  "
                         f"({hs_ppmv:.0f} ppmv)"])
        writer.writerow([f"# Headspace Source: {source_desc}"])
        writer.writerow([f"# Number of Blocks: {n_blocks}"])
        writer.writerow([f"# Analysis Time per Run: {analysis_time_s:.0f} s"])
        writer.writerow([f"# Estimated Total Time: {format_time(total_time)}"])
        writer.writerow([])

        # ── Data ──
        writer.writerow([
            "Run_Order", "Block", "Standard_ID",
            "Final_Conc_mg_L", "Final_Conc_ppmv",
            "Injection_Action_mL", "Vessel_Volume_mL",
        ])
        for e in entries:
            writer.writerow([
                e.run_order, e.block, e.standard_id,
                f"{e.final_conc:.2f}", f"{e.final_ppmv:.1f}",
                e.injection_action, e.vessel_volume,
            ])


# ──────────────────────────────────────────────────────────────────────────────
# GUI Application
# ──────────────────────────────────────────────────────────────────────────────

class CalibrationDesignerApp(tk.Tk):
    """Main application window."""

    # ── Colour palette ──
    BG        = "#1e1e2e"
    BG_CARD   = "#2a2a3d"
    FG        = "#cdd6f4"
    FG_DIM    = "#7f849c"
    ACCENT    = "#89b4fa"
    ACCENT2   = "#a6e3a1"
    ACCENT3   = "#f9e2af"   # yellow for shuffle
    DANGER    = "#f38ba8"
    BORDER    = "#45475a"

    def __init__(self):
        super().__init__()
        self.title("Smart Static Headspace Calibration Designer  ·  Methanol / DT-IMS")
        self.configure(bg=self.BG)
        self.minsize(1200, 780)
        self.geometry("1300x860")

        # State
        self._points: List[CalibrationPoint] = []
        self._entries: List[RunEntry] = []
        self._hs_conc: float = 0.0
        self._hs_ppmv: float = 0.0

        self._configure_styles()
        self._build_ui()

    # ── ttk style setup ──────────────────────────────────────────────────

    def _configure_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(".", background=self.BG, foreground=self.FG,
                         fieldbackground=self.BG_CARD, borderwidth=0,
                         font=("Segoe UI", 10))

        style.configure("Title.TLabel", font=("Segoe UI Semibold", 16),
                         foreground=self.ACCENT, background=self.BG)
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10),
                         foreground=self.FG_DIM, background=self.BG)
        style.configure("Section.TLabel", font=("Segoe UI Semibold", 11),
                         foreground=self.ACCENT2, background=self.BG)
        style.configure("Info.TLabel", font=("Segoe UI", 10),
                         foreground=self.FG, background=self.BG)
        style.configure("Highlight.TLabel", font=("Segoe UI Semibold", 11),
                         foreground=self.ACCENT, background=self.BG)
        style.configure("HSInfo.TLabel", font=("Segoe UI", 10),
                         foreground=self.ACCENT2, background=self.BG,
                         wraplength=700)

        style.configure("Card.TFrame", background=self.BG_CARD,
                         relief="flat")
        style.configure("Main.TFrame", background=self.BG)

        style.configure("Accent.TButton", font=("Segoe UI Semibold", 11),
                         foreground="#1e1e2e", background=self.ACCENT,
                         padding=(18, 8))
        style.map("Accent.TButton",
                  background=[("active", "#b4d8fd"), ("disabled", self.BORDER)])

        style.configure("Export.TButton", font=("Segoe UI Semibold", 11),
                         foreground="#1e1e2e", background=self.ACCENT2,
                         padding=(18, 8))
        style.map("Export.TButton",
                  background=[("active", "#c6f0c2"), ("disabled", self.BORDER)])

        style.configure("Shuffle.TButton", font=("Segoe UI Semibold", 11),
                         foreground="#1e1e2e", background=self.ACCENT3,
                         padding=(18, 8))
        style.map("Shuffle.TButton",
                  background=[("active", "#fdf0c8"), ("disabled", self.BORDER)])

        style.configure("TEntry", fieldbackground=self.BG_CARD,
                         foreground=self.FG, insertcolor=self.FG,
                         padding=6)

        style.configure("Treeview", background=self.BG_CARD,
                         foreground=self.FG, fieldbackground=self.BG_CARD,
                         rowheight=26, font=("Consolas", 10))
        style.configure("Treeview.Heading",
                         font=("Segoe UI Semibold", 10),
                         background=self.BORDER, foreground=self.FG)
        style.map("Treeview", background=[("selected", "#45475a")])

    # ── UI construction ──────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ──
        hdr = ttk.Frame(self, style="Main.TFrame")
        hdr.pack(fill="x", padx=20, pady=(18, 4))
        ttk.Label(hdr, text="⚗  Smart Static Headspace Calibration Designer",
                  style="Title.TLabel").pack(anchor="w")
        ttk.Label(hdr, text="Methanol gas-phase standards for Drift Tube Ion "
                  "Mobility Spectrometry (DT-IMS)",
                  style="Subtitle.TLabel").pack(anchor="w", pady=(2, 0))

        # ── Main paned container ──
        body = ttk.Frame(self, style="Main.TFrame")
        body.pack(fill="both", expand=True, padx=20, pady=10)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # ── Left panel (inputs) — use a canvas for scrollability ──
        left = ttk.Frame(body, style="Card.TFrame", width=340)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 12))
        left.grid_propagate(False)
        self._build_input_panel(left)

        # ── Right panel (results) ──
        right = ttk.Frame(body, style="Main.TFrame")
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(2, weight=1)
        right.columnconfigure(0, weight=1)
        self._build_results_panel(right)

    def _add_input_field(self, parent, label: str, default: str,
                         row: int) -> ttk.Entry:
        ttk.Label(parent, text=label, style="Info.TLabel",
                  background=self.BG_CARD).grid(
            row=row, column=0, sticky="w", padx=16, pady=(8, 1))
        var = tk.StringVar(value=default)
        entry = ttk.Entry(parent, textvariable=var, width=14)
        entry.grid(row=row + 1, column=0, sticky="w", padx=16, pady=(0, 2))
        entry._var = var  # keep reference
        return entry

    def _build_input_panel(self, parent):
        parent.columnconfigure(0, weight=1)
        row = 0

        # ── Lab Conditions ──
        ttk.Label(parent, text="Lab Conditions", style="Section.TLabel",
                  background=self.BG_CARD).grid(
            row=row, column=0, sticky="w", padx=16, pady=(12, 2))
        row += 1

        self.ent_temp = self._add_input_field(
            parent, "Lab Temperature (°C)", "25.0", row)
        row += 2
        self.ent_pressure = self._add_input_field(
            parent, "Lab Pressure (mbar)", "1013.25", row)
        row += 2
        self.ent_res = self._add_input_field(
            parent, "Syringe Resolution (mL)", "0.05", row)
        row += 2
        self.ent_blocks = self._add_input_field(
            parent, "Number of Replicates / Blocks", "5", row)
        row += 2
        self.ent_analysis_time = self._add_input_field(
            parent, "Analysis Time per Run (s)", "100", row)
        row += 2

        # ── Headspace Source ──
        sep0 = ttk.Separator(parent, orient="horizontal")
        sep0.grid(row=row, column=0, sticky="we", padx=16, pady=6)
        row += 1

        ttk.Label(parent, text="Headspace Source Vial",
                  style="Section.TLabel",
                  background=self.BG_CARD).grid(
            row=row, column=0, sticky="w", padx=16, pady=(4, 2))
        row += 1

        self.ent_stock_purity = self._add_input_field(
            parent, "Methanol Purity (% v/v)", "100", row)
        row += 2
        self.ent_liquid_vol = self._add_input_field(
            parent, "Liquid Volume in Vial (mL)", "1.0", row)
        row += 2
        self.ent_vial_vol = self._add_input_field(
            parent, "Source Vial Volume (mL)", "20", row)
        row += 2

        # ── Target Concentrations ──
        sep1 = ttk.Separator(parent, orient="horizontal")
        sep1.grid(row=row, column=0, sticky="we", padx=16, pady=6)
        row += 1

        ttk.Label(parent,
                  text="Target Concentrations (mg/L)",
                  style="Section.TLabel",
                  background=self.BG_CARD).grid(
            row=row, column=0, sticky="w", padx=16, pady=(4, 1))
        row += 1

        ttk.Label(parent,
                  text="Comma-separated (blank added auto.):",
                  style="Subtitle.TLabel",
                  background=self.BG_CARD).grid(
            row=row, column=0, sticky="w", padx=16, pady=(0, 3))
        row += 1

        self.txt_targets = tk.Text(
            parent, height=3, width=30,
            bg=self.BG, fg=self.FG,
            insertbackground=self.FG,
            font=("Consolas", 10),
            relief="flat", padx=8, pady=6,
            wrap="word",
        )
        self.txt_targets.grid(row=row, column=0, sticky="we", padx=16, pady=(0, 2))
        self.txt_targets.insert("1.0", "0.5, 1, 2, 5, 10, 20, 35, 50")
        row += 1

        # ── Vessels info ──
        sep2 = ttk.Separator(parent, orient="horizontal")
        sep2.grid(row=row, column=0, sticky="we", padx=16, pady=6)
        row += 1

        ttk.Label(parent, text="Available Vessels (mL)",
                  style="Section.TLabel",
                  background=self.BG_CARD).grid(
            row=row, column=0, sticky="w", padx=16)
        row += 1
        ttk.Label(parent,
                  text=", ".join(str(v) for v in AVAILABLE_VESSELS_ML),
                  style="Info.TLabel",
                  background=self.BG_CARD).grid(
            row=row, column=0, sticky="w", padx=16, pady=(2, 4))
        row += 1

        # ── Buttons ──
        btn_frame = ttk.Frame(parent, style="Card.TFrame")
        btn_frame.grid(row=row, column=0, sticky="we", padx=16, pady=(6, 2))
        row += 1

        self.btn_calc = ttk.Button(btn_frame, text="▶  Calculate",
                                   style="Accent.TButton",
                                   command=self._on_calculate)
        self.btn_calc.pack(fill="x", pady=(0, 5))

        self.btn_shuffle = ttk.Button(btn_frame, text="🔀  Shuffle Runs",
                                      style="Shuffle.TButton",
                                      command=self._on_shuffle,
                                      state="disabled")
        self.btn_shuffle.pack(fill="x", pady=(0, 5))

        self.btn_export = ttk.Button(btn_frame, text="⬇  Export CSV",
                                     style="Export.TButton",
                                     command=self._on_export,
                                     state="disabled")
        self.btn_export.pack(fill="x")

        # ── Status ──
        self.lbl_status = ttk.Label(parent, text="", style="Subtitle.TLabel",
                                    background=self.BG_CARD, wraplength=300)
        self.lbl_status.grid(row=row, column=0, sticky="w", padx=16,
                             pady=(8, 12))

    def _build_results_panel(self, parent):
        # ── Info bar (row 0) ──
        info = ttk.Frame(parent, style="Main.TFrame")
        info.grid(row=0, column=0, sticky="we", pady=(0, 2))

        self.lbl_hs = ttk.Label(info, text="Headspace Conc.:  —",
                                style="Highlight.TLabel")
        self.lbl_hs.pack(side="left")
        self.lbl_total = ttk.Label(info, text="Total runs:  —",
                                   style="Info.TLabel")
        self.lbl_total.pack(side="right")

        # ── Headspace info bar (row 1) ──
        info2 = ttk.Frame(parent, style="Main.TFrame")
        info2.grid(row=1, column=0, sticky="we", pady=(0, 6))

        self.lbl_hs_desc = ttk.Label(info2, text="",
                                     style="HSInfo.TLabel")
        self.lbl_hs_desc.pack(side="left")
        self.lbl_time = ttk.Label(info2, text="",
                                  style="Info.TLabel")
        self.lbl_time.pack(side="right")

        # ── Notebook for Standards / Sequence tabs (row 2) ──
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=2, column=0, sticky="nsew")

        # --- Standards tab ---
        tab_std = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(tab_std, text="  Calibration Standards  ")
        tab_std.rowconfigure(0, weight=1)
        tab_std.columnconfigure(0, weight=1)

        cols_std = ("ID", "Target (mg/L)", "Actual (mg/L)", "Actual (ppmv)",
                    "Injection", "Vessel (mL)")
        self.tree_std = ttk.Treeview(tab_std, columns=cols_std,
                                     show="headings", selectmode="browse")
        for c, w in zip(cols_std, (50, 105, 105, 100, 180, 90)):
            self.tree_std.heading(c, text=c)
            self.tree_std.column(c, width=w, anchor="center")
        self.tree_std.grid(row=0, column=0, sticky="nsew")

        sb_std = ttk.Scrollbar(tab_std, orient="vertical",
                               command=self.tree_std.yview)
        self.tree_std.configure(yscrollcommand=sb_std.set)
        sb_std.grid(row=0, column=1, sticky="ns")

        # --- Sequence tab ---
        tab_seq = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(tab_seq, text="  Randomized Run Sequence  ")
        tab_seq.rowconfigure(0, weight=1)
        tab_seq.columnconfigure(0, weight=1)

        cols_seq = ("Run", "Block", "Std ID", "mg/L", "ppmv",
                    "Injection", "Vessel (mL)")
        self.tree_seq = ttk.Treeview(tab_seq, columns=cols_seq,
                                     show="headings", selectmode="browse")
        for c, w in zip(cols_seq, (55, 55, 55, 85, 85, 180, 90)):
            self.tree_seq.heading(c, text=c)
            self.tree_seq.column(c, width=w, anchor="center")
        self.tree_seq.grid(row=0, column=0, sticky="nsew")

        sb_seq = ttk.Scrollbar(tab_seq, orient="vertical",
                               command=self.tree_seq.yview)
        self.tree_seq.configure(yscrollcommand=sb_seq.set)
        sb_seq.grid(row=0, column=1, sticky="ns")

    # ── Helpers ──────────────────────────────────────────────────────────

    def _get_source_description(self, t_c, p_mbar, purity, liq_vol, vial_vol):
        """Build a human-readable headspace source description."""
        if purity >= 100.0:
            stock_str = "neat methanol"
        else:
            stock_str = f"{purity:.1f}% v/v methanol solution"
        return (f"~{liq_vol:.1f} mL {stock_str} in a "
                f"{vial_vol:.0f} mL sealed vial at {t_c:.1f} °C, "
                f"{p_mbar:.1f} mbar")

    def _parse_targets(self) -> List[float]:
        """Parse the target concentrations from the text area."""
        raw = self.txt_targets.get("1.0", "end").strip()
        if not raw:
            raise ValueError("Please enter at least one target concentration.")

        for sep in [";", "\n", "\t"]:
            raw = raw.replace(sep, ",")

        values = []
        for token in raw.split(","):
            token = token.strip()
            if not token:
                continue
            v = float(token)
            if v < 0:
                raise ValueError(f"Concentration cannot be negative: {v}")
            if v == 0:
                continue  # blank is added automatically
            values.append(v)

        if not values:
            raise ValueError("Please enter at least one non-zero target.")
        return values

    def _read_inputs(self):
        """Parse and validate all user inputs. Raises ValueError on bad data."""
        t = float(self.ent_temp._var.get())
        if not (-20 <= t <= 80):
            raise ValueError("Temperature must be between −20 °C and 80 °C.")

        p = float(self.ent_pressure._var.get())
        if not (500 <= p <= 1200):
            raise ValueError("Lab pressure must be between 500 and 1200 mbar.")

        sr = float(self.ent_res._var.get())
        if sr <= 0:
            raise ValueError("Syringe resolution must be > 0.")

        nb = int(self.ent_blocks._var.get())
        if not (1 <= nb <= 30):
            raise ValueError("Number of blocks must be 1–30.")

        at = float(self.ent_analysis_time._var.get())
        if at <= 0:
            raise ValueError("Analysis time must be > 0.")

        purity = float(self.ent_stock_purity._var.get())
        if not (0 < purity <= 100):
            raise ValueError("Methanol purity must be between 0 and 100 % v/v.")

        liq_vol = float(self.ent_liquid_vol._var.get())
        if liq_vol <= 0:
            raise ValueError("Liquid volume must be > 0.")

        vial_vol = float(self.ent_vial_vol._var.get())
        if vial_vol <= 0:
            raise ValueError("Source vial volume must be > 0.")
        if liq_vol >= vial_vol:
            raise ValueError("Liquid volume must be less than vial volume.")

        targets = self._parse_targets()

        return t, p, sr, nb, at, purity, liq_vol, vial_vol, targets

    # ── Actions ──────────────────────────────────────────────────────────

    def _populate_sequence_table(self):
        """Fill the sequence treeview from self._entries."""
        self.tree_seq.delete(*self.tree_seq.get_children())
        for e in self._entries:
            self.tree_seq.insert("", "end", values=(
                e.run_order, e.block, e.standard_id,
                f"{e.final_conc:.2f}",
                f"{e.final_ppmv:.1f}",
                e.injection_action,
                e.vessel_volume if e.vessel_volume else "—",
            ))

    def _on_calculate(self):
        try:
            (t_c, p_mbar, syr_res, n_blk, a_time,
             purity, liq_vol, vial_vol, targets) = self._read_inputs()
        except (ValueError, tk.TclError) as exc:
            messagebox.showerror("Invalid Input", str(exc))
            return

        # Compute mole fraction from purity
        x_meoh = vol_percent_to_mole_fraction(purity)

        # Design
        self._hs_conc, self._hs_ppmv, self._points = design_calibration(
            t_c, targets, syr_res, p_lab_mbar=p_mbar, mole_fraction=x_meoh)

        # Sequence (fresh randomization)
        self._entries = generate_run_sequence(self._points, n_blk)

        total_runs = len(self._entries)
        total_time = total_runs * a_time

        # ── Update info bar ──
        self.lbl_hs.config(
            text=f"Headspace Conc.:  {self._hs_conc:.2f} mg/L  "
                 f"({self._hs_ppmv:.0f} ppmv)")
        self.lbl_total.config(text=f"Total runs:  {total_runs}")

        # Headspace description
        src_desc = self._get_source_description(
            t_c, p_mbar, purity, liq_vol, vial_vol)
        self.lbl_hs_desc.config(text=f"⚗ Source: {src_desc}")
        self.lbl_time.config(
            text=f"⏱ Est. total time: {format_time(total_time)}")

        # ── Populate standards table ──
        self.tree_std.delete(*self.tree_std.get_children())
        for pt in self._points:
            self.tree_std.insert("", "end", values=(
                pt.standard_id,
                f"{pt.target_conc:.2f}",
                f"{pt.actual_conc:.2f}",
                f"{pt.actual_ppmv:.1f}",
                pt.injection_label,
                pt.vessel_vol_ml if pt.vessel_vol_ml else "—",
            ))

        # ── Populate sequence table ──
        self._populate_sequence_table()

        self.btn_shuffle.config(state="normal")
        self.btn_export.config(state="normal")
        self.lbl_status.config(
            text=f"✓  {len(self._points)} standards designed, "
                 f"{total_runs} runs generated.")

    def _on_shuffle(self):
        """Re-randomize the run sequence without recalculating standards."""
        if not self._points:
            return

        try:
            n_blk = int(self.ent_blocks._var.get())
        except ValueError:
            n_blk = 5

        self._entries = generate_run_sequence(self._points, n_blk)
        self._populate_sequence_table()

        # Switch to the sequence tab so the user sees the new order
        self.notebook.select(1)
        self.lbl_status.config(text="🔀  Run sequence reshuffled.")

    def _on_export(self):
        if not self._entries:
            messagebox.showwarning("Nothing to Export",
                                   "Run the calculation first.")
            return

        try:
            t_c = float(self.ent_temp._var.get())
            p_mbar = float(self.ent_pressure._var.get())
            n_blk = int(self.ent_blocks._var.get())
            a_time = float(self.ent_analysis_time._var.get())
            purity = float(self.ent_stock_purity._var.get())
            liq_vol = float(self.ent_liquid_vol._var.get())
            vial_vol = float(self.ent_vial_vol._var.get())
        except ValueError:
            t_c, p_mbar, n_blk, a_time = 25.0, 1013.25, 5, 100.0
            purity, liq_vol, vial_vol = 100.0, 1.0, 20.0

        src_desc = self._get_source_description(
            t_c, p_mbar, purity, liq_vol, vial_vol)

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="Export Calibration Sequence",
            initialfile=f"MeOH_Calibration_{t_c:.0f}C.csv",
        )
        if not filepath:
            return

        try:
            export_csv(filepath, self._entries, t_c, p_mbar,
                       self._hs_conc, self._hs_ppmv, n_blk, a_time, src_desc)
            self.lbl_status.config(text=f"✓  Exported to {filepath}")
            messagebox.showinfo("Export Successful",
                                f"Saved {len(self._entries)} run entries to:\n"
                                f"{filepath}")
        except OSError as exc:
            messagebox.showerror("Export Error", str(exc))


# ──────────────────────────────────────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = CalibrationDesignerApp()
    app.mainloop()