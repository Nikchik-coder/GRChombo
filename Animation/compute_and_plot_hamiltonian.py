
#!/usr/bin/env python3
"""
Compute and plot Hamiltonian constraint for Wormhole simulation
This script computes the Hamiltonian constraint directly from the evolution variables
since Ham is not available in the dataset
"""

import yt
import numpy as np
import matplotlib.pyplot as plt
import os
import glob

# Set matplotlib to non-interactive backend
import matplotlib
matplotlib.use("Agg")

def get_center(ds):
    """Get center of the simulation domain"""
    center = None
    if hasattr(ds,'domain_right_edge'):
        center = ds.domain_right_edge / 2.0
    elif hasattr(ds[0],'domain_right_edge'):
        center = ds[0].domain_right_edge / 2.0
    return center

def compute_hamiltonian_constraint(ds):
    """
    Compute Hamiltonian constraint from evolution variables
    Ham = R + K^2 - A_ij A^ij  (in simplified form)
    
    For a more accurate calculation, we would need to compute the Ricci scalar R
    from the metric, but here we'll compute a simplified version using available fields
    """
    print("Computing Hamiltonian constraint from evolution variables...")
    
    # Extract data from dataset
    data = ds.all_data()
    
    # Get the basic fields
    chi = data[('chombo', 'chi')]
    K = data[('chombo', 'K')]
    lapse = data[('chombo', 'lapse')]
    
    # Get metric components  
    h11 = data[('chombo', 'h11')]
    h22 = data[('chombo', 'h22')]
    h33 = data[('chombo', 'h33')]
    h12 = data[('chombo', 'h12')]
    h13 = data[('chombo', 'h13')]
    h23 = data[('chombo', 'h23')]
    
    # Get extrinsic curvature components
    A11 = data[('chombo', 'A11')]
    A22 = data[('chombo', 'A22')]
    A33 = data[('chombo', 'A33')]
    A12 = data[('chombo', 'A12')]
    A13 = data[('chombo', 'A13')]
    A23 = data[('chombo', 'A23')]
    
    print("Computing metric determinant and inverse...")
    
    # Compute determinant of conformal metric h_ij
    det_h = (h11 * h22 * h33 + 2 * h12 * h13 * h23 - 
             h11 * h23**2 - h22 * h13**2 - h33 * h12**2)
    
    # Avoid division by zero
    det_h = np.where(np.abs(det_h) < 1e-10, 1e-10, det_h)
    
    # Compute inverse metric h^ij
    h_UU_11 = (h22 * h33 - h23**2) / det_h
    h_UU_22 = (h11 * h33 - h13**2) / det_h
    h_UU_33 = (h11 * h22 - h12**2) / det_h
    h_UU_12 = (h13 * h23 - h12 * h33) / det_h
    h_UU_13 = (h12 * h23 - h13 * h22) / det_h
    h_UU_23 = (h12 * h13 - h11 * h23) / det_h
    
    print("Computing A_ij A^ij...")
    
    # Compute A_ij A^ij = A_ij h^ik h^jl A_kl
    A_trace = (A11 * h_UU_11 + A22 * h_UU_22 + A33 * h_UU_33 + 
               2 * A12 * h_UU_12 + 2 * A13 * h_UU_13 + 2 * A23 * h_UU_23)
    
    # For wormhole initial data (time-symmetric slice), we expect:
    # - Ricci scalar R ≈ 0 (approximately flat initial data)
    # - A_ij = 0 initially (time-symmetric)
    # So Ham ≈ K^2 for initial data
    
    print("Computing simplified Hamiltonian constraint...")
    
    # Simplified Hamiltonian constraint (good approximation for time-symmetric data)
    # This ignores the Ricci scalar term which requires computing derivatives
    Ham_simplified = K**2 - A_trace
    
    # For a full calculation, we would need:
    # Ham = R + K^2 - A_ij A^ij
    # where R is the Ricci scalar requiring second derivatives of the metric
    
    print(f"Hamiltonian constraint statistics:")
    print(f"  Min: {float(np.min(Ham_simplified)):.6e}")
    print(f"  Max: {float(np.max(Ham_simplified)):.6e}")
    print(f"  Mean: {float(np.mean(Ham_simplified)):.6e}")
    print(f"  RMS: {float(np.sqrt(np.mean(Ham_simplified**2))):.6e}")
    
    return Ham_simplified

# Enable Parallelism
yt.enable_parallelism()

# Data file location - adjust this path as needed
data_location = "/home/nik/GRChombo_runs/Wormhole_Collapse/hdf5/Wormhole_*.3d.hdf5"

print("Looking for data files...")
print(f"Data location pattern: {data_location}")

# Check if files exist
test_files = glob.glob(data_location)
if not test_files:
    print("No data files found!")
    print("Please check the data location path.")
    exit(1)

print(f"Found {len(test_files)} data files")

# Loading dataset
ts = yt.load(data_location)

