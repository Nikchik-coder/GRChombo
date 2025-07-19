# Start from a modern, stable version of Ubuntu
FROM ubuntu:24.04

# Avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install all the modern dependencies needed to build GRChombo
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    gfortran \
    openmpi-bin \
    libopenmpi-dev \
    libhdf5-openmpi-dev \
    liblapack-dev \
    libblas-dev \
    csh \
    && rm -rf /var/lib/apt/lists/*

# Set a working directory for the build
WORKDIR /app

# Clone the LATEST source code directly from the repositories
RUN git clone https://github.com/GRChombo/Chombo.git
RUN git clone https://github.com/GRChombo/GRChombo.git

# --- This part requires your Make.defs.local file ---
# Copy your Chombo configuration file into the build context.
# This file must be in the same directory as your Dockerfile when you build.
COPY Make.defs.local /app/Chombo/lib/mk/Make.defs.local

# Build the Chombo library using the modern compiler
RUN cd Chombo/lib && make lib -j$(nproc)

# Set the environment variable so the GRChombo makefile can find Chombo
ENV CHOMBO_HOME=/app/Chombo/lib

# Set the default working directory for when the container runs
WORKDIR /app/GRChombo/Examples/

# This command makes the container start a bash shell by default
CMD ["/bin/bash"]