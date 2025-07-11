#!/usr/bin/env python3
"""
Plot Hamiltonian constraint for Wormhole simulation
Simplified script to plot only the Ham field which is available in the dataset
"""

import yt
import os
import matplotlib
import glob

matplotlib.use("Agg")

def get_center(ds):
    """Get center of the simulation domain"""
    center = None
    if hasattr(ds,'domain_right_edge'):
        center = ds.domain_right_edge / 2.0
    elif hasattr(ds[0],'domain_right_edge'):
        center = ds[0].domain_right_edge / 2.0
    return center

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
        for field in available_fields:
            print(f"  - {field}")
        print()
        
        # Check if Ham field is available
        if 'Ham' not in available_fields:
            print("ERROR: Ham field not found in dataset!")
            print("Cannot plot Hamiltonian constraint.")
            exit(1)
        else:
            print("✓ Ham (Hamiltonian constraint) field found!")
            
    except Exception as e:
        print(f"Error checking fields: {e}")
        exit(1)

# Set up plotting parameters
field_name = "Ham"
center = get_center(ts)
center[2] = 0  # Set z=0 for equatorial plane slice
axis = "z"  # Plot z-slice through equatorial plane

# Create output directory
if yt.is_root():
    output_dir = "hamiltonian_plots"
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

def produce_hamiltonian_plot(data, variable="Ham", axis="z"):
    """Create a slice plot of the Hamiltonian constraint"""
    
    print(f"Creating plot for time = {float(data.current_time):.3f}")
    
    # Create slice plot
    slc = yt.SlicePlot(data, axis, ('chombo', variable), center=center)
    
    # Configure the plot for Hamiltonian constraint
    slc.set_log(variable, False)  # Don't use log scale
    slc.set_cmap(field=variable, cmap="RdBu_r")  # Good for constraint violations
    
    # Set labels
    slc.set_xlabel(r"x $\left[\frac{1}{m}\right]$")
    slc.set_ylabel(r"y $\left[\frac{1}{m}\right]$")
    slc.set_colorbar_label(variable, "Hamiltonian Constraint")
    
    # Add time annotation
    slc.annotate_text(
        (0.13, 0.92),
        ("time = " + str(float(data.current_time)) + " 1/m"),
        coord_system="figure",
        text_args={"color": "white"},
    )
    
    # Set resolution and window size
    slc.set_buff_size(1024)
    slc.set_width(10)
    
    # Save the plot
    slc.save(f"{output_dir}/")
    
    return slc

# Plot for all timesteps
print(f"\nCreating Hamiltonian constraint plots...")
plot_count = 0

if hasattr(ts, 'piter'):
    # Multiple datasets (parallel case)
    print("Processing multiple datasets...")
    for i in ts.piter():
        try:
            produce_hamiltonian_plot(i)
            plot_count += 1
        except Exception as e:
            if yt.is_root():
                print(f"Error creating plot: {e}")
else:
    # Single dataset (serial case)
    if yt.is_root():
        print("Processing single dataset...")
        try:
            produce_hamiltonian_plot(ts)
            plot_count += 1
        except Exception as e:
            print(f"Error creating plot: {e}")

if yt.is_root():
    if plot_count > 0:
        print(f"\n✅ Successfully created {plot_count} Hamiltonian constraint plots!")
        print(f"Plots saved in: {output_dir}/")
        print("\nNext steps:")
        print("1. Check the plots in the hamiltonian_plots/ directory")
        print("2. Use create_animation.py to make an animation:")
        print("   python create_animation.py hamiltonian_plots")
    else:
        print("\n❌ No plots were created successfully.")
        
    print(f"\nDataset info:")
    print(f"- Number of timesteps: {len(ts)}")
    print(f"- Available field: Ham (Hamiltonian constraint)")
    print(f"- Domain center: {center}") 