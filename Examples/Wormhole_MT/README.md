# Wormhole_collapse Example - Build and Run Guide

This directory contains the Wormhole_collapse example for GRChombo, which simulates the collapse of a traversable wormhole spacetime.

## Prerequisites

- GRChombo source code
- Chombo library properly installed
- MPI implementation (OpenMPI or MPICH)
- HDF5 library
- LAPACK and BLAS libraries

## Build Process

### 1. Set Environment Variables

First, ensure that `CHOMBO_HOME` is set to the correct path. The makefile needs to find `Make.test`:

```bash
export CHOMBO_HOME=/home/nik/Chombo/Chombo/lib
```

**Note**: The common mistake is setting `CHOMBO_HOME=/home/nik/Chombo/lib` which is incorrect. The correct path should include the nested `Chombo` directory.

### 2. Build the Executable

```bash
make Main_Wormhole_collapse
```

This will create an executable with a name like:
```
Main_Wormhole_collapse3d.Linux.64.mpicxx.gfortran.OPTHIGH.MPI.OPENMPCC.ex
```

The exact name depends on your system configuration and compiler settings.

### 3. Verify the Build

Check that the executable was created:
```bash
ls -la Main_Wormhole_collapse*.ex
```

## Running the Simulation

### Available Parameter Files

This example provides two parameter files:
- `params.txt` - Full resolution simulation
- `params_cheap.txt` - Reduced resolution for testing

### Run Command

```bash
export EXEC_NAME=Main_Wormhole_collapse3d.Linux.64.mpicxx.gfortran.OPTHIGH.MPI.OPENMPCC.ex
mpirun -np 1 ./$EXEC_NAME params_cheap.txt
```

Replace the executable name with your actual built executable name.

For parallel execution with multiple cores:
```bash
mpirun -np 4 ./$EXEC_NAME params_cheap.txt
```

## Common Issues and Solutions

### Issue 1: "Permission denied" when running executable
**Problem**: The `EXEC_NAME` variable is not set, causing the command to try to run `./` instead of the actual executable.

**Solution**: Set the `EXEC_NAME` variable to the full executable name:
```bash
export EXEC_NAME=Main_Wormhole_collapse3d.Linux.64.mpicxx.gfortran.OPTHIGH.MPI.OPENMPCC.ex
```

### Issue 2: "No such file or directory" for Make.test
**Problem**: `CHOMBO_HOME` is set to an incorrect path.

**Solution**: Find the correct path and set it:
```bash
find /home/nik -name "Make.test" -type f 2>/dev/null
export CHOMBO_HOME=/path/to/correct/chombo/lib
```

### Issue 3: Parameter file not found
**Problem**: Trying to use a parameter file that doesn't exist.

**Solution**: Use one of the available parameter files:
- `params_cheap.txt` for quick testing
- `params.txt` for full simulation

### Issue 4: Compilation errors
**Problem**: Missing includes or incorrect header guards.

**Solution**: Ensure all source files are properly configured:
- `SimulationParameters.hpp` should exist (renamed from `WormholeSimParams.hpp`)
- Include paths in `GNUmakefile` should include `BlackHoles` directory
- Header guards should match between `.hpp` and `.impl.hpp` files

## Physical Description

This example simulates a traversable wormhole that collapses over time. The initial data consists of:

- **Wormhole throat**: Characterized by the throat radius parameter `b0`
- **Shape function**: b(r) = b₀²/r for r > b₀
- **Redshift function**: Constant redshift Φ₀ affecting the lapse function
- **Time-symmetric slice**: Initial extrinsic curvature set to zero

Key parameters that can be adjusted:
- `throat_radius` - The initial radius of the wormhole throat
- `redshift_constant` - Controls the lapse function via α = exp(Φ₀)

## Output

The simulation will create several output directories:
- `d/` - Contains diagnostic data
- `f/` - Contains field data  
- `o/` - Contains object files from compilation
- `p/` - Contains plot files

Output data includes:
- Metric components (h_ij)
- Extrinsic curvature (A_ij) 
- Conformal factor (chi)
- Lapse function (alpha)
- Shift vector (beta_i)

## Parameter File Modification

You can modify the parameter files to adjust:
- Grid resolution
- Simulation time
- Output frequency
- Wormhole parameters (throat radius, redshift constant)
- Grid center location

Refer to the GRChombo documentation for detailed parameter descriptions.

## Example Workflow

```bash
# 1. Set environment
export CHOMBO_HOME=/home/nik/Chombo/Chombo/lib

# 2. Build
make Main_Wormhole_collapse

# 3. Set executable name  
export EXEC_NAME=Main_Wormhole_collapse3d.Linux.64.mpicxx.gfortran.OPTHIGH.MPI.OPENMPCC.ex

# 4. Run simulation
mpirun -np 2 ./$EXEC_NAME params_cheap.txt


### Check Output Files

**Open another terminal** to monitor the creation of output files while the simulation runs:

```bash
# Navigate to your output directory
cd /home/nik/GRChombo_runs/BBH_run_1/

# Check for output files
ls -la

# Monitor the pout directory for processor output
ls -la pout/

# Follow the live simulation output (most useful)
tail -f pout/pout.0

# Watch for new files being created (optional)
watch -n 5 'ls -la'
```

You should see:
- `pout/` directory with processor output files (`pout.0`, `pout.1`, etc.)
- Plot files (`.hdf5` files) and checkpoint files as the simulation progresses
- Various diagnostic output files

```

mpirun -np 1 ./Main_Wormhole_collapse3d.Linux.64.mpicxx.gfortran.OPTHIGH.MPI.OPENMPCC.ex params.txt

## Notes

- The executable name will vary depending on your system configuration
- Use `params_cheap.txt` for initial testing to ensure everything works
- The simulation will create output files in the current directory
- Monitor the output for any error messages or warnings
- This example demonstrates the collapse of a traversable wormhole, which typically occurs on dynamical timescales
- The simulation uses the CCZ4 formulation of Einstein's equations with moving puncture gauge conditions 



      
mpirun -np 2 --allow-run-as-root ./Main_Wormhole_collapse3d_ch.Linux.64.mpicxx.gfortran.DEBUG.OPT.MPI.OPENMPCC.ex params.txt

    