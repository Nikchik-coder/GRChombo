# GRChombo on Google Cloud Platform

A complete guide for running GRChombo numerical relativity simulations on Google Cloud Platform with cost-effective, scalable infrastructure.

This workflow uses a three-phase approach to minimize costs: build a reusable "golden image" on a small VM, then launch powerful compute instances only when needed for simulations.

## Overview

The strategy separates one-time setup from repeatable computation:

1. **Preparation Phase** - Install software on a small, inexpensive VM
2. **Imaging Phase** - Create a reusable custom machine image  
3. **Production Phase** - Launch powerful VMs on-demand for simulations

## Quick Start

### Phase 1: Environment Preparation

Create a setup VM for software installation:

```bash
# VM Configuration
Name: grchombo-setup-vm
Machine type: e2-medium (2 vCPUs, 4 GB memory)
Boot disk: Debian 12
Region: us-central1-a (remember for later)
```

#### Adding More Memory During Setup

If you encounter memory issues during compilation (common with large C++ projects), you can increase the VM's memory:

**Option 1: Resize Existing VM**
1. Stop the `grchombo-setup-vm`
2. Go to **Compute Engine > VM instances**
3. Click on your VM name
4. Click **EDIT** at the top
5. Under **Machine configuration**, change machine type to:
   - `e2-standard-4` (4 vCPUs, 16 GB memory) - recommended for compilation
   - `e2-highmem-2` (2 vCPUs, 16 GB memory) - memory-optimized option
6. Click **Save** and restart the VM

**Option 2: Add Swap Space (if resizing isn't sufficient)**
```bash
# Create a 4GB swap file
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make swap permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verify swap is active
free -h
```

**When to Increase Memory:**
- **Direct Installation**: Chombo compilation can use 8+ GB during peak build
- **Error Signs**: "virtual memory exhausted", "make: *** [target] Killed", or build hanging

### Phase 2: Software Installation

Connect via SSH and install GRChombo from source:

#### Step 2.1: System Preparation

Update system packages:
```bash
sudo apt update
```

Install required dependencies:
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

#### Step 2.2: Download Source Code

Navigate to home directory and clone repositories:
```bash
cd ~
git clone https://github.com/GRChombo/Chombo.git
git clone https://github.com/GRChombo/GRChombo.git
```

#### Step 2.3: Configure Chombo

Navigate to Chombo configuration directory:
```bash
cd ~/Chombo/lib/mk
```

Create the Chombo configuration file:
```bash
nano Make.defs.local
```

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

#### Step 2.4: Build Chombo Library

```bash
cd ~/Chombo/lib
make realclean
make lib -j 8
```

**Note:** The compilation process will take significant time (potentially 30+ minutes). Look for `ar: creating ...` and `ranlib ...` messages indicating successful completion.

#### Step 2.5: Build GRChombo Example

Set environment variable and build example:
```bash
# Set Chombo path
export CHOMBO_HOME=~/Chombo/lib
echo 'export CHOMBO_HOME=~/Chombo/lib' >> ~/.bashrc

# Compile Binary Black Hole example
cd ~/GRChombo/Examples/BinaryBH
make all
```

This creates the main executable file in the BinaryBH directory.

### Phase 3: Create Machine Image

1. Stop the setup VM
2. Navigate to **Compute Engine > Machine Images**
3. Click **CREATE MACHINE IMAGE**
4. Configure:
   - Name: `grchombo-debian12-image`
   - Source: `grchombo-setup-vm`
5. Delete the setup VM to stop costs

## Running Simulations

### Launch Compute Instance

Create a powerful VM from your custom image:

```bash
# VM Configuration
Name: grchombo-compute-job-1
Machine type: c4-standard-8 (8 vCPUs, 30 GB memory)
Boot disk: Custom image (grchombo-debian12-image)
Zone: Same as data disk
```

### Attach Data Storage

1. **Create disk**: Navigate to **Compute Engine > Disks**
   - Name: `grchombo-data-disk-1`
   - Size: 500 GB - 2 TB (as needed)
   - Zone: Same as compute VM

2. **Attach disk**: Edit VM and attach the data disk

3. **Format and mount**:
```bash
# Format the disk
sudo mkfs.ext4 -m 0 -E lazy_itable_init=0,lazy_journal_init=0,discard /dev/sdb

# Create mount point and mount
sudo mkdir -p /mnt/data
sudo mount -o discard,defaults /dev/sdb /mnt/data
sudo chmod a+w /mnt/data

# Make permanent
echo "UUID=$(sudo blkid -s UUID -o value /dev/sdb) /mnt/data ext4 discard,defaults,nofail 0 2" | sudo tee -a /etc/fstab
```

### Execute Simulation

```bash
# Create working directory
mkdir /mnt/data/simulation1
cd /mnt/data/simulation1

# Navigate to GRChombo example
cd ~/GRChombo/Examples/BinaryBH

# Configure output path in params.txt
nano params.txt
# Change: output_path = "/mnt/data/simulation1/"

# Run simulation
EXEC_NAME=$(ls Main_BinaryBH*.ex)
mpirun -np 4 ./$EXEC_NAME params.txt

# For quick test, use:
# mpirun -np 1 ./$EXEC_NAME params_very_cheap.txt
```

### Monitor Simulation Progress

Open another terminal to monitor output:
```bash
# Check output files
cd /mnt/data/simulation1/
ls -la

# Follow live simulation output
tail -f pout/pout.0
```

You should see time step progression and output files being created.

## Cost Management

### Cleanup After Simulation

**Critical**: Delete the compute VM immediately after simulation completion to stop expensive hourly charges.

**Keep**:
- Custom machine image (minimal storage cost)
- Data disk (until data is backed up)

**Delete**:
- Compute VM instance (stops per-hour charges)

### Recommended VM Types

- **Setup Phase**: `e2-medium` (start), `e2-standard-4` (if compilation issues)
- **Compute Phase**: `c4-standard-8` or larger (high performance)
- **Storage**: Persistent SSD for speed, Standard for economy

## Troubleshooting

- Ensure VM and data disk are in the same zone
- Use `nofail` option in `/etc/fstab` for data disk mounting
- Monitor costs in Google Cloud Console billing section
- Test with small simulations before running large jobs
- **Memory Issues**: Resize VM or add swap space during setup phase
- **Compilation Failures**: Increase to `e2-standard-4` or `e2-highmem-2` for setup VM
- **Missing csh shell**: Install with `sudo apt install csh`
- **HDF5 library not found**: Verify paths in `Make.defs.local`
- **MPI compilation errors**: Ensure OpenMPI development packages are installed

## Support

For GRChombo-specific issues, consult the main [GRChombo documentation](https://github.com/GRChombo/GRChombo/wiki).

For Google Cloud Platform issues, see the [GCP documentation](https://cloud.google.com/docs).