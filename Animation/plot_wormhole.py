# plot_serial.py
# A simple, single-core, serial plotting script for GRChombo HDF5 files.
# This script processes files one by one and is easy to debug.

import yt
import os
import matplotlib
import argparse

# =========================================================================
# --- Configuration ---
# =========================================================================

# Define the list of all variables you are interested in plotting.
# The script will try to plot each of these from every file. If a variable
# does not exist in a particular file, it will be skipped automatically.
VARIABLES_TO_PLOT = [
    "chi", "K", "lapse", "Ham", 
    "h11", "h12", "h13", "h22", "h23", "h33",
    "A11", "A12", "A13", "A22", "A23", "A33",
    "Weyl4_Re", "Weyl4_Im"
]

# Set the axis for the 2D slice plot ("x", "y", or "z")
SLICE_AXIS = "z"

# Set the width of the plot window in code units.
PLOT_WIDTH = 32.0

# =========================================================================
# --- Main Script Logic (no changes needed below) ---
# =========================================================================

def get_center(ds):
    """Gets the domain center from a yt dataset."""
    if hasattr(ds, 'domain_right_edge'):
        return ds.domain_right_edge / 2.0
    return None

def produce_slice_plot(ds, variable_name):
    """
    Creates and saves a single slice plot for a given variable and dataset.
    """
    # Check if the requested variable exists in this specific HDF5 file
    available_fields = [field[1] for field in ds.field_list]
    if variable_name not in available_fields:
        print(f"  - Skipping variable '{variable_name}' (not found in this file).")
        return

    print(f"  + Plotting '{variable_name}'...")
    
    # Create the SlicePlot object
    center = get_center(ds)
    slc = yt.SlicePlot(ds, SLICE_AXIS, ('chombo', variable_name), center=center)
    
    # --- Apply specific visual settings for different variables ---
    if variable_name.startswith("h") or variable_name == "chi":
        slc.set_cmap(field=variable_name, cmap="viridis")
    elif variable_name == "lapse":
        slc.set_cmap(field=variable_name, cmap="plasma")
    else: # For K, Ham, Aij, etc.
        slc.set_cmap(field=variable_name, cmap="RdBu_r")
    
    # Set plot labels and annotations
    slc.set_xlabel(f"{SLICE_AXIS}-axis (1/m)")
    slc.set_ylabel("y-axis (1/m)" if SLICE_AXIS != "y" else "x-axis (1/m)")
    slc.set_colorbar_label(variable_name, variable_name)
    slc.annotate_title(f"{variable_name} at t = {ds.current_time:.3f}")
    
    # Set plot dimensions and resolution
    slc.set_width(PLOT_WIDTH)
    slc.set_buff_size(1024)
    
    # Create the output directory if it doesn't exist
    output_directory = f"plots_{variable_name}"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Save the plot
    slc.save(f"{output_directory}/")

def main():
    """
    Main function to orchestrate the serial plotting.
    """
    # Use a non-interactive backend suitable for saving files
    matplotlib.use("Agg")

    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Plot 2D slices from GRChombo HDF5 files.")
    parser.add_argument(
        "--data_dir",
        type=str,
        default="/home/nik/GRChombo/Examples/Wormhole_MT/simulation_output/hdf5/",
        help="Path to the directory containing HDF5 plot files."
    )
    args = parser.parse_args()

    # Construct the file pattern from the provided data directory
    data_path_pattern = os.path.join(args.data_dir, "Wormhole_p_*.3d.hdf5")

    # Load the dataset series. In serial mode, this creates a list of all files.
    try:
        ts = yt.load(data_path_pattern)
        print(f"Found {len(ts)} HDF5 files to process in '{data_path_pattern}'")
    except Exception as e:
        print(f"ERROR: Could not load data from pattern '{data_path_pattern}'")
        print(f"Please check that the path is correct and files exist. Details: {e}")
        return

    # The main serial loop. This will iterate through each file one by one.
    for i, ds in enumerate(ts):
        print(f"\n--- Processing file {i+1} of {len(ts)} (t = {ds.current_time:.3f}) ---")
        # Loop through the list of variables we want to plot
        for var_name in VARIABLES_TO_PLOT:
            try:
                produce_slice_plot(ds, var_name)
            except Exception as e:
                print(f"  ! FAILED to plot '{var_name}': {e}")

    print("\n===================================")
    print("All plotting tasks complete.")
    print("===================================")

# This ensures the main function is called when the script is executed
if __name__ == "__main__":
    main()