# Binary Black Hole Simulation Visualization

A complete analysis and visualization toolkit for binary black hole numerical relativity simulations using GRChombo HDF5 output files.

## 🎯 Project Overview

This project provides tools to visualize and analyze numerical relativity simulations from GRChombo. It creates both individual plots and animated visualizations showing the evolution of key gravitational fields. The toolkit supports:

- **Binary Black Hole mergers**: Inspiral, merger, and ringdown phases
- **Kerr Black Hole simulations**: Single rotating black hole spacetimes  
- **General CCZ4 simulations**: All standard CCZ4 evolution variables

The enhanced scripts automatically detect available fields and create appropriate visualizations for any GRChombo simulation.

## 📁 Project Structure

```
Binary/
├── hdf5/                           # Simulation data files
│   ├── BinaryBH_000000.3d.hdf5   # Full resolution data (81 files)
│   └── BinaryBHPlot_000000.3d.hdf5 # Plot resolution data (81 files)
├── data/                          # Additional data files
│   ├── punctures.dat              # Black hole trajectory data
│   └── Weyl4_mode_*.dat          # Gravitational wave modes
├── plot.py                        # Original plotting script (FIXED)
├── corrected_plot.py              # Enhanced plotting script
├── create_animation.py            # Animation generation script
├── chi/                           # Generated chi field plots (81 images)
├── lapse/                         # Generated lapse field plots (81 images)
├── K/                             # Generated K field plots (81 images)
├── animation_chi_BinaryBH.gif     # Chi field evolution animation
├── animation_lapse_BinaryBH.gif   # Lapse field evolution animation
├── animation_K_BinaryBH.gif       # K field evolution animation
├── plot_gravitational_waves.py   # Gravitational wave analysis script
├── view_gw_plots.py               # GW plot viewer utility
├── gw_plots/                      # Generated GW visualization plots
├── gw_data/                       # Processed GW data files
├── venv/                          # Python virtual environment
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install yt h5py matplotlib numpy pillow imageio
```

### 2. Generate Plots and Animations

```bash
# Generate plots for all available fields (auto-detected)
source venv/bin/activate && python corrected_plot.py

# OR run with MPI for parallel processing
source venv/bin/activate && mpirun -n 4 python corrected_plot.py

# List available field directories after plotting
source venv/bin/activate && python create_animation.py --list

source venv/bin/activate && mpirun -n 4 python create_animation.py --list

# Create animations for all available fields
source venv/bin/activate && python create_animation.py all

# OR create animation for specific field
source venv/bin/activate && python create_animation.py chi

# Analyze gravitational wave data
source venv/bin/activate && python plot_gravitational_waves.py

source venv/bin/activate && mpirun -n 4 python plot_gravitational_waves.py
```

### 3. View Results

Your visualization files will be created:
- **Individual plots**: `chi/`, `lapse/`, `K/` directories
- **Animations**: `animation_*_BinaryBH.gif` files
- **Gravitational wave plots**: `gw_plots/` directory
- **Processed GW data**: `gw_data/` directory

## 📊 Generated Visualizations

### 🎬 Animations (GIF files)
- **`animation_chi_BinaryBH.gif`** (1.2MB) - Conformal factor evolution
- **`animation_lapse_BinaryBH.gif`** (1.5MB) - Lapse function evolution  
- **`animation_K_BinaryBH.gif`** (1.6MB) - Extrinsic curvature evolution

### 🌊 Gravitational Wave Analysis
- **`weyl4_overview.png`** - Weyl4 scalar analysis (all modes)
- **`strain_analysis.png`** - Gravitational wave strain and frequency  
- **`inspiral_merger_ringdown.png`** - Complete merger evolution

### 📈 Individual Plots
- **81 timesteps** covering simulation time 0.0 to 10.0 (in code units)
- **3 key fields** essential for understanding black hole physics
- **Z-slice plots** through the equatorial plane (z=0)

## 🔬 Physics of Visualized Fields