# Check what fields are available in the dataset
if yt.is_root():
    print("\nChecking available fields...")
    try:
        available_fields = [field[1] for field in ts[0].field_list if field[0] == 'chombo']
        print("Available fields in the dataset:")
        for field in sorted(available_fields):
            print(f"  - {field}")
        print()
        
        # Check if we have all required fields for Hamiltonian computation
        required_fields = ['chi', 'K', 'lapse', 'h11', 'h22', 'h33', 'h12', 'h13', 'h23',
                          'A11', 'A22', 'A33', 'A12', 'A13', 'A23']
        missing_fields = [f for f in required_fields if f not in available_fields]
        
        if missing_fields:
            print(f"ERROR: Missing required fields: {missing_fields}")
            print("Cannot compute Hamiltonian constraint.")
            exit(1)
        else:
            print("✓ All required fields found for Hamiltonian constraint computation!")
            
    except Exception as e:
        print(f"Error checking fields: {e}")
        exit(1)

# Set up plotting parameters
center = get_center(ts)
center[2] = 0  # Set z=0 for equatorial plane slice
axis = "z"  # Plot z-slice through equatorial plane

# Create output directory
if yt.is_root():
    output_dir = "computed_hamiltonian"
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
        print(f"Created output directory: {output_dir}")
    else:
        # Clean existing plots
        old_plots = glob.glob(f"{output_dir}/*.png")
        if old_plots:
            print(f"Cleaning {len(old_plots)} old plots from {output_dir}/ directory")
            for plot_file in old_plots:
                os.remove(plot_file)

def create_hamiltonian_plot(ds, output_dir, timestep_number):
    """Create a plot of the computed Hamiltonian constraint"""
    
    print(f"Creating Hamiltonian plot for time = {float(ds.current_time):.3f}")
    
    # Compute Hamiltonian constraint
    Ham_computed = compute_hamiltonian_constraint(ds)
    
    # Create a derived field for plotting
    def _hamiltonian_constraint(field, data):
        return compute_hamiltonian_constraint(data.ds)
    
    # Add the derived field to yt
    ds.add_field(("gas", "hamiltonian_constraint"), 
                 function=_hamiltonian_constraint, 
                 units="dimensionless",
                 sampling_type="cell")
    
    # Create slice plot
    slc = yt.SlicePlot(ds, axis, ("gas", "hamiltonian_constraint"), center=center)
    
    # Configure the plot
    slc.set_log(("gas", "hamiltonian_constraint"), False)
    slc.set_cmap(field=("gas", "hamiltonian_constraint"), cmap="RdBu_r")
    
    # Set labels
    slc.set_xlabel(r"x $\left[\frac{1}{m}\right]$")
    slc.set_ylabel(r"y $\left[\frac{1}{m}\right]$")
    slc.set_colorbar_label(("gas", "hamiltonian_constraint"), "Hamiltonian Constraint (Computed)")
    
    # Add time annotation
    slc.annotate_text(
        (0.13, 0.92),
        ("time = " + str(float(ds.current_time)) + " 1/m"),
        coord_system="figure",
        text_args={"color": "white"},
    )
    
    # Set resolution and window size
    slc.set_buff_size(1024)
    slc.set_width(10)
    
    # Save the plot
    plot_name = f"computed_hamiltonian_{timestep_number:06d}"
    slc.save(f"{output_dir}/{plot_name}")
    
    return slc

# Plot for all timesteps
print(f"\nCreating computed Hamiltonian constraint plots...")
plot_count = 0
timestep = 0

if hasattr(ts, 'piter'):
    # Multiple datasets (parallel case)
    print("Processing multiple datasets...")
    for i in ts.piter():
        try:
            create_hamiltonian_plot(i, output_dir, timestep)
            plot_count += 1
            timestep += 1
        except Exception as e:
            if yt.is_root():
                print(f"Error creating plot for timestep {timestep}: {e}")
            timestep += 1
else:
    # Single dataset (serial case)
    if yt.is_root():
        print("Processing single dataset...")
        try:
            create_hamiltonian_plot(ts, output_dir, timestep)
            plot_count += 1
        except Exception as e:
            print(f"Error creating plot: {e}")

if yt.is_root():
    if plot_count > 0:
        print(f"\n✅ Successfully created {plot_count} computed Hamiltonian constraint plots!")
        print(f"Plots saved in: {output_dir}/")
        print("\nNext steps:")
        print("1. Check the plots in the computed_hamiltonian/ directory")
        print("2. Use create_animation.py to make an animation:")
        print("   python create_animation.py computed_hamiltonian")
        print("\nNote: This is a simplified Hamiltonian constraint calculation.")
        print("For the full constraint, the Ricci scalar R would need to be computed.")
    else:
        print("\n❌ No plots were created successfully.")
        
    print(f"\nDataset info:")
    print(f"- Number of timesteps: {len(ts)}")
    print(f"- Available evolution fields: {len(available_fields)}")
    print(f"- Computed field: Hamiltonian constraint (simplified)")
    print(f"- Formula used: Ham ≈ K² - A_ij A^ij")
    print(f"- Note: Full formula is Ham = R + K² - A_ij A^ij") 