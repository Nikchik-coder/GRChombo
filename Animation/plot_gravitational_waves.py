#!/usr/bin/env python3
"""
Gravitational Wave Analysis for GRChombo Simulations
Analyzes and visualizes Weyl4 data to extract gravitational wave signals
Enhanced with auto-detection and flexible data handling
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from scipy.integrate import cumulative_trapezoid
from scipy.signal import savgol_filter
import os
import glob

class GravitationalWaveAnalyzer:
    """Class for analyzing gravitational wave data from Weyl4 modes"""
    
    def __init__(self, data_dir=None):
        """Initialize with data directory (auto-detected if None)"""
        self.data_dir = self.find_data_directory(data_dir)
        self.modes = {}
        self.strain = {}
        print(f"Initialized GW analyzer with data directory: {self.data_dir}")
        
    def find_data_directory(self, data_dir=None):
        """Auto-detect data directory with Weyl4 files"""
        if data_dir and os.path.exists(data_dir):
            return data_dir
        
        # Search for common data directory patterns
        search_dirs = [
            "data",
            "gw_data", 
            "../data",
            "../../data",
            "/home/nik/GRChombo_runs/Wormhole_Collapse/data"

        ]
        
        for search_dir in search_dirs:
            if os.path.exists(search_dir):
                # Check if it contains Weyl4 files
                weyl4_files = glob.glob(f"{search_dir}/Weyl4_*.dat")
                if weyl4_files:
                    print(f"Found Weyl4 data in: {search_dir}")
                    return search_dir
        
        # If not found, create a default directory
        default_dir = "gw_data"
        if not os.path.exists(default_dir):
            os.makedirs(default_dir)
            print(f"Created default data directory: {default_dir}")
        
        return default_dir
    
    def discover_available_modes(self):
        """Discover all available Weyl4 mode files"""
        if not os.path.exists(self.data_dir):
            print(f"Data directory {self.data_dir} does not exist")
            return {}
            
        # Search for Weyl4 files with different naming patterns
        patterns = [
            "Weyl4_mode_*.dat",
            "Weyl4_l*_m*.dat", 
            "psi4_mode_*.dat",
            "psi4_l*_m*.dat"
        ]
        
        available_modes = {}
        
        for pattern in patterns:
            files = glob.glob(f"{self.data_dir}/{pattern}")
            for file in files:
                basename = os.path.basename(file)
                
                # Try to extract (l,m) from different naming conventions
                if "mode_" in basename:
                    # Format: Weyl4_mode_22.dat or psi4_mode_22.dat
                    mode_str = basename.split("mode_")[1].split(".")[0]
                    if len(mode_str) == 2:
                        l, m = int(mode_str[0]), int(mode_str[1])
                        available_modes[(l, m)] = file
                elif "_l" in basename and "_m" in basename:
                    # Format: Weyl4_l2_m2.dat
                    parts = basename.split("_")
                    l = int([p for p in parts if p.startswith("l")][0][1:])
                    m = int([p for p in parts if p.startswith("m")][0][1:])
                    available_modes[(l, m)] = file
        
        return available_modes
    
    def load_weyl4_data(self):
        """Load all available Weyl4 mode data with auto-detection"""
        print("Discovering available Weyl4 data...")
        
        # Auto-discover available modes
        available_modes = self.discover_available_modes()
        
        if not available_modes:
            print("No Weyl4 data files found.")
            print(f"Searched in: {self.data_dir}")
            print("Expected file patterns:")
            print("  - Weyl4_mode_22.dat")
            print("  - Weyl4_l2_m2.dat")
            print("  - psi4_mode_22.dat")
            return
        
        print(f"Found {len(available_modes)} Weyl4 mode files:")
        for (l, m), filename in available_modes.items():
            print(f"  (l,m) = ({l},{m}): {os.path.basename(filename)}")
        
        # Load the data
        print("\nLoading Weyl4 data...")
        for (l, m), filename in available_modes.items():
            try:
                print(f"  Loading (l,m) = ({l},{m}) from {os.path.basename(filename)}")
                data = np.loadtxt(filename, comments='#')
                
                # Handle different file formats
                if data.shape[1] >= 3:
                    # Standard format: time, real, imag
                    time_col, real_col, imag_col = 0, 1, 2
                elif data.shape[1] == 2:
                    # Amplitude only format: time, amplitude
                    time_col, real_col, imag_col = 0, 1, None
                else:
                    print(f"    Warning: Unexpected file format for {filename}")
                    continue
                
                mode_data = {
                    'time': data[:, time_col],
                    'real': data[:, real_col] if real_col is not None else np.zeros(len(data)),
                    'imag': data[:, imag_col] if imag_col is not None else np.zeros(len(data))
                }
                mode_data['complex'] = mode_data['real'] + 1j * mode_data['imag']
                
                self.modes[(l, m)] = mode_data
                print(f"    Loaded {len(data)} time points")
                
            except Exception as e:
                print(f"    Error loading {filename}: {e}")
                continue
        
        if self.modes:
            print(f"\nSuccessfully loaded {len(self.modes)} Weyl4 modes")
        else:
            print("\nNo Weyl4 modes could be loaded")
    
    def calculate_strain(self):
        """Calculate gravitational wave strain h from Weyl4 by double integration"""
        if not self.modes:
            print("No Weyl4 data available. Run load_weyl4_data() first.")
            return
            
        print("Calculating gravitational wave strain...")
        
        for (l, m), data in self.modes.items():
            try:
                print(f"  Processing (l,m) = ({l},{m}) mode")
                
                time = data['time']
                weyl4 = data['complex']
                
                # Check for valid data
                if len(time) < 2:
                    print(f"    Warning: Not enough data points for mode ({l},{m})")
                    continue
                
                # First integration: ∫ Weyl4 dt
                psi4_int1 = cumulative_trapezoid(weyl4, time, initial=0)
                
                # Second integration: ∫∫ Weyl4 dt dt = strain h
                strain_complex = cumulative_trapezoid(psi4_int1, time, initial=0)
                
                self.strain[(l, m)] = {
                    'time': time,
                    'complex': strain_complex,
                    'real': np.real(strain_complex),
                    'imag': np.imag(strain_complex), 
                    'amplitude': np.abs(strain_complex),
                    'phase': np.angle(strain_complex)
                }
                
                print(f"    Max strain amplitude: {np.max(np.abs(strain_complex)):.2e}")
                
            except Exception as e:
                print(f"    Error processing mode ({l},{m}): {e}")
                continue
        
        if self.strain:
            print("Strain calculation completed")
        else:
            print("No strain data could be calculated")
    
    def calculate_frequency(self, mode=(2, 2), smooth=True):
        """Calculate instantaneous frequency from phase evolution"""
        if mode not in self.strain:
            print(f"Mode {mode} not available for frequency calculation")
            return None, None
            
        try:
            time = self.strain[mode]['time']
            phase = self.strain[mode]['phase']
            
            # Check for sufficient data
            if len(time) < 5:
                print(f"Not enough data points for frequency calculation of mode {mode}")
                return None, None
            
            # Unwrap phase to avoid 2π jumps
            phase_unwrapped = np.unwrap(phase)
            
            # Smooth phase if requested
            if smooth and len(phase_unwrapped) > 10:
                window_length = min(21, len(phase_unwrapped) // 4)
                if window_length % 2 == 0:
                    window_length -= 1
                if window_length >= 3:
                    phase_unwrapped = savgol_filter(phase_unwrapped, window_length, 3)
            
            # Calculate frequency: f = (1/2π) * dφ/dt
            dt = np.diff(time)
            dphase_dt = np.diff(phase_unwrapped)
            
            # Avoid division by zero
            mask = dt > 0
            if not np.any(mask):
                print(f"Invalid time data for mode {mode}")
                return None, None
            
            frequency = dphase_dt[mask] / (2 * np.pi * dt[mask])
            time_freq = time[:-1][mask] + dt[mask]/2  # Midpoint times
            
            return time_freq, frequency
            
        except Exception as e:
            print(f"Error calculating frequency for mode {mode}: {e}")
            return None, None
    
    def plot_weyl4_overview(self, save_dir="gw_plots"):
        """Plot overview of all Weyl4 modes"""
        if not self.modes:
            print("No Weyl4 data available for plotting")
            return
            
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            
            # Plot 1: Real parts
            ax = axes[0, 0]
            for (l, m), data in self.modes.items():
                ax.plot(data['time'], data['real'], label=f'({l},{m})', linewidth=1.5)
            ax.set_xlabel('Time (code units)')
            ax.set_ylabel('Re[Ψ₄]')
            ax.set_title('Weyl4 Scalar - Real Part')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Plot 2: Imaginary parts  
            ax = axes[0, 1]
            for (l, m), data in self.modes.items():
                ax.plot(data['time'], data['imag'], label=f'({l},{m})', linewidth=1.5)
            ax.set_xlabel('Time (code units)')
            ax.set_ylabel('Im[Ψ₄]')
            ax.set_title('Weyl4 Scalar - Imaginary Part')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Plot 3: Amplitude
            ax = axes[1, 0]
            for (l, m), data in self.modes.items():
                amplitude = np.abs(data['complex'])
                ax.semilogy(data['time'], amplitude, label=f'({l},{m})', linewidth=1.5)
            ax.set_xlabel('Time (code units)')
            ax.set_ylabel('|Ψ₄|')
            ax.set_title('Weyl4 Scalar - Amplitude (Log Scale)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Plot 4: Phase
            ax = axes[1, 1]
            for (l, m), data in self.modes.items():
                phase = np.angle(data['complex'])
                ax.plot(data['time'], phase, label=f'({l},{m})', linewidth=1.5)
            ax.set_xlabel('Time (code units)')
            ax.set_ylabel('Phase [rad]')
            ax.set_title('Weyl4 Scalar - Phase')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(f'{save_dir}/weyl4_overview.png', dpi=300, bbox_inches='tight')
            plt.show()
            print(f"Weyl4 overview plot saved to {save_dir}/weyl4_overview.png")
            
        except Exception as e:
            print(f"Error creating Weyl4 overview plot: {e}")
    
    def plot_strain_analysis(self, save_dir="gw_plots"):
        """Plot gravitational wave strain analysis"""
        if not self.strain:
            print("No strain data available. Run calculate_strain() first.")
            return
            
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            
            # Plot 1: Strain amplitude
            ax = axes[0, 0]
            for (l, m), data in self.strain.items():
                ax.semilogy(data['time'], data['amplitude'], label=f'h_{{{l}{m}}}', linewidth=2)
            ax.set_xlabel('Time (code units)')
            ax.set_ylabel('Strain Amplitude |h|')
            ax.set_title('Gravitational Wave Strain - Amplitude')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Plot 2: Strain real/imaginary for dominant mode
            ax = axes[0, 1]
            dominant_mode = self.get_dominant_mode()
            if dominant_mode:
                data = self.strain[dominant_mode]
                ax.plot(data['time'], data['real'], 'b-', label='h₊ (real)', linewidth=1.5)
                ax.plot(data['time'], data['imag'], 'r-', label='h₋ (imag)', linewidth=1.5)
                ax.set_xlabel('Time (code units)')
                ax.set_ylabel(f'Strain h_{{{dominant_mode[0]}{dominant_mode[1]}}}')
                ax.set_title(f'Gravitational Wave Strain - ({dominant_mode[0]},{dominant_mode[1]}) Mode')
                ax.legend()
                ax.grid(True, alpha=0.3)
            
            # Plot 3: Frequency evolution
            ax = axes[1, 0]
            for (l, m) in self.strain.keys():
                time_freq, frequency = self.calculate_frequency((l, m))
                if time_freq is not None:
                    # Only plot positive frequencies and reasonable range
                    mask = (frequency > 0) & (frequency < 1.0)  # Adjust range as needed
                    if np.any(mask):
                        ax.plot(time_freq[mask], frequency[mask], 
                               label=f'f_{{{l}{m}}}', linewidth=1.5)
            ax.set_xlabel('Time (code units)')
            ax.set_ylabel('Frequency (code units)')
            ax.set_title('Gravitational Wave Frequency Evolution')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Plot 4: Strain spectrogram for dominant mode
            ax = axes[1, 1]
            dominant_mode = self.get_dominant_mode()
            if dominant_mode:
                data = self.strain[dominant_mode]
                try:
                    from scipy.signal import stft
                    
                    strain_real = data['real']
                    dt = data['time'][1] - data['time'][0]
                    f, t, Zxx = stft(strain_real, fs=1.0/dt, nperseg=min(16, len(strain_real)//4))
                    
                    # Convert to proper time coordinates
                    t_plot = data['time'][0] + t * (data['time'][-1] - data['time'][0]) / (t[-1] if t[-1] > 0 else 1)
                    
                    mesh = ax.pcolormesh(t_plot, f, np.abs(Zxx), shading='gouraud', 
                                       norm=colors.LogNorm(vmin=np.max(np.abs(Zxx))*1e-4, 
                                                          vmax=np.max(np.abs(Zxx))))
                    ax.set_xlabel('Time (code units)')
                    ax.set_ylabel('Frequency (code units)')
                    ax.set_title(f'Strain Spectrogram - ({dominant_mode[0]},{dominant_mode[1]}) Mode')
                    plt.colorbar(mesh, ax=ax, label='|h(f,t)|')
                except Exception as e:
                    ax.text(0.5, 0.5, f'Spectrogram not available\n{str(e)}', 
                           transform=ax.transAxes, ha='center', va='center')
            
            plt.tight_layout()
            plt.savefig(f'{save_dir}/strain_analysis.png', dpi=300, bbox_inches='tight')
            plt.show()
            print(f"Strain analysis plot saved to {save_dir}/strain_analysis.png")
            
        except Exception as e:
            print(f"Error creating strain analysis plot: {e}")
    
    def get_dominant_mode(self):
        """Get the dominant strain mode (highest amplitude)"""
        if not self.strain:
            return None
        
        # Prioritize (2,2) mode if available
        if (2, 2) in self.strain:
            return (2, 2)
        
        # Otherwise, find mode with highest peak amplitude
        max_amplitude = 0
        dominant_mode = None
        
        for (l, m), data in self.strain.items():
            peak_amp = np.max(data['amplitude'])
            if peak_amp > max_amplitude:
                max_amplitude = peak_amp
                dominant_mode = (l, m)
        
        return dominant_mode
    
    def plot_inspiral_merger_ringdown(self, save_dir="gw_plots"):
        """Plot showing the three phases of binary black hole merger"""
        dominant_mode = self.get_dominant_mode()
        
        if not dominant_mode:
            print("No strain data available for IMR analysis")
            return
        
        try:
            data = self.strain[dominant_mode]
            time = data['time']
            amplitude = data['amplitude']
            
            # Calculate frequency
            time_freq, frequency = self.calculate_frequency(dominant_mode)
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # Amplitude evolution
            ax1.semilogy(time, amplitude, 'b-', linewidth=2, label=f'|h_{{{dominant_mode[0]}{dominant_mode[1]}}}|')
            ax1.set_ylabel('Strain Amplitude |h|')
            ax1.set_title('GRChombo Simulation: Gravitational Wave Evolution')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            # Frequency evolution
            if time_freq is not None:
                mask = (frequency > 0) & (frequency < 1.0)
                if np.any(mask):
                    ax2.plot(time_freq[mask], frequency[mask], 'r-', linewidth=2, 
                            label=f'f_{{{dominant_mode[0]}{dominant_mode[1]}}}')
                    ax2.set_xlabel('Time (code units)')
                    ax2.set_ylabel('Frequency (code units)')
                    ax2.grid(True, alpha=0.3)
                    ax2.legend()
                    
                    # Add phase annotations if enough data
                    if len(amplitude) > 20:
                        max_amp_idx = np.argmax(amplitude)
                        max_amp_time = time[max_amp_idx]
                        
                        # Simple phase identification
                        total_time = time[-1] - time[0]
                        
                        # Early phase
                        early_end = time[0] + 0.6 * total_time
                        ax1.axvspan(time[0], early_end, alpha=0.2, color='blue', label='Early Evolution')
                        ax2.axvspan(time[0], early_end, alpha=0.2, color='blue')
                        
                        # Late phase
                        ax1.axvspan(early_end, time[-1], alpha=0.2, color='green', label='Late Evolution')
                        ax2.axvspan(early_end, time[-1], alpha=0.2, color='green')
                        
                        ax1.legend()
            
            plt.tight_layout()
            plt.savefig(f'{save_dir}/inspiral_merger_ringdown.png', dpi=300, bbox_inches='tight')
            plt.show()
            print(f"Evolution analysis plot saved to {save_dir}/inspiral_merger_ringdown.png")
            
        except Exception as e:
            print(f"Error creating IMR analysis plot: {e}")
    
    def save_processed_data(self, output_dir="gw_data"):
        """Save processed gravitational wave data to files"""
        if not self.strain:
            print("No strain data to save")
            return
            
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        try:
            # Save strain data
            for (l, m), data in self.strain.items():
                filename = f"/home/nik/GRChombo_runs/Wormhole_Collapse_Cheap/data/Weyl4_mode_{l}{m}.dat"
                header = f"# Gravitational wave strain for (l,m) = ({l},{m})\n"
                header += f"# Columns: time, Re[h], Im[h], |h|, phase\n"
                
                output_data = np.column_stack([
                    data['time'], data['real'], data['imag'], 
                    data['amplitude'], data['phase']
                ])
                
                np.savetxt(filename, output_data, header=header, 
                          fmt='%15.8e', delimiter='  ')
                print(f"Saved strain data to {filename}")
            
            # Save frequency data
            for (l, m) in self.strain.keys():
                time_freq, frequency = self.calculate_frequency((l, m))
                if time_freq is not None:
                    filename = f"/home/nik/GRChombo_runs/Wormhole_Collapse_Cheap/data/frequency_mode_{l}{m}.dat"
                    header = f"# Gravitational wave frequency for (l,m) = ({l},{m})\n"
                    header += f"# Columns: time, frequency\n"
                    
                    output_data = np.column_stack([time_freq, frequency])
                    np.savetxt(filename, output_data, header=header, 
                              fmt='%15.8e', delimiter='  ')
                    print(f"Saved frequency data to {filename}")
                    
        except Exception as e:
            print(f"Error saving processed data: {e}")

def main():
    """Main analysis function"""
    print("🌊 GRChombo Gravitational Wave Analysis")
    print("=" * 50)
    
    # Set the data directory explicitly
    data_dir = "/home/nik/GRChombo_runs/Wormhole_Collapse_Cheap/data"
    
    # Initialize analyzer with explicit data directory
    gw = GravitationalWaveAnalyzer(data_dir=data_dir)
    
    # Load Weyl4 data
    gw.load_weyl4_data()
    
    if not gw.modes:
        print("\n❌ No Weyl4 data found.")
        print("Please check that your simulation has:")
        print("  - Weyl4 extraction enabled")
        print("  - Output files in expected locations")
        print("  - Proper file naming (Weyl4_mode_*.dat)")
        return
    
    # Calculate strain
    gw.calculate_strain()
    
    if not gw.strain:
        print("\n❌ No strain data could be calculated.")
        return
    
    # Create plots
    print("\nCreating visualizations...")
    gw.plot_weyl4_overview()
    gw.plot_strain_analysis() 
    gw.plot_inspiral_merger_ringdown()
    
    # Save processed data
    print("\nSaving processed data...")
    gw.save_processed_data()
    
    print("\n🎉 Gravitational wave analysis completed!")
    print("Check the 'gw_plots/' directory for visualizations")
    print("Check the 'gw_data/' directory for processed data files")

if __name__ == "__main__":
    main() 