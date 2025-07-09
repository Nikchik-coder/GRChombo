# GRChombo Installation Guide

Complete step-by-step guide for installing and running GRChombo on Debian/Ubuntu systems.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [System Preparation](#system-preparation)
3. [Download Source Code](#download-source-code)
4. [Configure and Build Chombo](#configure-and-build-chombo)
5. [Build GRChombo Example](#build-grchombo-example)
6. [Run Simulation](#run-simulation)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

This guide assumes you have:
- A Debian/Ubuntu-based Linux system
- Administrative (sudo) privileges
- Basic familiarity with terminal commands

## System Preparation

### Update System Packages

```bash
sudo apt update
```

### Install Required Dependencies

Install all necessary compilers, libraries, and tools:

```bash
sudo apt install build-essential gfortran openmpi-bin libopenmpi-dev \
                 libhdf5-openmpi-dev liblapack-dev libblas-dev csh
```

**Package breakdown:**
- `build-essential`: C/C++ compilers and build tools
- `gfortran`: Fortran compiler
- `openmpi-bin libopenmpi-dev`: MPI implementation for parallel computing
- `libhdf5-openmpi-dev`: Parallel HDF5 library for data I/O
- `liblapack-dev libblas-dev`: Linear algebra libraries
- `csh`: C shell (required by Chombo build system)

## Download Source Code

### Navigate to Home Directory

```bash
cd ~
```

### Clone Chombo Library

```bash
git clone https://github.com/GRChombo/Chombo.git
```

### Clone GRChombo

```bash
git clone https://github.com/GRChombo/GRChombo.git
```

## Configure and Build Chombo

### Navigate to Chombo Configuration Directory

```bash
cd ~/Chombo/lib/mk
```

### Create Configuration File

Create the Chombo configuration file:

```bash
nano Make.defs.local
```

### Configuration Content

Copy and paste the following configuration:

```makefile
# Make.defs.local - Chombo configuration for GRChombo
makefiles+=Make.defs.local

################################################################
# Core Configuration
################################################################
DIM                = 3
DEBUG              = FALSE
OPT                = HIGH
PRECISION          = DOUBLE
MPI                = TRUE
OPENMPCC           = TRUE
CXX                = g++
FC                 = gfortran
MPICXX             = mpicxx

################################################################
# Optional Features & HDF5 Configuration
################################################################
USE_HDF            = TRUE
USE_64             = TRUE
USE_MT             = FALSE

# HDF5 library paths for Debian/Ubuntu systems
HDFINCFLAGS        = -I/usr/include/hdf5/openmpi
HDFLIBFLAGS        = -L/usr/lib/x86_64-linux-gnu/hdf5/openmpi -lhdf5 -lz
HDFMPIINCFLAGS     = -I/usr/include/hdf5/openmpi
HDFMPILIBFLAGS     = -L/usr/lib/x86_64-linux-gnu/hdf5/openmpi -lhdf5 -lz

################################################################
# Compiler Optimization & System Libraries
################################################################
cxxoptflags        = -O3 -march=native
foptflags          = -O3 -march=native
syslibflags        = -lblas -llapack
```

Save and exit the file (`Ctrl+X`, then `Y`, then `Enter` in nano).

### Build Chombo Library

```bash
cd ~/Chombo/lib
make realclean
make lib -j 8
```

**Note:** The compilation process will take significant time. Look for `ar: creating ...` and `ranlib ...` messages indicating successful completion.

## Build GRChombo Example

### Set Environment Variable

Set the Chombo path for the current session:

```bash
export CHOMBO_HOME=/home/nik/Chombo/lib
```

### Make Environment Variable Permanent

Add to your shell configuration:

```bash
echo 'export CHOMBO_HOME=/home/nik/Chombo/lib' >> ~/.bashrc
source ~/.bashrc
```

### Compile Binary Black Hole Example

```bash
cd ~/GRChombo/Examples/BinaryBH
make all
```

This creates the main executable file in the BinaryBH directory.

## Run Simulation

### Create Output Directory

```bash
mkdir -p /home/nik/GRChombo_runs/BBH_run_1
```

### Configure Simulation Parameters

Edit the parameter file:

```bash
cd ~/GRChombo/Examples/BinaryBH
nano params.txt
```

Find and modify the output path line:

```bash
# Change from:
# output_path = ""

# To:
output_path = "/home/nik/GRChombo_runs/BBH_run_1/"
```

Save the file.

### Execute Simulation

Run the simulation with MPI using the full command:

```bash
# Run with 4 processors (full simulation)
EXEC_NAME=$(ls Main_BinaryBH*.ex) && mpirun -np 4 ./$EXEC_NAME params.txt
```

For a quick test run, use the lightweight parameters:

```bash
# Run with 1 processor (quick test)
EXEC_NAME=$(ls Main_BinaryBH*.ex) && mpirun -np 1 ./$EXEC_NAME params_very_cheap.txt
```

**Alternative:** You can also run the commands separately in the same shell session:

```bash
# Set the executable name variable
EXEC_NAME=$(ls Main_BinaryBH*.ex)

# Then run the simulation (choose one)
mpirun -np 1 ./$EXEC_NAME params.txt          # Full simulation
mpirun -np 1 ./$EXEC_NAME params_very_cheap.txt  # Quick test


mpirun -np 1 ./Main_Wormhole_collapse3d.Linux.64.mpicxx.gfortran.OPTHIGH.MPI.OPENMPCC.ex params.txt
```

## Verification

### Monitor Simulation Progress

You should now see the simulation running in your terminal, with time steps advancing. The simulation will display time step information similar to:

```
GRAMRLevel::advance level 0 at time 0 (0 M/hr). Boxes on this rank: 1 / 1
GRAMRLevel::advance level 1 at time 0 (0 M/hr). Boxes on this rank: 1 / 2
GRAMRLevel::advance level 2 at time 0 (0 M/hr). Boxes on this rank: 1 / 2
```

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

## Troubleshooting

### Common Issues

1. **Missing csh shell**: Install with `sudo apt install csh`
2. **HDF5 library not found**: Verify paths in `Make.defs.local`
3. **MPI compilation errors**: Ensure OpenMPI development packages are installed
4. **Permission errors**: Check directory permissions for output path

### Getting Help

- Check the [GRChombo documentation](https://github.com/GRChombo/GRChombo)
- Review Chombo installation notes in `InstallNotes/MakeDefsLocalExamples/`
- Examine example configurations for your system type

### Performance Notes

- Use `params_very_cheap.txt` for quick testing
- Adjust processor count (`-np` parameter) based on your system capabilities
- Monitor system resources during longer simulations

---

**Success!** You now have a fully functional GRChombo installation ready for numerical relativity simulations.


