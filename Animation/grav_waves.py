#!/usr/bin/env python3
"""
Advanced diagnostic script for gravitational waves.

This script now reads a data file with multiple radii and allows you
to select which one to plot.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import cumulative_trapezoid

# --- Configuration ---

# NEW: CHOOSE WHICH RADIUS TO PLOT FROM THE DATA FILE
# Your file contains data for R=1.0 and R=5.0
radius_to_plot = 5.0  # <-- CHANGE THIS VALUE to 1.0 or 5.0

M = 1.0
mode = "22"

# --- Data Loading ---
psi4_input_filename = "/home/nik/GRChombo_runs/Wormhole_Collapse_Cheap/data/Weyl4_mode_" + mode + ".dat"

try:
    # Load the raw Psi4 data.
    psi4_data = np.loadtxt(psi4_input_filename)
    print(f"Successfully loaded raw Psi4 data from: {psi4_input_filename}")
except Exception as e:
    print(f"--- ERROR ---")
    print(f"Could not load data file: {e}")
    exit()

# --- NEW: Column selection logic ---
# Based on the value of 'radius_to_plot', we pick the correct columns.
print(f"Selecting data columns for radius R = {radius_to_plot}")
time_simulation = psi4_data[:, 0]

if radius_to_plot == 1.0:
    re_psi4 = psi4_data[:, 1]  # Column 1 is Re(Psi4) for R=1.0
    im_psi4 = psi4_data[:, 2]  # Column 2 is Im(Psi4) for R=1.0
elif radius_to_plot == 5.0:
    re_psi4 = psi4_data[:, 3]  # Column 3 is Re(Psi4) for R=5.0
    im_psi4 = psi4_data[:, 4]  # Column 4 is Im(Psi4) for R=5.0
else:
    raise ValueError(f"Invalid radius_to_plot: {radius_to_plot}. Your data file only contains data for R=1.0 and R=5.0.")

# --- Processing: Recreate the strain calculation ---
complex_psi4 = re_psi4 + 1j * im_psi4
h_dot = cumulative_trapezoid(complex_psi4, time_simulation, initial=0)
h_raw = cumulative_trapezoid(h_dot, time_simulation, initial=0)
re_h_raw = np.real(h_raw)

# --- Retarded Time Calculation (Re-instated) ---
# This will now work for R=5.0 but correctly fail for R=1.0
if (radius_to_plot / (2.0 * M) - 1.0) <= 0:
    raise ValueError(f"R={radius_to_plot} is not > 2M. This radius is inside the event horizon and physically invalid for this calculation.")
r_tortoise = radius_to_plot + M * np.log(radius_to_plot / (2.0 * M) - 1.0)
time_retarded = time_simulation - r_tortoise

# --- Detrend the Data ---
poly_coeffs = np.polyfit(time_retarded, re_h_raw, 2)
drift_poly = np.poly1d(poly_coeffs)
re_h_detrended = re_h_raw - drift_poly(time_retarded)

# --- Plotting ---
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 15), sharex=True)
fig.suptitle(f"Gravitational Wave Signal Diagnostics for R = {radius_to_plot}", fontsize=16)

# Plot 1: Raw Re(Psi4)
ax1.plot(time_retarded, re_psi4, 'g-', label=f'Re(Ψ₄) at R={radius_to_plot}')
ax1.set_ylabel("Raw Re(Ψ₄)")
ax1.set_title("Step 1: Raw Signal from Simulation")
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend()

# Plot 2: Original strain data with drift
ax2.plot(time_retarded, re_h_raw, 'r-', lw=1.5, label='Original Strain (with drift)')
ax2.set_ylabel("Strain h_{" + mode + "}")
ax2.set_title("Step 2: Strain Calculated from Raw Data")
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.legend()

# Plot 3: The corrected, detrended data
ax3.plot(time_retarded, re_h_detrended, 'b-', lw=1.5, label='Detrended Strain')
ax3.set_xlabel("Retarded Time (t - r*)")
ax3.set_ylabel("Strain h_{" + mode + "}")
ax3.set_title("Step 3: Final Signal After Removing Drift")
ax3.grid(True, linestyle='--', alpha=0.6)
ax3.legend()

# --- Save and Show ---
plt.tight_layout(rect=[0, 0.03, 1, 0.96])
output_filename = f"strain_diagnostics_R{int(radius_to_plot)}_{mode}.png"
plt.savefig(output_filename, dpi=300)
print(f"Diagnostic plot saved as {output_filename}")
plt.show()