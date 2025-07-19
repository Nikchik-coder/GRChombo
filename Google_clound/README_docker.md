# GRChombo Docker Workflow

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://hub.docker.com/r/grchombo/grchombo)
[![GRChombo](https://img.shields.io/badge/GRChombo-Numerical%20Relativity-blue)](https://github.com/GRChombo/GRChombo)

> A containerized development environment for custom GRChombo simulations that separates your code from complex software dependencies.

## Overview

This Docker workflow allows you to:
- Write and edit code on your local machine
- Use the official GRChombo Docker image as a pre-packaged development environment
- Compile and run simulations in a consistent, portable environment
- Keep your custom code separate from the complex GRChombo software stack

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Development Workflow](#development-workflow)
- [Monitoring Simulations](#monitoring-simulations)
- [Troubleshooting](#troubleshooting)
- [Directory Structure](#directory-structure)
- [Benefits](#benefits)

## Prerequisites

- **Docker Engine**: Installed and running on your system
- **Linux Users**: Use official Docker Engine from Docker's repository (avoid snap packages)
- **Project Structure**: Your work must be in a GRChombo directory containing `Source/` and `Examples/` subdirectories

## Quick Start

```bash
# 1. Navigate to your GRChombo project root
cd /home/nik/GRChombo/

# 2. Start Docker container with mounted project
docker run -v $(pwd):/my_project -it grchombo/grchombo /bin/bash

# 3. Inside container: navigate to your example
cd /my_project/Examples/Wormhole_MT/

# 4. Compile and run
make
ls *.ex  # Find the actual executable name
mpirun -np 4 --allow-run-as-root ./[TAB-complete-executable-name] params.txt
```

## Installation

### 1. Install Docker Engine

**Linux (Ubuntu/Debian):**
```bash
# Install Docker from official repository (NOT snap)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

**Fix AppArmor issues (if needed):**
```bash
sudo apt-get install apparmor-utils
sudo aa-complain /etc/apparmor.d/docker
sudo systemctl restart docker
```

### 2. Download GRChombo Environment

```bash
docker pull grchombo/grchombo
```

### 3. Organize Project Directory

Ensure your project follows this structure:
```
/home/nik/GRChombo/
├── Source/
├── Examples/
│   └── Wormhole_MT/          # Your custom simulation
│       ├── GNUmakefile
│       ├── params.txt
│       └── *.cpp, *.hpp files
└── [other GRChombo directories]
```

## Development Workflow

### Phase 1: Container Setup

1. **Navigate to project root** (critical step):
   ```bash
   cd /home/nik/GRChombo/
   ```

2. **Start Docker container**:
   ```bash
   docker run -v $(pwd):/my_project -it grchombo/grchombo /bin/bash
   ```
   
   > 💡 Your terminal prompt will change to `root@...`, indicating you're inside the container.

3. **Navigate to your custom example**:
   ```bash
   cd /my_project/Examples/Wormhole_MT/
   ```

### Phase 2: Configuration

**Configure output path in `params.txt`:**

✅ **Correct** (relative path):
```
output_path = "simulation_output/"
```

❌ **Incorrect** (absolute path):
```
output_path = "/home/nik/..."
```

### Phase 3: Compile and Run

1. **Compile your code**:
   ```bash
   make
   ```

2. **Find your executable name**:
   ```bash
   ls *.ex
   ```
   > 💡 GRChombo creates executables with long, descriptive names like `Main_Wormhole_collapse3d_ch.Linux.64.mpicxx.gfortran.DEBUG.OPT.MPI.OPENMPCC.ex`

3. **Run simulation**:
   ```bash
   # Use TAB completion after typing the first few characters
   mpirun -np 4 --allow-run-as-root ./Main_[TAB] params.txt
   
   # Or copy the full name from ls output:
   mpirun -np 4 --allow-run-as-root ./Main_Wormhole_collapse3d_ch.Linux.64.mpicxx.gfortran.DEBUG.OPT.MPI.OPENMPCC.ex params.txt
   ```
   
   > ⚠️ The `--allow-run-as-root` flag is required when running as root inside the container.

## Monitoring Simulations

### Real-time Output Monitoring

**In a NEW local terminal** (keep simulation running in the original):

1. **Check output files**:
   ```bash
   ls -l /home/nik/GRChombo/Examples/Wormhole_MT/simulation_output/
   ```

2. **Monitor live simulation log**:
   ```bash
   tail -f /home/nik/GRChombo/Examples/Wormhole_MT/pout/pout.0
   ```

### Expected Output

You should see HDF5 files appearing in real-time:
- `*.3d.hdf5` - 3D simulation data
- `*.checkpoint.3d.hdf5` - Checkpoint files for restarts
- `pout/pout.*` - Log files with simulation progress

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| **Permission denied errors** | Ensure Docker is installed from official repository, not snap |
| **Files not appearing locally** | Check that output path in `params.txt` is relative |
| **Container won't start** | Try `sudo aa-complain /etc/apparmor.d/docker` on Linux |
| **Build fails** | Ensure you're in the correct directory with `GNUmakefile` |
| **MPI errors** | Always include `--allow-run-as-root` flag |
| **"Unable to launch executable"** | Use `ls *.ex` to find the actual executable name, don't guess |
| **Wrong executable name** | Use TAB completion: type `./Main_[TAB]` to auto-complete |

### Debugging Commands

```bash
# Check Docker is running
docker --version
docker ps

# Verify container can access files
docker run -v $(pwd):/my_project -it grchombo/grchombo ls -la /my_project

# Test AppArmor status (Linux)
sudo aa-status | grep docker
```

### Executable Name Tips

**GRChombo generates very long executable names** like:
```
Main_Wormhole_collapse3d_ch.Linux.64.mpicxx.gfortran.DEBUG.OPT.MPI.OPENMPCC.ex
```

**Helpful shortcuts:**

```bash
# Use tab completion (type first few chars + TAB)
mpirun -np 4 --allow-run-as-root ./Main_[TAB] params.txt

# Create a shorter symlink
ln -s Main_Wormhole_collapse*.ex wormhole.ex
mpirun -np 4 --allow-run-as-root ./wormhole.ex params.txt

# Use wildcards (if only one .ex file exists)
mpirun -np 4 --allow-run-as-root ./Main_Wormhole_collapse*.ex params.txt
```

## Directory Structure

After setup, your local directory structure will look like:

```
/home/nik/GRChombo/
├── Examples/
│   └── Wormhole_MT/
│       ├── simulation_output/     # ← Output appears here
│       │   ├── *.3d.hdf5
│       │   └── *.checkpoint.3d.hdf5
│       ├── pout/                  # ← Log files
│       │   └── pout.0
│       ├── Main_Wormhole_collapse3d_ch.Linux.64.mpicxx.gfortran.DEBUG.OPT.MPI.OPENMPCC.ex
│       ├── params.txt
│       └── source files...
└── Source/
```

## Benefits

- ✅ **Portable**: Works consistently across different systems
- ✅ **Clean**: Separates your code from complex dependencies  
- ✅ **Reproducible**: Same environment for all team members
- ✅ **Safe**: No need to install GRChombo dependencies locally
- ✅ **Efficient**: File sharing between host and container

---

**Need help?** Check the [GRChombo documentation](https://github.com/GRChombo/GRChombo) or open an issue in the repository.