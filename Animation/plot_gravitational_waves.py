#!/usr/bin/env python3
"""
Gravitational Wave Analysis for Binary Black Hole Simulations
Analyzes and visualizes Weyl4 data to extract gravitational wave signals
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from scipy.integrate import cumulative_trapezoid
from scipy.signal import savgol_filter
import os

class GravitationalWaveAnalyzer:
    """Class for analyzing gravitational wave data from Weyl4 modes"""
    
    def __init__(self, data_dir="data"):
        """Initialize with data directory"""
        self.data_dir = data_dir
        self.modes = {}
        self.strain = {}
        
    def load_weyl4_data(self):
        """Load all available Weyl4 mode data"""
        mode_files = {
            (2, 0): f"{self.data_dir}/Weyl4_mode_20.dat",
            (2, 1): f"{self.data_dir}/Weyl4_mode_21.dat", 
            (2, 2): f"{self.data_dir}/Weyl4_mode_22.dat"
        }
        
        print("Loading Weyl4 data...")
        for (l, m), filename in mode_files.items():
            if os.path.exists(filename):
                print(f"  Loading (l,m) = ({l},{m}) mode from {filename}")
                data = np.loadtxt(filename, comments='#')
                
                self.modes[(l, m)] = {
                    'time': data[:, 0],
                    'real': data[:, 1], 
                    'imag': data[:, 2],
                    'complex': data[:, 1] + 1j * data[:, 2]
                }
                print(f"    Loaded {len(data)} time points")
            else:
                print(f"  Warning: {filename} not found")
        
        print(f"Successfully loaded {len(self.modes)} Weyl4 modes\n")
    
    def calculate_strain(self):
        """Calculate gravitational wave strain h from Weyl4 by double integration"""
        print("Calculating gravitational wave strain...")
        
        for (l, m), data in self.modes.items():
            print(f"  Processing (l,m) = ({l},{m}) mode")
            
            time = data['time']
            weyl4 = data['complex']
            
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
        
        print("Strain calculation completed\n")
    
    def calculate_frequency(self, mode=(2, 2), smooth=True):
        """Calculate instantaneous frequency from phase evolution"""
        if mode not in self.strain:
            print(f"Mode {mode} not available for frequency calculation")
            return None, None
            
        time = self.strain[mode]['time']
        phase = self.strain[mode]['phase']
        
        # Unwrap phase to avoid 2π jumps
        phase_unwrapped = np.unwrap(phase)
        
        # Smooth phase if requested
        if smooth and len(phase_unwrapped) > 10:
            window_length = min(21, len(phase_unwrapped) // 4)
            if window_length % 2 == 0:
                window_length -= 1
            phase_unwrapped = savgol_filter(phase_unwrapped, window_length, 3)
        
        # Calculate frequency: f = (1/2π) * dφ/dt
        dt = np.diff(time)
        dphase_dt = np.diff(phase_unwrapped)
        frequency = dphase_dt / (2 * np.pi * dt)
        time_freq = time[:-1] + dt/2  # Midpoint times
        
        return time_freq, frequency
    
    def plot_weyl4_overview(self, save_dir="gw_plots"):
        """Plot overview of all Weyl4 modes"""
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
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
    
    def plot_strain_analysis(self, save_dir="gw_plots"):
        """Plot gravitational wave strain analysis"""
        if not self.strain:
            print("No strain data available. Run calculate_strain() first.")
            return
            
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
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
        
        # Plot 2: Strain real/imaginary for dominant (2,2) mode
        ax = axes[0, 1]
        if (2, 2) in self.strain:
            data = self.strain[(2, 2)]
            ax.plot(data['time'], data['real'], 'b-', label='h₊ (real)', linewidth=1.5)
            ax.plot(data['time'], data['imag'], 'r-', label='h₋ (imag)', linewidth=1.5)
            ax.set_xlabel('Time (code units)')
            ax.set_ylabel('Strain h₂₂')
            ax.set_title('Gravitational Wave Strain - (2,2) Mode')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        # Plot 3: Frequency evolution
        ax = axes[1, 0]
        for (l, m) in self.strain.keys():
            time_freq, frequency = self.calculate_frequency((l, m))
            if time_freq is not None:
                # Only plot positive frequencies and reasonable range
                mask = (frequency > 0) & (frequency < 1.0)  # Adjust range as needed
                ax.plot(time_freq[mask], frequency[mask], 
                       label=f'f_{{{l}{m}}}', linewidth=1.5)
        ax.set_xlabel('Time (code units)')
        ax.set_ylabel('Frequency (code units)')
        ax.set_title('Gravitational Wave Frequency Evolution')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Plot 4: Strain spectrogram for (2,2) mode
        ax = axes[1, 1]
        if (2, 2) in self.strain:
            data = self.strain[(2, 2)]
            # Create a simple time-frequency plot
            from scipy.signal import stft
            
            strain_real = data['real']
            f, t, Zxx = stft(strain_real, fs=1.0/(data['time'][1]-data['time'][0]), nperseg=16)
            
            # Convert to proper time coordinates
            t_plot = data['time'][0] + t * (data['time'][-1] - data['time'][0]) / t[-1]
            
            mesh = ax.pcolormesh(t_plot, f, np.abs(Zxx), shading='gouraud', 
                               norm=colors.LogNorm(vmin=np.max(np.abs(Zxx))*1e-4, vmax=np.max(np.abs(Zxx))))
            ax.set_xlabel('Time (code units)')
            ax.set_ylabel('Frequency (code units)')
            ax.set_title('Strain Spectrogram - (2,2) Mode')
            plt.colorbar(mesh, ax=ax, label='|h(f,t)|')
        
        plt.tight_layout()
        plt.savefig(f'{save_dir}/strain_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        print(f"Strain analysis plot saved to {save_dir}/strain_analysis.png")
    
    def plot_inspiral_merger_ringdown(self, save_dir="gw_plots"):
        """Plot showing the three phases of binary black hole merger"""
        if (2, 2) not in self.strain:
            print("(2,2) mode not available for IMR analysis")
            return
            
        data = self.strain[(2, 2)]
        time = data['time']
        amplitude = data['amplitude']
        
        # Calculate frequency
        time_freq, frequency = self.calculate_frequency((2, 2))
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Amplitude evolution
        ax1.semilogy(time, amplitude, 'b-', linewidth=2, label='|h₂₂|')
        ax1.set_ylabel('Strain Amplitude |h₂₂|')
        ax1.set_title('Binary Black Hole Merger: Inspiral-Merger-Ringdown')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Frequency evolution
        if time_freq is not None:
            mask = (frequency > 0) & (frequency < 1.0)
            ax2.plot(time_freq[mask], frequency[mask], 'r-', linewidth=2, label='f₂₂')
            ax2.set_xlabel('Time (code units)')
            ax2.set_ylabel('Frequency (code units)')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            
            # Add phase annotations
            if len(frequency[mask]) > 20:
                # Simple heuristic to identify phases
                max_amp_idx = np.argmax(amplitude)
                max_amp_time = time[max_amp_idx]
                
                # Inspiral: before peak
                ax1.axvspan(time[0], max_amp_time, alpha=0.2, color='blue', label='Inspiral')
                ax2.axvspan(time[0], max_amp_time, alpha=0.2, color='blue')
                
                # Merger: around peak  
                merger_width = (time[-1] - time[0]) * 0.1  # 10% of total time
                ax1.axvspan(max_amp_time - merger_width/2, max_amp_time + merger_width/2, 
                           alpha=0.2, color='red', label='Merger')
                ax2.axvspan(max_amp_time - merger_width/2, max_amp_time + merger_width/2, 
                           alpha=0.2, color='red')
                
                # Ringdown: after peak
                ax1.axvspan(max_amp_time + merger_width/2, time[-1], 
                           alpha=0.2, color='green', label='Ringdown')
                ax2.axvspan(max_amp_time + merger_width/2, time[-1], 
                           alpha=0.2, color='green')
                
                ax1.legend()
        
        plt.tight_layout()
        plt.savefig(f'{save_dir}/inspiral_merger_ringdown.png', dpi=300, bbox_inches='tight')
        plt.show()
        print(f"IMR analysis plot saved to {save_dir}/inspiral_merger_ringdown.png")
    
    def save_processed_data(self, output_dir="gw_data"):
        """Save processed gravitational wave data to files"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Save strain data
        for (l, m), data in self.strain.items():
            filename = f"{output_dir}/strain_mode_{l}{m}.dat"
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
                filename = f"{output_dir}/frequency_mode_{l}{m}.dat"
                header = f"# Gravitational wave frequency for (l,m) = ({l},{m})\n"
                header += f"# Columns: time, frequency\n"
                
                output_data = np.column_stack([time_freq, frequency])
                np.savetxt(filename, output_data, header=header, 
                          fmt='%15.8e', delimiter='  ')
                print(f"Saved frequency data to {filename}")

def main():
    """Main analysis function"""
    print("🌊 Binary Black Hole Gravitational Wave Analysis")
    print("=" * 50)
    
    # Initialize analyzer
    gw = GravitationalWaveAnalyzer()
    
    # Load Weyl4 data
    gw.load_weyl4_data()
    
    if not gw.modes:
        print("No Weyl4 data found. Please check data directory.")
        return
    
    # Calculate strain
    gw.calculate_strain()
    
    # Create plots
    print("Creating visualizations...")
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