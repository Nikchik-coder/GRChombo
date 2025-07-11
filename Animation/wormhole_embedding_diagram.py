import yt
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import cumulative_trapezoid
import os
import argparse
import glob
import imageio
from datetime import datetime

# Set plotting style
plt.style.use('dark_background')

def plot_embedding_diagram(file_path, output_dir=".", frame_number=None, fixed_limits=None):
    """
    Loads a GRChombo HDF5 file, computes the embedding diagram for the
    Einstein-Rosen bridge, and saves a 3D plot.

    Args:
        file_path (str): The full path to the HDF5 plot file.
        output_dir (str): The directory to save the output image.
        frame_number (int): Frame number for animation (if None, uses original naming)
        fixed_limits (dict): Fixed axis limits for consistent animation frames
    Returns:
        tuple: (sim_time, axis_limits) for use in animation consistency
    """
    # --- 1. Load Data with YT ---
    ds = yt.load(file_path)
    
    # Get the simulation time for the plot title
    sim_time = ds.current_time.d

    # Create a 1D slice (a ray) of data along the x-axis from the center outwards
    # This gives us the values of chi along a line.
    center = ds.domain_center
    start_point = center
    end_point = [ds.domain_right_edge[0], center[1], center[2]]
    ray = ds.ray(start_point, end_point)

    # Sort the ray by the x-coordinate to ensure correct order for integration
    sorted_indices = np.argsort(ray["x"])
    radius = np.array(ray["x"][sorted_indices])
    chi = np.array(ray["chi"][sorted_indices])

    # The puncture is at r=0, where chi can be unstable. Start integration
    # from a small radius away from the center to ensure stability.
    min_radius_index = np.where(radius > 0.05)[0][0]
    radius = radius[min_radius_index:]
    chi = chi[min_radius_index:]

    # --- 2. Calculate the Embedding Function ---
    # The formula for the embedding z(r) is derived from the spatial metric in
    # isotropic coordinates: dL^2 = psi^4 (dr^2 + r^2 d(angles)^2)
    # We want to embed this in 3D Euclidean space: dL^2 = dz^2 + dr^2
    # This requires dz/dr = sqrt(psi^4 - 1), where psi = chi^(-1/4)
    
    psi = chi**(-0.25)
    
    # We need to be careful where psi^4 < 1, which can happen due to numerical errors.
    # We take the max with 0 to avoid taking the square root of a negative number.
    integrand = np.sqrt(np.maximum(0, psi**4 - 1.0))
    
    # Perform the cumulative integration to get z(r)
    # This gives the height of the "funnel" at each radius r.
    z = cumulative_trapezoid(integrand, radius, initial=0)

    # --- 3. Prepare for 3D Plotting ---
    # Create a 2D grid of polar coordinates for the surface plot
    theta = np.linspace(0, 2 * np.pi, 100)
    R, THETA = np.meshgrid(radius, theta)

    # Convert polar to Cartesian coordinates for the plot
    X = R * np.cos(THETA)
    Y = R * np.sin(THETA)
    
    # Z will be the same for all angles theta, it only depends on the radius R.
    # We need to create a 2D array for Z that matches the shape of X and Y.
    Z = np.tile(z, (len(theta), 1))

    # --- 4. THE KEY STEP: Create the Mirrored Universe ---
    # To show the full "tunnel", we just need to plot the mirror image of our
    # universe's embedding. This represents the second sheet of spacetime.
    Z_mirror = -Z

    # --- 5. Create and Save the 3D Plot ---
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Plot the top sheet (our universe)
    ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.9, edgecolor='none')
    
    # Plot the bottom sheet (the "other" universe)
    ax.plot_surface(X, Y, Z_mirror, cmap='cividis', alpha=0.9, edgecolor='none')

    # Set plot aesthetics
    ax.set_xlabel('x', fontsize=14, labelpad=10)
    ax.set_ylabel('y', fontsize=14, labelpad=10)
    ax.set_zlabel('Embedding z', fontsize=14, labelpad=10)
    ax.set_title(f'Einstein-Rosen Bridge Embedding\nTime = {sim_time:.2f}', fontsize=16)
    
    # Calculate axis limits for consistency across frames
    current_limits = {
        'x_range': (X.min(), X.max()),
        'y_range': (Y.min(), Y.max()),
        'z_range': (Z_mirror.min(), Z.max())
    }
    
    # Use fixed limits if provided (for animation consistency)
    if fixed_limits is not None:
        ax.set_xlim(fixed_limits['x_range'])
        ax.set_ylim(fixed_limits['y_range'])
        ax.set_zlim(fixed_limits['z_range'])
    else:
        # Set a consistent aspect ratio
        max_range = np.array([X.max()-X.min(), Y.max()-Y.min(), (Z.max()-Z.min()) * 2]).max() / 2.0
        mid_x = (X.max()+X.min()) * 0.5
        mid_y = (Y.max()+Y.min()) * 0.5
        mid_z = 0
        ax.set_xlim(mid_x - max_range, mid_x + max_range)
        ax.set_ylim(mid_y - max_range, mid_y + max_range)
        ax.set_zlim(mid_z - max_range, mid_z + max_range)

    # Set viewing angle
    ax.view_init(elev=20, azim=-70)
    ax.dist = 11

    # Save the figure
    if frame_number is not None:
        # For animation frames, use numbered naming
        output_filename = f"frame_{frame_number:04d}.png"
    else:
        # For single files, use original naming
        file_basename = os.path.basename(file_path)
        output_filename = f"embedding_{file_basename.replace('.3d.hdf5', '.png')}"
    
    plt.savefig(os.path.join(output_dir, output_filename), dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    if frame_number is not None:
        print(f"Saved frame {frame_number:04d} (t={sim_time:.2f})")
    else:
        print(f"Saved embedding diagram to {os.path.join(output_dir, output_filename)}")
    
    return sim_time, current_limits

def process_all_files_and_create_animation(hdf5_directory, output_dir="./embedding_animation", duration=0.3):
    """
    Process all HDF5 files in a directory and create an animation.
    
    Args:
        hdf5_directory (str): Directory containing HDF5 files
        output_dir (str): Directory to save frames and animation
        duration (float): Duration per frame in seconds
    """
    # Find all HDF5 files
    hdf5_pattern = os.path.join(hdf5_directory, "*.hdf5")
    hdf5_files = sorted(glob.glob(hdf5_pattern))
    
    if not hdf5_files:
        print(f"No HDF5 files found in {hdf5_directory}")
        return
    
    print(f"Found {len(hdf5_files)} HDF5 files")
    
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create frames subdirectory
    frames_dir = os.path.join(output_dir, "frames")
    if not os.path.exists(frames_dir):
        os.makedirs(frames_dir)
    
    # First pass: determine consistent axis limits by processing a few files
    print("Determining consistent axis limits...")
    sample_files = hdf5_files[::max(1, len(hdf5_files)//5)]  # Sample every 5th file or so
    all_limits = []
    
    for file_path in sample_files[:5]:  # Sample up to 5 files
        try:
            _, limits = plot_embedding_diagram(file_path, "/tmp", fixed_limits=None)
            all_limits.append(limits)
        except Exception as e:
            print(f"Warning: Could not process sample file {file_path}: {e}")
    
    # Calculate global limits
    if all_limits:
        global_limits = {
            'x_range': (min(l['x_range'][0] for l in all_limits), max(l['x_range'][1] for l in all_limits)),
            'y_range': (min(l['y_range'][0] for l in all_limits), max(l['y_range'][1] for l in all_limits)),
            'z_range': (min(l['z_range'][0] for l in all_limits), max(l['z_range'][1] for l in all_limits))
        }
        
        # Add some padding
        x_padding = (global_limits['x_range'][1] - global_limits['x_range'][0]) * 0.1
        y_padding = (global_limits['y_range'][1] - global_limits['y_range'][0]) * 0.1
        z_padding = (global_limits['z_range'][1] - global_limits['z_range'][0]) * 0.1
        
        global_limits = {
            'x_range': (global_limits['x_range'][0] - x_padding, global_limits['x_range'][1] + x_padding),
            'y_range': (global_limits['y_range'][0] - y_padding, global_limits['y_range'][1] + y_padding),
            'z_range': (global_limits['z_range'][0] - z_padding, global_limits['z_range'][1] + z_padding)
        }
    else:
        global_limits = None
    
    # Second pass: generate all frames with consistent limits
    print(f"Generating {len(hdf5_files)} animation frames...")
    successful_frames = []
    times = []
    
    for i, file_path in enumerate(hdf5_files):
        try:
            sim_time, _ = plot_embedding_diagram(file_path, frames_dir, frame_number=i, fixed_limits=global_limits)
            successful_frames.append(os.path.join(frames_dir, f"frame_{i:04d}.png"))
            times.append(sim_time)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    if not successful_frames:
        print("No frames were successfully created!")
        return
    
    # Create animation
    print(f"Creating animation from {len(successful_frames)} frames...")
    try:
        # Read all frames
        images = []
        for frame_path in successful_frames:
            img = imageio.imread(frame_path)
            images.append(img)
        
        # Save as GIF
        animation_path = os.path.join(output_dir, "wormhole_embedding_animation.gif")
        imageio.mimsave(animation_path, images, duration=duration)
        
        # Get file size for reporting
        file_size = os.path.getsize(animation_path) / (1024*1024)  # MB
        print(f"✅ Animation saved: {animation_path} ({file_size:.1f} MB)")
        
        # Save metadata
        metadata_path = os.path.join(output_dir, "animation_info.txt")
        with open(metadata_path, 'w') as f:
            f.write(f"Wormhole Embedding Animation\n")
            f.write(f"============================\n\n")
            f.write(f"Creation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Source Directory: {hdf5_directory}\n")
            f.write(f"Total Frames: {len(successful_frames)}\n")
            f.write(f"Animation Duration: {duration} seconds per frame\n")
            f.write(f"Time Range: {min(times):.2f} to {max(times):.2f}\n")
            f.write(f"Output Files:\n")
            f.write(f"  - Animation: wormhole_embedding_animation.gif\n")
            f.write(f"  - Frames: frames/frame_XXXX.png\n")
        
        print(f"📄 Metadata saved: {metadata_path}")
        print(f"📁 Individual frames saved in: {frames_dir}")
        
    except Exception as e:
        print(f"❌ Error creating animation: {e}")

def find_hdf5_directories():
    """Find directories containing HDF5 files"""
    potential_dirs = []
    
    # Check common locations
    common_paths = [
        "/home/nik/GRChombo_runs/*/hdf5",
        "/home/nik/GRChombo_output/*/hdf5",
        "./hdf5",
        "../*/hdf5"
    ]
    
    for pattern in common_paths:
        dirs = glob.glob(pattern)
        for d in dirs:
            if glob.glob(os.path.join(d, "*.hdf5")):
                potential_dirs.append(d)
    
    return potential_dirs

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate embedding diagrams and animations from GRChombo plot files.")
    parser.add_argument("input", type=str, nargs='?', help="Path to HDF5 file or directory containing HDF5 files")
    parser.add_argument("--output_dir", type=str, default="./embedding_animation", help="Directory to save output")
    parser.add_argument("--duration", type=float, default=0.3, help="Duration per frame in seconds (for animation)")
    parser.add_argument("--list-dirs", action="store_true", help="List available HDF5 directories")
    parser.add_argument("--single", action="store_true", help="Process single file instead of creating animation")
    
    args = parser.parse_args()
    
    # List available directories
    if args.list_dirs:
        dirs = find_hdf5_directories()
        if dirs:
            print("Available HDF5 directories:")
            for d in dirs:
                count = len(glob.glob(os.path.join(d, "*.hdf5")))
                print(f"  {d} ({count} files)")
        else:
            print("No HDF5 directories found")
        exit(0)
    
    # Handle input
    if not args.input:
        # Try to auto-detect
        dirs = find_hdf5_directories()
        if dirs:
            args.input = dirs[0]
            print(f"Auto-detected HDF5 directory: {args.input}")
        else:
            print("No input specified and no HDF5 directories found.")
            print("Usage:")
            print("  Single file: python wormhole_embedding_diagram.py file.hdf5 --single")
            print("  Animation:   python wormhole_embedding_diagram.py /path/to/hdf5/directory")
            print("  List dirs:   python wormhole_embedding_diagram.py --list-dirs")
            exit(1)
    
    # Check if input is file or directory
    if os.path.isfile(args.input) or args.single:
        # Single file mode
        if not os.path.exists(args.input):
            print(f"Error: File not found at {args.input}")
            exit(1)
        
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)
        plot_embedding_diagram(args.input, args.output_dir)
        
    elif os.path.isdir(args.input):
        # Animation mode
        print(f"Creating wormhole embedding animation from {args.input}")
        process_all_files_and_create_animation(args.input, args.output_dir, args.duration)
        
    else:
        print(f"Error: {args.input} is neither a file nor a directory")