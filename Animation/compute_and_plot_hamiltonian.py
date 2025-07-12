import yt
import numpy as np
import matplotlib.pyplot as plt
import argparse
import os
import glob

def get_hamiltonian_norm_vs_time(sim_dir, plot_prefix="Wormhole_p_"):
    """
    Loops through all plot files, calculates the L2 norm of the Hamiltonian
    constraint for each, and returns the results. This version uses a manual
    L2 norm calculation for maximum compatibility across yt versions.

    Args:
        sim_dir (str): The path to the main simulation output directory.
        plot_prefix (str): The prefix for the plot files.

    Returns:
        A tuple containing two lists: (times, ham_norms)
    """
    search_path = os.path.join(sim_dir, "hdf5", f"{plot_prefix}*.3d.hdf5")
    plot_files = sorted(glob.glob(search_path))

    if not plot_files:
        print(f"Error: No plot files found at '{search_path}'")
        return None, None

    print(f"Found {len(plot_files)} plot files to process...")

    times = []
    ham_norms = []

    for file_path in plot_files:
        try:
            ds = yt.load(file_path)
            
            if ("chombo", "Ham") not in ds.field_list:
                print(f"Skipping {os.path.basename(file_path)}: 'Ham' field not found.")
                continue

            # --- Manual L2 Norm Calculation (Most Compatible Method) ---
            # Create a data object for the entire domain.
            ad = ds.all_data()
            
            # Get the Hamiltonian values, cell volumes, and flatten them.
            # We must convert them to numpy arrays to do math.
            ham_values = ad[("chombo", "Ham")].to_value()
            cell_volumes = ad[("index", "cell_volume")].to_value()
            
            # Calculate the L2 norm: sqrt( sum( (field_value^2) * cell_volume ) )
            ham_sq_times_vol = (ham_values**2) * cell_volumes
            l2_norm = np.sqrt(np.sum(ham_sq_times_vol))
            
            times.append(ds.current_time.to_value())
            ham_norms.append(l2_norm)
            
            print(f"Time: {ds.current_time.to_value():.2f}, L2 Norm(Ham): {l2_norm:.3e}")

        except Exception as e:
            print(f"Could not process {file_path}. Error: {e}")

    return times, ham_norms

def plot_norm_vs_time(times, norms, output_dir="."):
    """
    Generates a plot of the L2 norm vs. time with clean white background.
    """
    if not times or not norms:
        print("No data to plot.")
        return

    # Use clean white background style
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Set white background
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    # Enhanced plot styling
    ax.plot(times, norms, marker='o', linestyle='-', markersize=6, 
            linewidth=2.5, color='#2E86AB', markerfacecolor='#A23B72', 
            markeredgecolor='white', markeredgewidth=1.5, alpha=0.8)
    
    ax.set_yscale('log')
    
    # Enhanced labels and title
    ax.set_xlabel("Time", fontsize=16, fontweight='bold', color='#333333')
    ax.set_ylabel("L2 Norm of Hamiltonian Constraint", fontsize=16, fontweight='bold', color='#333333')
    ax.set_title("Hamiltonian Constraint Violation vs. Time", fontsize=18, fontweight='bold', 
                 color='#2E2E2E', pad=20)
    
    # Enhanced tick styling
    ax.tick_params(axis='both', which='major', labelsize=13, colors='#333333', width=1.2)
    ax.tick_params(axis='both', which='minor', labelsize=11, colors='#666666', width=0.8)
    
    # Add subtle grid
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.8, color='#CCCCCC')
    ax.set_axisbelow(True)
    
    # Enhanced spines
    for spine in ax.spines.values():
        spine.set_color('#666666')
        spine.set_linewidth(1.2)
    
    # Tight layout with padding
    plt.tight_layout(pad=2.0)

    output_filename = os.path.join(output_dir, "hamiltonian_norm_vs_time.png")
    plt.savefig(output_filename, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    print(f"\nSaved plot to: {output_filename}")
    plt.close(fig)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Calculate and plot the L2 norm of the Hamiltonian constraint over a full simulation run."
    )
    parser.add_argument(
        "sim_dir",
        type=str,
        help="The full path to the simulation output directory (e.g., '/home/nik/GRChombo_runs/Wormhole_Collapse')."
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="Wormhole_p_",
        help="The plot file prefix."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=".",
        help="Directory to save the final plot. Defaults to the current directory."
    )
    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    times, ham_norms = get_hamiltonian_norm_vs_time(args.sim_dir, args.prefix)
    plot_norm_vs_time(times, ham_norms, args.output_dir)