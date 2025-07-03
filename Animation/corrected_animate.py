#!/usr/bin/env python3
"""
Corrected animation script for binary black hole data
"""

import h5py
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import glob
import os

def read_chombo_data(filename, level='level_0'):
    """Read Chombo AMR data properly (copied from corrected_plot.py)"""
    with h5py.File(filename, 'r') as f:
        level_group = f[level]
        
        # Get attributes
        attrs = level_group['data_attributes'].attrs
        n_comps = attrs['comps']
        ghost = attrs['ghost']
        
        # Get data and boxes
        data = level_group['data:datatype=0'][:]
        boxes = level_group['boxes'][:]
        
        # For multiple boxes, we need to reconstruct the grid
        # For now, let's use the first box (coarsest level usually has 1 box)
        box = boxes[0]
        nx = box['hi_i'] - box['lo_i'] + 1
        ny = box['hi_j'] - box['lo_j'] + 1
        nz = box['hi_k'] - box['lo_k'] + 1
        
        # Add ghost zones
        nx_ghost = nx + 2 * ghost[0]
        ny_ghost = ny + 2 * ghost[1] 
        nz_ghost = nz + 2 * ghost[2]
        
        # Reshape data with ghost zones
        try:
            # Try components-last with ghost zones
            data_4d = data.reshape(nx_ghost, ny_ghost, nz_ghost, n_comps, order='F')
            
            # Extract non-ghost data
            if ghost[0] > 0 or ghost[1] > 0 or ghost[2] > 0:
                gx, gy, gz = ghost[0], ghost[1], ghost[2]
                data_4d = data_4d[gx:nx_ghost-gx, gy:ny_ghost-gy, gz:nz_ghost-gz, :]
            
            return data_4d, n_comps
        except:
            # Fallback to components-first with ghost zones
            data_4d = data.reshape(n_comps, nx_ghost, ny_ghost, nz_ghost, order='F')
            
            # Extract non-ghost data
            if ghost[0] > 0 or ghost[1] > 0 or ghost[2] > 0:
                gx, gy, gz = ghost[0], ghost[1], ghost[2]
                data_4d = data_4d[:, gx:nx_ghost-gx, gy:ny_ghost-gy, gz:nz_ghost-gz]
            
            return data_4d, n_comps

def read_slice(filename, component=0, slice_axis=2, level='level_0'):
    """Read a specific slice from a file"""
    data_4d, n_comps = read_chombo_data(filename, level)
    
    if component >= n_comps:
        component = 0
    
    # Extract the component
    if len(data_4d.shape) == 4:
        if data_4d.shape[3] == n_comps:  # (nx,ny,nz,comps)
            comp_data = data_4d[:, :, :, component]
        else:  # (comps,nx,ny,nz)
            comp_data = data_4d[component, :, :, :]
    
    # Extract slice
    slice_index = comp_data.shape[slice_axis] // 2
    
    if slice_axis == 0:
        slice_data = comp_data[slice_index, :, :]
    elif slice_axis == 1:
        slice_data = comp_data[:, slice_index, :]
    else:  # slice_axis == 2
        slice_data = comp_data[:, :, slice_index]
    
    return slice_data

