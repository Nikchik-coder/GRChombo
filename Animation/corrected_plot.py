# corrected_plot.py
# Fixed plotting script for GRChombo Binary Black Hole HDF5 files
# Fixed data path and added more suitable fields for BH visualization

# Load the modules
import yt
import os
import matplotlib

def get_center(ds):
    # Small function that gets center for both single
    # or multiple dataset
    #   input: ds .. YT dataset
    #   return: center ... vector with center of box
    center = None
    if hasattr(ds,'domain_right_edge'):
        center = ds.domain_right_edge / 2.0
    elif hasattr(ds[0],'domain_right_edge'):
        center = ds[0].domain_right_edge / 2.0
    return center

matplotlib.use("Agg")

# Enable Parallelism
yt.enable_parallelism()

# FIXED: Correct data file location for the external data directory
data_location = "/home/nik/GRChombo_runs/BBH_run_2/hdf5/BinaryBHChk_*.3d.hdf5"  # Data file location
# Loading dataset
ts = yt.load(data_location)

# Choose what fields you want to plot
# Common fields for binary black hole simulations:
# "chi" - conformal factor (shows spacetime structure)
# "lapse" - lapse function (shows time dilation)  
# "K" - trace of extrinsic curvature
variable_names = ["chi", "lapse", "K"]

# Choose the center of the plot
# "c" ... center of the box
# "max" ... maximum of the plotted field
# ("max",field) ... maximum of different field
# [x,y,z] ... custom center
center = get_center(ts)
center[2] = 0  # Set z=0 for equatorial plane

# Orthogonal Axis (plot z-slice through equatorial plane)
axis = "z"

# mkdir the plot directories (and optionally clean them)
if yt.is_root():
    for name in variable_names:
        if not os.path.exists(name):
            os.mkdir(name)
        else:
            # Clean existing plots to avoid mixing data from different runs
            import glob
            old_plots = glob.glob(f"{name}/*.png")
            if old_plots:
                print(f"Cleaning {len(old_plots)} old plots from {name}/ directory")
                for plot_file in old_plots:
                    os.remove(plot_file)

# Define a basic plot
def produce_slice_plot(data, variable, axis = axis):
    slc = yt.SlicePlot(data, axis, ('chombo',variable), center = center)
    
    # Set appropriate scaling for different fields
    if variable == "chi":
        slc.set_log(variable, False)
        slc.set_cmap(field=variable, cmap="viridis")
        slc.set_zlim(variable, 0.0, 1.0)  # Chi typically ranges 0-1
    elif variable == "lapse":
        slc.set_log(variable, False) 
        slc.set_cmap(field=variable, cmap="plasma")
        slc.set_zlim(variable, 0.0, 1.0)  # Lapse typically ranges 0-1
    elif variable == "K":
        slc.set_log(variable, False)
        slc.set_cmap(field=variable, cmap="RdBu_r")
        # K can be positive or negative, use symmetric scale
    else:
        slc.set_log(variable, False)
        slc.set_cmap(field=variable, cmap="dusk")
    
    # Plot Boxes (uncomment next line to activate)
    #slc.annotate_grids()
    # Plot Grid points (uncomment next line to activate)
    #slc.annotate_cell_edges()
    # Plot contours (uncomment next line to activate)
    #slc.annotate_contour(variable)
    
    # Resolution of the fixed resolution mesh used for plotting
    slc.set_buff_size(1024)
    
    # Labels
    slc.set_xlabel(r"x $\left[\frac{1}{m}\right]$")
    slc.set_ylabel(r"y $\left[\frac{1}{m}\right]$")
    slc.set_colorbar_label(variable, variable)
    
    # Add time annotation
    slc.annotate_text(
        (0.13, 0.92),
        ("time = " + str(float(data.current_time)) + " 1/m"),
        coord_system="figure",
        text_args={"color": "white"},
    )
    
    # Set size of plotted window
    slc.set_width(10)
    slc.save(variable + "/")

# Loop over all files and plot
if hasattr(ts,'piter'):
    # CASE FOR MULTIPLE DATASETS (PARALLEL)
    for i in ts.piter():
        for name in variable_names:
            produce_slice_plot(i, name)
else:
    # CASE FOR SINGLE DATASET (NOT PARALLEL)
    if yt.is_root():
        for name in variable_names:
            produce_slice_plot(ts, name)

print(f"Plotting completed! Generated plots for {len(variable_names)} variables across {len(ts)} timesteps")
print(f"Available fields in simulation: {[field[1] for field in ts[0].field_list]}") 