### `chi` - Conformal Factor
- **Physical meaning**: Overall spacetime curvature and structure
- **Range**: 0 (strong gravity) to 1 (flat spacetime)
- **What to observe**: 
  - Dark regions show black hole locations
  - Evolution during inspiral and merger
  - Formation of common horizon

### `lapse` - Lapse Function  
- **Physical meaning**: Time dilation effects
- **Range**: 0 (time stops) to 1 (normal time flow)
- **What to observe**:
  - Time slowing near black holes
  - Gauge effects during simulation
  - Coordinate singularity avoidance

### `K` - Extrinsic Curvature Trace
- **Physical meaning**: Spacetime expansion/contraction rate
- **Range**: Negative (contraction) to positive (expansion)
- **What to observe**:
  - Gravitational wave emission
  - Spacetime dynamics
  - Merger signature

## 🛠️ Code Documentation

### 1. `corrected_plot.py` - Main Plotting Script (Enhanced)

**Key Features:**
- **Auto-detection of available fields**: Automatically discovers all CCZ4 fields in simulation data
- **Support for all CCZ4 variables**: chi, lapse, K, Ham, A11-A33, h11-h33, Gamma1-3, shift1-3, B1-3, Theta
- **Intelligent field selection**: Prioritizes the most physically relevant fields
- **Proper colormap and scaling** for each field type
- **Error handling**: Continues plotting even if some fields are missing
- **Time annotations** on plots
- **Parallel processing support** with MPI

**Usage:**
```bash
source venv/bin/activate && python corrected_plot.py
```

**New Enhanced Features:**
```python
# AUTO-DETECTION: Checks what fields are available in the dataset
available_fields = [field[1] for field in ts[0].field_list if field[0] == 'chombo']
print("Available fields:", available_fields)

# INTELLIGENT SELECTION: Prioritizes best fields for visualization
potential_fields = ["chi", "lapse", "K", "Ham", "h11", "h22", "h33", 
                   "A11", "A22", "A33", "Gamma1", "Gamma2", "Gamma3", 
                   "shift1", "shift2", "shift3"]

# FIELD-SPECIFIC VISUALIZATION: Appropriate settings for each field type
if variable.startswith("A"):
    slc.set_cmap(field=variable, cmap="RdBu_r")  # Extrinsic curvature
elif variable.startswith("h"):
    slc.set_cmap(field=variable, cmap="viridis")  # Metric components
elif variable.startswith("Gamma"):
    slc.set_cmap(field=variable, cmap="RdBu_r")  # Connection coefficients
elif variable.startswith("shift"):
    slc.set_cmap(field=variable, cmap="RdBu_r")  # Shift vector
elif variable == "Ham":
    slc.set_cmap(field=variable, cmap="RdBu_r")  # Hamiltonian constraint

# ERROR HANDLING: Gracefully handles missing fields
try:
    produce_slice_plot(i, name)
except Exception as e:
    print(f"Error plotting {name}: {e}")
```

### 2. `create_animation.py` - Animation Generator (Enhanced)

**Features:**
- **Auto-detection of available fields**: Automatically finds all directories containing PNG files
- **Support for all CCZ4 fields**: Works with chi, lapse, K, Ham, A11, A12, h11, Gamma1, Theta, shift1, etc.
- **Multiple usage modes**: Create single animations, all animations, or list available fields
- **Flexible command-line interface** with enhanced options
- **Sample plot viewing** for any available field
- **Smart field discovery**: No longer hardcoded to specific fields

**Usage:**
```bash
# List available field directories
python create_animation.py --list

# Create animations for all available fields
python create_animation.py all

# Create animation for specific field
python create_animation.py chi --duration 0.3 --output custom_chi.gif

# View sample plot (any available field)
python create_animation.py A11 --show --timestep 40

# Run without arguments to see available fields and create all animations
python create_animation.py
```

**New Enhanced Functions:**
```python
def get_available_fields():
    """Auto-detect all directories with PNG files"""
    
def create_all_animations(duration=0.2):
    """Create animations for all available field directories"""
    
def list_available_fields():
    """List all available field directories and their contents"""
    
def create_animation(field_name, output_filename=None, duration=0.2):
    """Create GIF animation from PNG files"""
    
def show_sample_plot(field_name, timestep=0):
    """Display a sample plot for any field"""
```