def create_corrected_animation(component=0, slice_axis=2, max_files=50, save_gif=True, use_data_files=False, level='level_0'):
    """Create corrected animation"""
    
    # Find files
    if use_data_files:
        files = sorted(glob.glob("hdf5/BinaryBH_*.hdf5"))
        file_type = "BinaryBH"
    else:
        files = sorted(glob.glob("hdf5/BinaryBHPlot_*.hdf5"))
        file_type = "BinaryBHPlot"
    
    if not files:
        print("No HDF5 files found!")
        return
    
    # Limit number of files
    if len(files) > max_files:
        step = len(files) // max_files
        files = files[::step]
    
    print(f"Creating animation with {len(files)} frames...")
    print(f"File type: {file_type}, Component: {component}, Slice axis: {slice_axis}")
    
    # Read first frame to get dimensions and check component count
    first_data, n_comps = read_chombo_data(files[0], level)
    print(f"Available components: 0 to {n_comps-1}")
    
    if component >= n_comps:
        print(f"Component {component} not available, using 0")
        component = 0
    
    first_slice = read_slice(files[0], component, slice_axis, level)
    
    # Calculate global min/max for consistent color scale
    print("Calculating global data range...")
    all_slices = []
    for i, filename in enumerate(files[::5]):  # Sample every 5th file
        try:
            slice_data = read_slice(filename, component, slice_axis, level)
            all_slices.append(slice_data)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            continue
        if i % 10 == 0:
            print(f"  Processed {i+1}/{len(files[::5])} files")
    
    if not all_slices:
        print("No valid data found!")
        return
    
    all_slices = np.array(all_slices)
    vmin, vmax = np.min(all_slices), np.max(all_slices)
    print(f"Global range: {vmin:.3e} to {vmax:.3e}")
    
    # Set up the figure
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create initial plot
    if vmax > vmin:
        if vmin > 0 and vmax/vmin > 100:
            from matplotlib.colors import LogNorm
            im = ax.imshow(first_slice.T, origin='lower', cmap='plasma', 
                          norm=LogNorm(vmin=max(vmin, vmax/1e6), vmax=vmax),
                          animated=True)
        else:
            im = ax.imshow(first_slice.T, origin='lower', cmap='plasma', 
                          vmin=vmin, vmax=vmax, animated=True)
    else:
        im = ax.imshow(first_slice.T, origin='lower', cmap='plasma', animated=True)
    
    # Add colorbar
    cbar = plt.colorbar(im, shrink=0.8)
    
    # Labels
    axis_names = ['X', 'Y', 'Z']
    if slice_axis == 0:
        ax.set_xlabel('Y'), ax.set_ylabel('Z')
        slice_name = 'X'
    elif slice_axis == 1:
        ax.set_xlabel('X'), ax.set_ylabel('Z')
        slice_name = 'Y'
    else:
        ax.set_xlabel('X'), ax.set_ylabel('Y')
        slice_name = 'Z'
    
    title = ax.text(0.5, 1.02, '', transform=ax.transAxes, ha='center', fontsize=12)
    
    def animate(frame):
        """Animation function"""
        try:
            filename = files[frame]
            slice_data = read_slice(filename, component, slice_axis, level)
            
            # Update image
            im.set_array(slice_data.T)
            
            # Update title
            file_num = os.path.basename(filename).split('_')[-1].split('.')[0]
            title.set_text(f'Binary BH - {file_type} Component {component}\n'
                          f'{slice_name}-slice, Frame {frame+1}/{len(files)}, File: {file_num}')
            
            return [im, title]
        
        except Exception as e:
            print(f"Error in frame {frame}: {e}")
            return [im, title]
    
    # Create animation
    print("Creating animation...")
    anim = animation.FuncAnimation(fig, animate, frames=len(files), 
                                  interval=200, blit=True, repeat=True)
    
    # Save or show
    if save_gif:
        output_file = f"corrected_animation_{file_type}_comp{component}_axis{slice_axis}.gif"
        print(f"Saving animation as {output_file}...")
        
        anim.save(output_file, writer='pillow', fps=5)
        print(f"Animation saved as {output_file}")
    else:
        print("Displaying animation...")
        plt.show()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Create corrected animation')
    parser.add_argument('--component', type=int, default=0, help='Component to animate')
    parser.add_argument('--slice-axis', type=int, default=2, choices=[0,1,2], help='Slice axis')
    parser.add_argument('--max-frames', type=int, default=40, help='Maximum frames')
    parser.add_argument('--no-save', action='store_true', help='Display instead of saving')
    parser.add_argument('--use-data-files', action='store_true', help='Use BinaryBH files (25 comps)')
    parser.add_argument('--level', default='level_0', help='AMR level')
    
    args = parser.parse_args()
    
    create_corrected_animation(
        component=args.component,
        slice_axis=args.slice_axis,
        max_files=args.max_frames,
        save_gif=not args.no_save,
        use_data_files=args.use_data_files,
        level=args.level
    )

if __name__ == "__main__":
    main() 