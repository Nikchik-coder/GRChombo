#!/usr/bin/env python3
"""
Hamiltonian Constraint Animation for GRChombo
Creates animations and plots of the Hamiltonian constraint violation over time
"""

import yt
import matplotlib.pyplot as plt
import numpy as np
import argparse
import os
import glob
import imageio
from datetime import datetime

def plot_hamiltonian_slice(file_path, output_dir=".", show_grid=True):
    """
    Loads a GRChombo HDF5 plot file and creates a 2D slice plot of the
    Hamiltonian constraint 'Ham'. This version uses syntax compatible with
    older yt versions that have these specific AttributeErrors.

    Args:
        file_path (str): The full path to the HDF5 plot file.
        output_dir (str): The directory to save the output PNG image.
        show_grid (bool): Whether to show the AMR grid structure.
        
    Returns:
        str: Path to the saved image file, or None if failed
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        return None

    print(f"Loading file: {file_path}")
    
    try:
        # --- 1. Load Data with YT ---
        ds = yt.load(file_path)

        # --- 2. Create a Slice Plot Object ---
        field_to_plot = ("chombo", "Ham")
        
        if field_to_plot not in ds.field_list:
            print(f"Error: Field '{field_to_plot[1]}' not found in the dataset.")
            print("Available fields are:")
            for field in ds.field_list:
                print(f"  - {field[1]}")
            return None
            
        slc = yt.SlicePlot(ds, "z", [field_to_plot])

        # --- 3. Customize the Plot (Syntax for your yt version) ---
        
        # Set the colormap for the specified field
        slc.set_cmap(field_to_plot, 'plasma')
        
        # Set the color scale to logarithmic
        slc.set_log(field_to_plot, True, linthresh=1e-10)
        
        # Set the color bar limits
        # We find the min/max of the data in the slice to set robust limits
        data = slc.frb[field_to_plot]
        min_val = np.min(data[data > 0]) if np.any(data > 0) else 1e-9
        max_val = np.max(data) if np.any(data > 0) else 1e-1
        slc.set_zlim(field_to_plot, min_val, max_val)

        # Annotate the plot with a title and AMR grid patches
        sim_time = ds.current_time.to_value()
        slc.annotate_title(f"Hamiltonian Constraint at t = {sim_time:.2f}")
        
        if show_grid:
            slc.annotate_grids()
        
        # Set the figure size
        slc.set_figure_size(8)

        # --- 4. Save the Plot ---
        file_basename = os.path.basename(file_path)
        output_filename = f"hamiltonian_{file_basename.replace('.3d.hdf5', '.png')}"
        output_path = os.path.join(output_dir, output_filename)
        
        # The save command is universal
        slc.save(output_path, mpl_kwargs={"dpi": 200})
        
        print(f"Saved plot to: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def find_hamiltonian_files(pattern="Wormhole_p_*.3d.hdf5", base_dir=None):
    """
    Find all Hamiltonian constraint HDF5 files matching the pattern
    
    Args:
        pattern (str): File pattern to search for
        base_dir (str): Directory to search in
        
    Returns:
        list: Sorted list of file paths
    """
    if base_dir:
        files = glob.glob(os.path.join(base_dir, pattern))
    else:
        files = glob.glob(pattern)
        
    if not files:
        # Try common subdirectories
        search_dirs = [
            "/home/nik/GRChombo_runs/Wormhole_Collapse/hdf5/",
            "hdf5", "output", "data", "../hdf5", "../output"
        ]
        for subdir in search_dirs:
            if os.path.exists(subdir):
                files = glob.glob(os.path.join(subdir, pattern))
                if files:
                    break
    
    return sorted(files)

def create_hamiltonian_animation(output_dir="hamiltonian_plots", file_pattern="Wormhole_p_*.3d.hdf5", 
                               max_files=50, duration=0.5, show_grid=True, base_dir=None):
    """
    Create an animation of the Hamiltonian constraint evolution
    
    Args:
        output_dir (str): Directory to save individual plots and animation
        file_pattern (str): Pattern to match HDF5 files
        max_files (int): Maximum number of files to process
        duration (float): Duration per frame in seconds
        show_grid (bool): Whether to show AMR grid structure
        base_dir (str): Base directory to search for files
        
    Returns:
        str: Path to the created animation file
    """
    # Find HDF5 files
    hdf5_files = find_hamiltonian_files(file_pattern, base_dir)
    
    if not hdf5_files:
        print(f"No HDF5 files found matching pattern: {file_pattern}")
        if base_dir:
            print(f"Searched in: {base_dir}")
        print("Please ensure your HDF5 files are accessible or specify the correct pattern.")
        return None
    
    # Limit number of files for reasonable animation length
    if len(hdf5_files) > max_files:
        step = len(hdf5_files) // max_files
        hdf5_files = hdf5_files[::step]
    
    print(f"Creating Hamiltonian constraint animation with {len(hdf5_files)} frames...")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate individual plots
    image_files = []
    for i, hdf5_file in enumerate(hdf5_files):
        print(f"Processing frame {i+1}/{len(hdf5_files)}: {os.path.basename(hdf5_file)}")
        
        image_path = plot_hamiltonian_slice(hdf5_file, output_dir, show_grid)
        if image_path and os.path.exists(image_path):
            image_files.append(image_path)
    
    if not image_files:
        print("No valid images were created!")
        return None
    
    # Create animation
    print(f"Creating GIF animation from {len(image_files)} images...")
    
    # Read images and create GIF
    images = []
    for img_path in image_files:
        try:
            images.append(imageio.imread(img_path))
        except Exception as e:
            print(f"Error reading {img_path}: {e}")
            continue
    
    if not images:
        print("No images could be read for animation!")
        return None
    
    # Save animation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    animation_path = os.path.join(output_dir, f"hamiltonian_animation_{timestamp}.gif")
    
    try:
        imageio.mimsave(animation_path, images, duration=duration)
        print(f"Animation saved to: {animation_path}")
        
        # Save metadata
        metadata_file = os.path.join(output_dir, f"animation_info_{timestamp}.txt")
        with open(metadata_file, 'w') as f:
            f.write(f"Hamiltonian Constraint Animation\n")
            f.write(f"================================\n\n")
            f.write(f"Creation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Source Files: {len(hdf5_files)} HDF5 files\n")
            f.write(f"Animation Frames: {len(images)}\n")
            f.write(f"Frame Duration: {duration} seconds\n")
            f.write(f"Total Duration: {len(images) * duration:.1f} seconds\n")
            f.write(f"Grid Overlay: {'Yes' if show_grid else 'No'}\n")
            f.write(f"File Pattern: {file_pattern}\n")
            f.write(f"Animation File: {os.path.basename(animation_path)}\n")
        
        print(f"Animation metadata saved to: {metadata_file}")
        return animation_path
        
    except Exception as e:
        print(f"Error creating animation: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Generate Hamiltonian constraint plots and animations from GRChombo data."
    )
    parser.add_argument(
        "action",
        choices=["plot", "animate"],
        nargs="?", 
        default="plot",
        help="Action to perform: 'plot' for single plot, 'animate' for animation"
    )
    parser.add_argument(
        "file_path",
        nargs="?",
        help="Path to HDF5 file (for plot) or file pattern (for animate)"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="hamiltonian_plots",
        help="Directory to save output files"
    )
    parser.add_argument(
        "--max_files",
        type=int,
        default=50,
        help="Maximum number of files to use for animation"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=0.5,
        help="Duration per frame in seconds for animation"
    )
    parser.add_argument(
        "--no_grid",
        action="store_true",
        help="Don't show AMR grid overlay"
    )
    parser.add_argument(
        "--base_dir",
        type=str,
        default="/home/nik/GRChombo_runs/Wormhole_Collapse/hdf5/",
        help="Base directory to search for HDF5 files"
    )
    
    args = parser.parse_args()
    
    # If no action specified but file_path given, assume plot
    if args.file_path and args.action == "plot":
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)
            
        result = plot_hamiltonian_slice(
            args.file_path, 
            args.output_dir, 
            show_grid=not args.no_grid
        )
        if result:
            print(f"Plot created successfully: {result}")
    
    elif args.action == "animate":
        file_pattern = args.file_path if args.file_path else "Wormhole_p_*.3d.hdf5"
        
        result = create_hamiltonian_animation(
            output_dir=args.output_dir,
            file_pattern=file_pattern,
            max_files=args.max_files,
            duration=args.duration,
            show_grid=not args.no_grid,
            base_dir=args.base_dir
        )
        if result:
            print(f"Animation created successfully: {result}")
    
    else:
        # Default behavior - try to create a single plot
        if args.file_path:
            if not os.path.exists(args.output_dir):
                os.makedirs(args.output_dir)
                
            result = plot_hamiltonian_slice(
                args.file_path, 
                args.output_dir, 
                show_grid=not args.no_grid
            )
            if result:
                print(f"Plot created successfully: {result}")
        else:
            print("Please specify a file path for plotting or use 'animate' action for animation")

if __name__ == "__main__":
    main()