**Command-line Options:**
- `--list, -l`: List available field directories
- `--show, -s`: Show sample plot instead of creating animation
- `--duration, -d`: Set frame duration (default: 0.2s)
- `--timestep, -t`: Which timestep to show (for --show option)
- `--output, -o`: Custom output filename

**Examples:**
```bash
# For GRChombo CCZ4 simulations with fields like:
# chi, lapse, K, Ham, A11, A12, A13, A22, A23, A33
# h11, h12, h13, h22, h23, h33, Gamma1, Gamma2, Gamma3
# shift1, shift2, shift3, B1, B2, B3, Theta

python create_animation.py chi      # Create chi animation
python create_animation.py Ham      # Create Hamiltonian constraint animation  
python create_animation.py A11      # Create A11 component animation
python create_animation.py all      # Create all available animations
```

### 3. `plot.py` - Original Script (Fixed)

**Fixed issues:**
- ✅ Data path corrected
- ✅ Compatible with current file structure
- ✅ Ready for single-field plotting

### 4. `plot_gravitational_waves.py` - Gravitational Wave Analyzer

**Features:**
- Loads Weyl4 mode data from `data/` directory
- Calculates gravitational wave strain via double integration: h = ∫∫ Ψ₄ dt dt
- Extracts frequency evolution from phase analysis
- Creates comprehensive visualizations
- Saves processed data for further analysis

**Key physics:**
```python
# Convert Weyl4 to strain (fundamental GW relationship)
psi4_int1 = cumulative_trapezoid(weyl4, time, initial=0)      # First integration
strain = cumulative_trapezoid(psi4_int1, time, initial=0)    # Second integration

# Extract frequency from phase evolution
frequency = (1/2π) * dφ/dt
```

**Usage:**
```bash
# Complete GW analysis
source venv/bin/activate && python plot_gravitational_waves.py

# View specific plots
source venv/bin/activate && python view_gw_plots.py weyl4
source venv/bin/activate && python view_gw_plots.py strain
source venv/bin/activate && python view_gw_plots.py imr
```

## 📋 Simulation Data Details

### Data Structure
- **Total files**: 162 HDF5 files (81 × 2 types)
- **Time range**: 0.0 to 10.0 code units
- **Domain size**: 16×16×8 code units
- **Grid resolution**: 32×32×16 base grid with AMR
- **Available fields**: 25 total fields

### Complete Field List
```
Physical fields: chi, lapse, K, Theta
Metric components: h11, h12, h13, h22, h23, h33  
Shift vector: shift1, shift2, shift3
Vector potential: A11, A12, A13, A22, A23, A33
Magnetic field: B1, B2, B3
Connection: Gamma1, Gamma2, Gamma3
```

## 🎨 Customization Options

### Plot Different Fields
Modify `variable_names` in `corrected_plot.py`:
```python
# Example: Plot metric components
variable_names = ["h11", "h22", "h33"]

# Example: Plot shift vector
variable_names = ["shift1", "shift2", "shift3"]
```

### Change Slice Direction
Modify `axis` variable:
```python
axis = "x"  # YZ-plane slice
axis = "y"  # XZ-plane slice  
axis = "z"  # XY-plane slice (default, equatorial)
```

### Custom Animation Settings
```python
# Slower animation (0.5s per frame)
create_animation("chi", duration=0.5)

# Faster animation (0.1s per frame)
create_animation("lapse", duration=0.1)
```

## 🔧 Troubleshooting

### Common Issues

**1. ModuleNotFoundError: No module named 'yt'**
```bash
source venv/bin/activate
pip install yt h5py matplotlib numpy pillow imageio
```

**2. No such file or directory: 'hdf5/'**
- Ensure HDF5 files are in `hdf5/` directory
- Check file permissions

**3. AttributeError: 'AxisAlignedSlicePlot' object has no attribute 'set_window_size'**
- This was fixed in `corrected_plot.py` by using `set_width()` instead

