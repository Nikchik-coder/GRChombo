
# Enhanced GW plotting script with multi-radius extraction
# Shows how gravitational waves appear at different distances from the source

import numpy as np
import matplotlib.pyplot as plt
import os

def calculate_retarded_time(time, radius, mass=1.0):
    """
    Calculate retarded time accounting for light travel time
    
    Parameters:
    -----------
    time : array_like
        Coordinate time
    radius : float
        Extraction radius
    mass : float
        Total ADM mass (default: 1.0)
        
    Returns:
    --------
    array_like : Retarded time t_ret = (t - r*)/M
    """
    # Tortoise coordinate: r* = r + M*ln(r/(2M) - 1)
    # This accounts for curved spacetime geometry
    r_tortoise = radius + mass * np.log(radius/(2.0*mass) - 1.0)
    
    # Retarded time: subtract light travel time
    t_retarded = (time - r_tortoise) / mass
    
    return t_retarded

def load_weyl4_data(mode="22"):
    """Load raw Weyl4 data from the data directory"""
    filename = f"data/Weyl4_mode_{mode}.dat"
    
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Weyl4 data file {filename} not found!")
    
    # Load data: time, Re[Psi4], Im[Psi4]
    data = np.loadtxt(filename)
    
    return {
        'time': data[:, 0],
        'real': data[:, 1], 
        'imag': data[:, 2],
        'complex': data[:, 1] + 1j * data[:, 2]
    }

# Physical parameters
extraction_radii = [50, 100, 150]  # Multiple extraction radii
M = 1.0  # Total ADM mass
mode = "22"  # Dominant gravitational wave mode

print(f"Loading Weyl4 data for mode ({mode[0]},{mode[1]})...")

try:
    # Load the raw Weyl4 data
    weyl4_data = load_weyl4_data(mode)
    print(f"Loaded {len(weyl4_data['time'])} time points")
    print(f"Time range: {weyl4_data['time'][0]:.3f} to {weyl4_data['time'][-1]:.3f}")
    
except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Available files in data/:")
    if os.path.exists("data"):
        files = [f for f in os.listdir("data") if f.endswith('.dat')]
        for f in files:
            print(f"  - {f}")
    exit(1)

# Create the multi-radius gravitational wave plot
fig = plt.figure(figsize=(16, 12))

# Colors and styles for different radii
colors = ['red', 'blue', 'green', 'purple']
styles = ['-', '--', '-.', ':']
labels = []

print(f"\nProcessing gravitational waves at multiple extraction radii...")

# Plot 1: Real part of Weyl4 at different radii
plt.subplot(2, 3, 1)
for i, radius in enumerate(extraction_radii):
    # Calculate retarded time for this radius
    t_retarded = calculate_retarded_time(weyl4_data['time'], radius, M)
    
    # Plot the real part of Weyl4
    plt.plot(t_retarded, weyl4_data['real'], 
             color=colors[i], linestyle=styles[i], linewidth=2,
             label=f"r = {radius}M")
    
    print(f"  Processed r = {radius}M: retarded time range {t_retarded[0]:.1f} to {t_retarded[-1]:.1f}")

plt.xlabel("Retarded Time t/M")
plt.ylabel(f"Re[Ψ₄] Mode ({mode[0]},{mode[1]})")
plt.title("Gravitational Wave Signal - Real Part")
plt.legend()
plt.grid(True, alpha=0.3)
plt.xlim(-200, 200)  # Focus on interesting region

# Plot 2: Imaginary part
plt.subplot(2, 3, 2)
for i, radius in enumerate(extraction_radii):
    t_retarded = calculate_retarded_time(weyl4_data['time'], radius, M)
    plt.plot(t_retarded, weyl4_data['imag'], 
             color=colors[i], linestyle=styles[i], linewidth=2,
             label=f"r = {radius}M")

plt.xlabel("Retarded Time t/M")
plt.ylabel(f"Im[Ψ₄] Mode ({mode[0]},{mode[1]})")
plt.title("Gravitational Wave Signal - Imaginary Part")
plt.legend()
plt.grid(True, alpha=0.3)
plt.xlim(-200, 200)

# Plot 3: Amplitude comparison
plt.subplot(2, 3, 3)
for i, radius in enumerate(extraction_radii):
    t_retarded = calculate_retarded_time(weyl4_data['time'], radius, M)
    amplitude = np.abs(weyl4_data['complex'])
    plt.semilogy(t_retarded, amplitude, 
                 color=colors[i], linestyle=styles[i], linewidth=2,
                 label=f"r = {radius}M")

