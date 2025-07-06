# KerrBH Example - Build and Run Guide

This directory contains the KerrBH example for GRChombo, which simulates a Kerr black hole spacetime.

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
make Main_KerrBH
```

This will create an executable with a name like:
```
Main_KerrBH3d.Linux.64.mpicxx.gfortran.OPTHIGH.MPI.OPENMPCC.ex
```

The exact name depends on your system configuration and compiler settings.

### 3. Verify the Build

Check that the executable was created:
```bash
ls -la Main_KerrBH*.ex
```

## Running the Simulation

### Available Parameter Files

This example provides two parameter files:
- `params.txt` - Full resolution simulation
- `params_cheap.txt` - Reduced resolution for testing

### Run Command

```bash
export EXEC_NAME=Main_KerrBH3d.Linux.64.mpicxx.gfortran.OPTHIGH.MPI.OPENMPCC.ex
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
export EXEC_NAME=Main_KerrBH3d.Linux.64.mpicxx.gfortran.OPTHIGH.MPI.OPENMPCC.ex
```

### Issue 2: "No such file or directory" for Make.test
**Problem**: `CHOMBO_HOME` is set to an incorrect path.

**Solution**: Find the correct path and set it:
```bash
find /home/nik -name "Make.test" -type f 2>/dev/null
export CHOMBO_HOME=/path/to/correct/chombo/lib
```

### Issue 3: Parameter file not found
**Problem**: Trying to use `params_very_cheap.txt` which doesn't exist for this example.

**Solution**: Use one of the available parameter files:
- `params_cheap.txt` for quick testing
- `params.txt` for full simulation

## Output

The simulation will create several output directories:
- `d/` - Contains diagnostic data
- `f/` - Contains field data
- `o/` - Contains object files from compilation
- `p/` - Contains plot files

## Parameter File Modification

You can modify the parameter files to adjust:
- Grid resolution
- Simulation time
- Output frequency
- Black hole parameters (mass, spin, etc.)

Refer to the GRChombo documentation for detailed parameter descriptions.

## Example Workflow

```bash
# 1. Set environment
export CHOMBO_HOME=/home/nik/Chombo/Chombo/lib

# 2. Build
make Main_KerrBH

# 3. Set executable name
export EXEC_NAME=Main_KerrBH3d.Linux.64.mpicxx.gfortran.OPTHIGH.MPI.OPENMPCC.ex

# 4. Run simulation
mpirun -np 1 ./$EXEC_NAME params_cheap.txt
```

## Notes

- The executable name will vary depending on your system configuration
- Use `params_cheap.txt` for initial testing to ensure everything works
- The simulation will create output files in the current directory
- Monitor the output for any error messages or warnings 