### Performance Tips
- Use virtual environment to avoid package conflicts
- For large datasets, consider plotting subset of timesteps
- Adjust `slc.set_buff_size()` for different image quality vs. speed

## 📈 Analysis Workflow

### Step-by-Step Process

1. **Setup Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install yt h5py matplotlib numpy pillow imageio
   ```

2. **Generate Individual Plots**
   ```bash
   python corrected_plot.py
   # Creates: chi/, lapse/, K/ directories with 81 PNG files each
   ```

3. **Create Animations**
   ```bash
   python create_animation.py
   # Creates: animation_*_BinaryBH.gif files
   ```

4. **Analysis and Interpretation**
   - View animations to understand overall evolution
   - Examine individual timesteps for detailed analysis
   - Compare different fields to understand physics

### Scientific Analysis Questions

**Questions to explore with your visualizations:**
- When do the black holes merge? (Look for horizon formation in `chi`)
- How does time dilation evolve? (Track `lapse` evolution)
- What gravitational wave patterns emerge? (Study `K` field dynamics)
- How does the spacetime geometry change? (Compare all three fields)

## 🎯 Results Summary

### What You've Accomplished
- ✅ **Fixed original plotting code** - Corrected paths and API issues
- ✅ **Enhanced visualization** - Added optimal field selection and colormaps  
- ✅ **Generated complete dataset** - 243 individual plots across 81 timesteps
- ✅ **Created animations** - 3 GIF files showing field evolution
- ✅ **Analyzed gravitational waves** - Complete Weyl4 to strain analysis
- ✅ **Built analysis toolkit** - Reusable scripts for future simulations

### Generated Files
- **Individual plots**: 243 PNG files (81 timesteps × 3 fields)
- **Animations**: 3 GIF files (4.3MB total)
- **GW visualizations**: 3 comprehensive gravitational wave plots
- **Processed GW data**: 6 data files with strain and frequency evolution
- **Analysis scripts**: 5 Python files with full documentation

### 🌊 Gravitational Wave Results
- **Dominant mode**: (l,m) = (2,2) with max strain amplitude 1.08×10⁻¹
- **Secondary modes**: (2,0) and (2,1) provide additional physics information
- **Complete evolution**: Inspiral → Merger → Ringdown phases clearly visible
- **Frequency evolution**: Shows characteristic "chirp" pattern of binary coalescence

## 🚀 Future Extensions

### Possible Enhancements
1. **3D Volume Rendering** - Use yt's volume rendering for 3D visualization
2. **Gravitational Wave Extraction** - Analyze Weyl4 modes for GW signals
3. **Trajectory Analysis** - Use puncture data to track black hole orbits
4. **Comparative Analysis** - Plot multiple fields simultaneously
5. **Interactive Visualization** - Create web-based interactive plots

### Advanced Analysis
```python
# Example: 3D volume rendering
from yt import Scene
sc = Scene()
vol = sc.add_volume(ds, ("chombo", "chi"))
sc.render()

# Example: Multi-field comparison
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
# Plot chi, lapse, K side by side
```

## 📚 References

- **GRChombo**: [https://www.grchombo.org/](https://www.grchombo.org/)
- **yt Project**: [https://yt-project.org/](https://yt-project.org/)
- **Numerical Relativity**: Baumgarte & Shapiro textbook
- **Binary Black Holes**: [LIGO Scientific Papers](https://www.ligo.org/science/Publication-O3bCatalog/)

## 📧 Contact & Support

For questions about this visualization toolkit or binary black hole simulations:
- Check GRChombo documentation
- Review yt visualization examples  
- Consult numerical relativity literature

---

**Last Updated**: July 2025  
**Version**: 1.0  
**Status**: Production Ready ✅



nik@Nik:~/GRChombo$ 
miltonian_norm_vs_time.png
python3 Animation/compute_and_plot_hamiltonian.py /home/nik/GRChombo_runs/Wormhole_Collapse/ --output_dir Animation/

python3 Animation/plot_hamiltonian.py /home/nik/GRChombo_runs/Wormhole_Collapse/hdf5/Wormhole_p_000000.3d.hdf5 --output_dir Animation