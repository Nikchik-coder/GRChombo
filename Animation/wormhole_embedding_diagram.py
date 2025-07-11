#!/usr/bin/env python3
"""
Wormhole Embedding Diagram Visualization for GRChombo Simulations

This script creates the classic "funnel" embedding diagram for wormhole collapse,
showing how the Einstein-Rosen bridge throat pinches off over time.

Physical Theory:
- For a wormhole in isotropic coordinates, the metric in the equatorial plane is:
  ds² = ψ⁴(dr² + r²dφ²)
- The embedding surface z = z(r) satisfies: dz/dr = ±√(ψ⁴ - 1)
- The conformal factor ψ relates to the GRChombo variable chi as: chi = ψ⁻⁴
- As the wormhole collapses, the throat (minimum radius) shrinks until pinch-off

Created by: Claude Sonnet (AI Assistant)
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import h5py
import os
import glob
from scipy.interpolate import interp1d
from scipy.integrate import quad, cumulative_trapezoid
import imageio
import warnings
warnings.filterwarnings('ignore')

class WormholeEmbeddingVisualizer:
    """Class for creating embedding diagrams of wormhole collapse"""
    
    def __init__(self, data_pattern=None, output_dir="embedding_diagrams"):
        """Initialize with data file pattern"""
        self.data_pattern = self.find_data_pattern(data_pattern)
        self.output_dir = output_dir
        self.setup_output_directory()
        
        print("🌀 Wormhole Embedding Diagram Visualizer")
        print("=" * 50)
        print(f"Data pattern: {self.data_pattern}")
        print(f"Output directory: {self.output_dir}")
        
    def find_data_pattern(self, data_pattern=None):
        """Auto-detect wormhole simulation data files"""
        if data_pattern and glob.glob(data_pattern):
            return data_pattern
            
        # Search for wormhole data files
        search_patterns = [
            "/home/nik/GRChombo_runs/Wormhole_Collapse/hdf5/Wormhole_*.3d.hdf5",
            "Wormhole_*.3d.hdf5",
            "../Wormhole_*/hdf5/Wormhole_*.3d.hdf5",
            "*/Wormhole_*.3d.hdf5"
        ]
        
        for pattern in search_patterns:
            files = glob.glob(pattern)
            if files:
                print(f"Found {len(files)} wormhole data files using pattern: {pattern}")
                return pattern
                
        # Default pattern if no files found
        default_pattern = "/home/nik/GRChombo_runs/Wormhole_Collapse/hdf5/Wormhole_*.3d.hdf5"
        print(f"No data files found, using default pattern: {default_pattern}")
        return default_pattern
        
    def setup_output_directory(self):
        """Create output directory structure"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Created output directory: {self.output_dir}")
            
        subdirs = ["individual_frames", "data", "animations"]
        for subdir in subdirs:
            path = os.path.join(self.output_dir, subdir)
            if not os.path.exists(path):
                os.makedirs(path)
                
    def load_wormhole_data(self, filename):
        """Load wormhole data from HDF5 file using YT for proper Chombo data handling"""
        try:
            # Use YT to load Chombo data properly
            import yt
            
            ds = yt.load(filename)
            time = float(ds.current_time)
            
            # Get a covering grid (uniform grid covering the domain)
            # This will interpolate the AMR data onto a uniform grid
            level = 0  # Use base level
            left_edge = ds.domain_left_edge
            right_edge = ds.domain_right_edge
            dims = ds.domain_dimensions * (2**level)  # Resolution based on level
            
            covering_grid = ds.covering_grid(level, left_edge, dims)
            
            # Extract chi data
            chi_data = covering_grid[('chombo', 'chi')].v
            
            # Get coordinate information
            dx = float(ds.index.get_smallest_dx())
            
            # Create coordinate arrays
            nx, ny, nz = chi_data.shape
            domain_width = right_edge - left_edge
            x = np.linspace(float(left_edge[0]), float(right_edge[0]), nx)
            y = np.linspace(float(left_edge[1]), float(right_edge[1]), ny)
            z = np.linspace(float(left_edge[2]), float(right_edge[2]), nz)
            
            print(f"Loaded data: shape={chi_data.shape}, time={time:.3f}, dx={dx:.3f}")
            
            return {
                'time': time,
                'chi': chi_data,
                'x': x,
                'y': y, 
                'z': z,
                'dx': [dx, dx, dx],
                'shape': (nx, ny, nz)
            }
                
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return None
            
    def extract_equatorial_slice(self, data):
        """Extract 2D slice through the equatorial plane (z=0)"""
        chi = data['chi']
        x, y, z = data['x'], data['y'], data['z']
        
        # Find the index closest to z=0
        z_center_idx = np.argmin(np.abs(z))
        
        # Extract the equatorial slice
        chi_slice = chi[:, :, z_center_idx]
        
        # Create 2D coordinate grids
        X, Y = np.meshgrid(x, y, indexing='ij')
        
        return {
            'chi': chi_slice,
            'X': X,
            'Y': Y,
            'time': data['time']
        }
        
    def calculate_embedding_surface(self, slice_data, r_max=None, nr=100):
        """Calculate the embedding surface z(r) for the wormhole"""
        chi_slice = slice_data['chi']
        X, Y = slice_data['X'], slice_data['Y']
        
        # Convert to cylindrical coordinates
        R = np.sqrt(X**2 + Y**2)
        
        # Set maximum radius for embedding calculation
        if r_max is None:
            r_max = min(np.max(np.abs(X)), np.max(np.abs(Y))) * 0.8
            
        # Create radial array
        r_array = np.linspace(0.1, r_max, nr)  # Start from small r to avoid singularity
        
        # Interpolate chi values along radial direction - robust method
        chi_radial = np.zeros(nr)
        
        for i, r in enumerate(r_array):
            # Sample chi at many angular positions for better accuracy
            angles = np.linspace(0, 2*np.pi, 32, endpoint=False)
            chi_samples = []
            
            for angle in angles:
                x_sample = r * np.cos(angle)
                y_sample = r * np.sin(angle)
                
                # Find nearest grid points with bounds checking
                ix = np.argmin(np.abs(X[0, :] - x_sample))
                iy = np.argmin(np.abs(Y[:, 0] - y_sample))
                
                # Ensure indices are within bounds
                ix = max(0, min(ix, chi_slice.shape[1] - 1))
                iy = max(0, min(iy, chi_slice.shape[0] - 1))
                
                chi_samples.append(chi_slice[iy, ix])
                    
            # Take minimum chi (maximum curvature) rather than average
            # This better captures the wormhole throat structure
            chi_radial[i] = np.min(chi_samples) if chi_samples else 1.0
            
        # Convert chi to psi: chi = psi^(-4), so psi = chi^(-1/4)
        psi_radial = np.power(np.maximum(chi_radial, 1e-10), -0.25)
        
        # Calculate embedding height: dz/dr = sqrt(psi^4 - 1)
        # For regions where psi^4 < 1, set to 0 (no embedding possible)
        psi4 = psi_radial**4
        embedding_integrand = np.sqrt(np.maximum(psi4 - 1.0, 0.0))
        
        # Integrate to get z(r) - create both upper and lower surfaces
        z_upper = cumulative_trapezoid(embedding_integrand, r_array, initial=0)
        z_lower = -z_upper
        
        return {
            'r': r_array,
            'z_upper': z_upper, 
            'z_lower': z_lower,
            'psi': psi_radial,
            'chi': chi_radial,
            'time': slice_data['time']
        }
        
    def create_3d_embedding_plot(self, embedding_data, save_filename=None, show_plot=False):
        """Create 3D surface plot of the embedding diagram"""
        
        r = embedding_data['r']
        z_upper = embedding_data['z_upper']
        z_lower = embedding_data['z_lower']
        time = embedding_data['time']
        
        # Create angular array for full 3D surface
        theta = np.linspace(0, 2*np.pi, 60)
        R, THETA = np.meshgrid(r, theta)
        
        # Convert to Cartesian coordinates
        X = R * np.cos(THETA)
        Y = R * np.sin(THETA)
        Z_upper = np.tile(z_upper, (len(theta), 1))
        Z_lower = np.tile(z_lower, (len(theta), 1))
        
        # Create the plot with enhanced visualization
        fig = plt.figure(figsize=(15, 12))
        ax = fig.add_subplot(111, projection='3d')
        
        # Plot upper and lower surfaces with better colors
        surf_upper = ax.plot_surface(X, Y, Z_upper, alpha=0.9, cmap='viridis', 
                                   antialiased=True, linewidth=0, shade=True)
        surf_lower = ax.plot_surface(X, Y, Z_lower, alpha=0.9, cmap='viridis',
                                   antialiased=True, linewidth=0, shade=True)
        
        # Add contour lines for better depth perception
        if len(r) > 1 and len(theta) > 1:
            ax.contour(X, Y, Z_upper, levels=15, colors='white', alpha=0.8, linewidths=1)
            ax.contour(X, Y, Z_lower, levels=15, colors='white', alpha=0.8, linewidths=1)
            
        # Add connecting lines to show the tunnel throat
        for i in range(0, len(theta), 10):  # Every 10th angle
            ax.plot([X[i, :]], [Y[i, :]], [Z_upper[i, :]], 'r-', alpha=0.3, linewidth=0.5)
            ax.plot([X[i, :]], [Y[i, :]], [Z_lower[i, :]], 'r-', alpha=0.3, linewidth=0.5)
        
        # Customize the plot
        ax.set_xlabel('X (coordinate units)', fontsize=12)
        ax.set_ylabel('Y (coordinate units)', fontsize=12) 
        ax.set_zlabel('Embedding Height Z', fontsize=12)
        ax.set_title(f'Wormhole Embedding Diagram\nTime = {time:.3f} (code units)', fontsize=14, fontweight='bold')
        
        # Set aspect ratio to emphasize the tunnel depth
        max_range = np.max(r)
        max_z = np.max(np.abs(np.concatenate([z_upper, z_lower])))
        ax.set_xlim([-max_range, max_range])
        ax.set_ylim([-max_range, max_range])
        ax.set_zlim([-max_z*1.3, max_z*1.3])
        
        # Set optimal viewing angle to show the tunnel
        ax.view_init(elev=20, azim=45)  # Good angle to see the tunnel depth
        
        # Add colorbar
        fig.colorbar(surf_upper, ax=ax, shrink=0.6, label='Embedding Height')
        
        # Add physics information text
        throat_radius = r[np.argmin(np.abs(z_upper))] if len(z_upper) > 0 else 0
        max_height = np.max(z_upper) if len(z_upper) > 0 else 0
        
        info_text = f"Throat Radius: {throat_radius:.3f}\nMax Height: {max_height:.3f}"
        ax.text2D(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=10,
                 verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        if save_filename:
            plt.savefig(save_filename, dpi=300, bbox_inches='tight')
            print(f"Saved embedding diagram: {save_filename}")
            
        if show_plot:
            plt.show()
        else:
            plt.close()
            
        return fig
        
    def create_cross_section_plot(self, embedding_data, save_filename=None, show_plot=False):
        """Create 2D cross-section plot showing the funnel shape"""
        
        r = embedding_data['r']
        z_upper = embedding_data['z_upper']
        z_lower = embedding_data['z_lower']
        psi = embedding_data['psi']
        time = embedding_data['time']
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot 1: Cross-section of the embedding surface
        ax1.plot(r, z_upper, 'b-', linewidth=2, label='Upper surface')
        ax1.plot(r, z_lower, 'r-', linewidth=2, label='Lower surface')
        ax1.fill_between(r, z_upper, z_lower, alpha=0.3, color='gray', label='Wormhole throat')
        
        ax1.set_xlabel('Radial Coordinate r', fontsize=12)
        ax1.set_ylabel('Embedding Height z', fontsize=12)
        ax1.set_title(f'Wormhole Cross-Section\nTime = {time:.3f}', fontsize=14)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Add throat indicator
        throat_idx = np.argmin(np.abs(z_upper)) if len(z_upper) > 0 else 0
        throat_r = r[throat_idx]
        ax1.axvline(throat_r, color='green', linestyle='--', alpha=0.7, label=f'Throat at r={throat_r:.3f}')
        
        # Plot 2: Conformal factor psi(r)
        ax2.plot(r, psi, 'g-', linewidth=2, label='ψ(r)')
        ax2.axhline(y=1, color='red', linestyle='--', alpha=0.7, label='ψ = 1 (flat space)')
        
        ax2.set_xlabel('Radial Coordinate r', fontsize=12)
        ax2.set_ylabel('Conformal Factor ψ', fontsize=12)
        ax2.set_title('Conformal Factor Profile', fontsize=14)
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        plt.tight_layout()
        
        if save_filename:
            plt.savefig(save_filename, dpi=300, bbox_inches='tight')
            print(f"Saved cross-section plot: {save_filename}")
            
        if show_plot:
            plt.show()
        else:
            plt.close()
            
        return fig
        
    def analyze_throat_evolution(self, embedding_list):
        """Analyze how the wormhole throat evolves over time"""
        times = []
        throat_radii = []
        max_heights = []
        
        for embedding_data in embedding_list:
            times.append(embedding_data['time'])
            
            r = embedding_data['r']
            z_upper = embedding_data['z_upper']
            
            # Find throat radius (where z is minimum)
            if len(z_upper) > 0:
                throat_idx = np.argmin(np.abs(z_upper))
                throat_radii.append(r[throat_idx])
                max_heights.append(np.max(z_upper))
            else:
                throat_radii.append(0)
                max_heights.append(0)
                
        return {
            'times': np.array(times),
            'throat_radii': np.array(throat_radii),
            'max_heights': np.array(max_heights)
        }
        
    def plot_throat_evolution(self, evolution_data, save_filename=None, show_plot=False):
        """Plot the evolution of throat properties over time"""
        
        times = evolution_data['times']
        throat_radii = evolution_data['throat_radii']
        max_heights = evolution_data['max_heights']
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Plot throat radius evolution
        ax1.plot(times, throat_radii, 'b-o', linewidth=2, markersize=4)
        ax1.set_xlabel('Time (code units)')
        ax1.set_ylabel('Throat Radius')
        ax1.set_title('Wormhole Throat Radius Evolution')
        ax1.grid(True, alpha=0.3)
        
        # Plot maximum height evolution
        ax2.plot(times, max_heights, 'r-o', linewidth=2, markersize=4)
        ax2.set_xlabel('Time (code units)')
        ax2.set_ylabel('Maximum Embedding Height')
        ax2.set_title('Wormhole Height Evolution')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_filename:
            plt.savefig(save_filename, dpi=300, bbox_inches='tight')
            print(f"Saved throat evolution plot: {save_filename}")
            
        if show_plot:
            plt.show()
        else:
            plt.close()
            
        return fig
        
    def create_animation(self, max_frames=50, duration=0.2):
        """Create animated GIF of the wormhole collapse"""
        
        # Get list of data files
        files = sorted(glob.glob(self.data_pattern))
        if not files:
            print("No data files found for animation!")
            return
            
        # Limit number of frames
        if len(files) > max_frames:
            step = len(files) // max_frames
            files = files[::step]
            
        print(f"Creating animation with {len(files)} frames...")
        
        embedding_list = []
        frame_files = []
        
        for i, filename in enumerate(files):
            print(f"Processing frame {i+1}/{len(files)}: {os.path.basename(filename)}")
            
            # Load data
            data = self.load_wormhole_data(filename)
            if data is None:
                continue
                
            # Extract equatorial slice
            slice_data = self.extract_equatorial_slice(data)
            
            # Calculate embedding surface
            embedding_data = self.calculate_embedding_surface(slice_data)
            embedding_list.append(embedding_data)
            
            # Create frame plot
            frame_filename = os.path.join(self.output_dir, "individual_frames", f"frame_{i:04d}.png")
            self.create_3d_embedding_plot(embedding_data, save_filename=frame_filename)
            frame_files.append(frame_filename)
            
        # Create GIF animation
        if frame_files:
            gif_filename = os.path.join(self.output_dir, "animations", "wormhole_collapse_embedding.gif")
            
            # Load images and create GIF
            images = []
            for frame_file in frame_files:
                if os.path.exists(frame_file):
                    images.append(imageio.imread(frame_file))
                    
            if images:
                imageio.mimsave(gif_filename, images, duration=duration)
                print(f"Created animation: {gif_filename}")
                
        # Analyze throat evolution
        if embedding_list:
            evolution_data = self.analyze_throat_evolution(embedding_list)
            evolution_filename = os.path.join(self.output_dir, "wormhole_throat_evolution.png") 
            self.plot_throat_evolution(evolution_data, save_filename=evolution_filename)
            
            # Save evolution data
            data_filename = os.path.join(self.output_dir, "data", "throat_evolution.npz")
            np.savez(data_filename, **evolution_data)
            print(f"Saved evolution data: {data_filename}")
            
        print("✅ Animation creation completed!")
        
    def analyze_single_timestep(self, filename=None, show_plots=False):
        """Analyze a single timestep for detailed embedding diagram"""
        
        if filename is None:
            # Use the first available file
            files = sorted(glob.glob(self.data_pattern))
            if not files:
                print("No data files found!")
                return
            filename = files[0]
            print(f"Using first available file: {os.path.basename(filename)}")
            
        # Load and process data
        data = self.load_wormhole_data(filename)
        if data is None:
            return
            
        slice_data = self.extract_equatorial_slice(data)
        embedding_data = self.calculate_embedding_surface(slice_data)
        
        # Create plots
        time_str = f"t{embedding_data['time']:.3f}".replace('.', 'p')
        
        # 3D embedding diagram
        embedding_3d_file = os.path.join(self.output_dir, f"wormhole_embedding_3d_{time_str}.png")
        self.create_3d_embedding_plot(embedding_data, save_filename=embedding_3d_file, show_plot=show_plots)
        
        # Cross-section plot
        crosssection_file = os.path.join(self.output_dir, f"wormhole_crosssection_{time_str}.png")
        self.create_cross_section_plot(embedding_data, save_filename=crosssection_file, show_plot=show_plots)
        
        # Save data
        data_file = os.path.join(self.output_dir, "data", f"embedding_data_{time_str}.npz")
        np.savez(data_file, **embedding_data)
        print(f"Saved embedding data: {data_file}")
        
        print(f"✅ Single timestep analysis completed for t = {embedding_data['time']:.3f}")
        
def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create wormhole embedding diagrams")
    parser.add_argument("--mode", choices=["single", "animation", "both"], default="both",
                       help="Analysis mode: single timestep, animation, or both")
    parser.add_argument("--data-pattern", type=str, default=None,
                       help="Pattern for data files")
    parser.add_argument("--max-frames", type=int, default=50,
                       help="Maximum number of frames for animation")
    parser.add_argument("--duration", type=float, default=0.2,
                       help="Duration per frame in animation (seconds)")
    parser.add_argument("--show-plots", action="store_true",
                       help="Display plots interactively")
    
    args = parser.parse_args()
    
    # Create visualizer
    visualizer = WormholeEmbeddingVisualizer(data_pattern=args.data_pattern)
    
    # Run analysis
    if args.mode in ["single", "both"]:
        visualizer.analyze_single_timestep(show_plots=args.show_plots)
        
    if args.mode in ["animation", "both"]:
        visualizer.create_animation(max_frames=args.max_frames, duration=args.duration)
        
    print("\n🎉 Wormhole embedding diagram analysis completed!")
    print(f"Check the '{visualizer.output_dir}' directory for results")
    
if __name__ == "__main__":
    main() 