plt.xlabel("Retarded Time t/M")
plt.ylabel(f"|Ψ₄| Mode ({mode[0]},{mode[1]})")
plt.title("Gravitational Wave Amplitude (Log Scale)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.xlim(-200, 200)

# Plot 4: Time delay demonstration
plt.subplot(2, 3, 4)
coordinate_time = weyl4_data['time']
amplitude = np.abs(weyl4_data['complex'])

# Show the same signal as it arrives at different detectors
for i, radius in enumerate(extraction_radii):
    t_retarded = calculate_retarded_time(coordinate_time, radius, M)
    
    # Apply amplitude scaling (1/r falloff)
    scaled_amplitude = amplitude / radius
    
    plt.plot(coordinate_time, scaled_amplitude, 
             color=colors[i], linestyle=styles[i], linewidth=2,
             label=f"Detector at r = {radius}M")

plt.xlabel("Coordinate Time")
plt.ylabel("Scaled Amplitude |Ψ₄|/r")
plt.title("Signal Arrival Time at Different Detectors")
plt.legend()
plt.grid(True, alpha=0.3)

# Plot 5: Light travel time effects
plt.subplot(2, 3, 5)
for i, radius in enumerate(extraction_radii):
    # Calculate the time delay
    r_tortoise = radius + M * np.log(radius/(2.0*M) - 1.0)
    time_delay = r_tortoise / M
    
    # Plot vertical line showing when signal reaches each detector
    plt.axvline(x=time_delay, color=colors[i], linestyle=styles[i], 
                linewidth=3, label=f"r = {radius}M (delay = {time_delay:.1f}M)")

plt.xlabel("Time Delay (M)")
plt.ylabel("Detector")
plt.title("Light Travel Time to Different Radii")
plt.legend()
plt.grid(True, alpha=0.3)

# Plot 6: Physics explanation
plt.subplot(2, 3, 6)
plt.text(0.1, 0.8, "Multi-Radius GW Extraction", fontsize=14, weight='bold')
plt.text(0.1, 0.7, "Physics Concepts:", fontsize=12, weight='bold')
plt.text(0.1, 0.6, "• Retarded time: t_ret = (t - r*)/M", fontsize=10)
plt.text(0.1, 0.55, "• Tortoise coord: r* = r + M·ln(r/2M - 1)", fontsize=10)
plt.text(0.1, 0.5, "• Light travel time creates delays", fontsize=10)
plt.text(0.1, 0.45, "• Amplitude scales as 1/r", fontsize=10)

plt.text(0.1, 0.35, f"Parameters for Mode ({mode[0]},{mode[1]}):", fontsize=12, weight='bold')
plt.text(0.1, 0.3, f"• Total mass M = {M:.1f}", fontsize=10)
plt.text(0.1, 0.25, f"• Extraction radii: {extraction_radii}", fontsize=10)
plt.text(0.1, 0.2, f"• Data points: {len(weyl4_data['time'])}", fontsize=10)

# Calculate and display time delays
plt.text(0.1, 0.1, "Time delays (in units of M):", fontsize=10, weight='bold')
for i, radius in enumerate(extraction_radii):
    r_tortoise = radius + M * np.log(radius/(2.0*M) - 1.0)
    delay = r_tortoise / M
    plt.text(0.15, 0.05 - i*0.03, f"r = {radius}M: Δt = {delay:.1f}M", fontsize=9)

plt.xlim(0, 1)
plt.ylim(0, 1)
plt.axis('off')

plt.suptitle(f"Gravitational Wave Multi-Radius Extraction - Mode ({mode[0]},{mode[1]})", 
             fontsize=16, weight='bold')
plt.tight_layout()

# Save the plot
filename = f"GW_multi_radius_mode_{mode}.png"
plt.savefig(filename, dpi=300, bbox_inches='tight')
print(f"\nPlot saved as: {filename}")

# Print summary
print(f"\nGravitational Wave Multi-Radius Analysis:")
print("=" * 50)
print(f"Mode: ({mode[0]},{mode[1]})")
print(f"Total mass: {M:.1f}")
print(f"Data range: {weyl4_data['time'][0]:.1f} to {weyl4_data['time'][-1]:.1f}")
print(f"Max |Ψ₄|: {np.max(np.abs(weyl4_data['complex'])):.2e}")

print(f"\nExtraction radii and time delays:")
for radius in extraction_radii:
    r_tortoise = radius + M * np.log(radius/(2.0*M) - 1.0)
    delay = r_tortoise / M
    print(f"  r = {radius:3d}M: r* = {r_tortoise:6.1f}M, time delay = {delay:6.1f}M")

plt.show()