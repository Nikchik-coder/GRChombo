# Running GRChombo with Docker on Google Cloud

## Phase 1: Pre-flight Check (One-Time Setup)

Before you begin, ensure you have completed the following one-time setup tasks:

1. **Custom Docker Image Built**: You have created a modern, optimized Docker image (e.g., `grchombo-dev`).

2. **Artifact Registry Setup**:
   - You have created a Docker repository in Google Artifact Registry.
   - You have pushed your custom image to this repository.

3. **Cloud Storage Bucket Created**:
   - You have created a Google Cloud Storage Bucket for long-term data archival (e.g., `gs://rock-wonder-466311-g6-grchombo-results`). 
   - We recommend the Coldline storage class for cost savings.

4. **Project Code in Git**: Your GRChombo project, including your custom example, is available in a Git repository (e.g., on GitHub) for easy cloning.

## Phase 2: Cloud Test Run on a Low-Power VM

Always perform a quick, cheap test run to ensure your setup works before launching an expensive machine.

### Step 2.1: Create the Test VM

1. Navigate to **Compute Engine > VM instances** and click **CREATE INSTANCE**.

2. Configure the VM:
   - **Name**: `grchombo-test-node`
   - **Machine type**: An inexpensive `e2-medium` (2 vCPUs, 4 GB memory) is perfect for this.
   - **Boot disk**: Debian 12 or Ubuntu.
   - **Identity and API access**:
     - **Access scopes**: Select "Allow full access to all Cloud APIs". This is critical for pulling from Artifact Registry and writing to a Storage Bucket.

3. Click **Create**.

### Step 2.2: Prepare the Test VM Environment

1. SSH into `grchombo-test-node`.

2. Install tools:
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io git
   ```

3. Authenticate Docker:
   ```bash
   # Replace us-central1 with the region of your Artifact Registry
   gcloud auth configure-docker us-central1-docker.pkg.dev
   ```

4. Pull your custom image from the registry:
   ```bash
   # Use the image name you built and pushed
   docker pull us-central1-docker.pkg.dev/rock-wonder-466311-g6/grchombo-repo/grchombo-dev
   ```

5. Clone your project code:
   ```bash
   git clone https://your-git-repo-url/GRChombo.git
   ```

### Step 2.3: Run a "Cheap" Test Simulation

1. Navigate to your project root:
   ```bash
   cd GRChombo/
   ```

2. Start the Docker container, using the full image name from the registry.

   > **Note**: This command does **not** mount the persistent data disk. For this test run, the simulation will write a small amount of output data to a `simulation_output` directory inside your project folder. Do not change `output_path` to `/output/...` at this stage.

   ```bash
   docker run -v $(pwd):/my_project -it us-central1-docker.pkg.dev/rock-wonder-466311-g6/grchombo-repo/grchombo-dev
   ```

3. cd /my_project/Examples/Wormhole_MT/

4. Compile the code:
   ```bash
   make
   ```

5. Run the simulation with a test parameter file:
   ```bash
   mpirun -np 2 --allow-run-as-root --oversubscribe ./Main_Wormhole_collapse3d_ch.Linux.64.mpicxx.gfortran.OPT.MPI.OPENMPCC.ex params_cheap.txt
   ```
   This should complete quickly and generate a small amount of data.

Phase 3: Adding a Persistent Disk for Simulation Data

For production runs, you need a large, dedicated disk to store your simulation output. This keeps your data separate from the OS and prevents the boot disk from filling up.
Step 3.1: Create and Attach the Data Disk

    Stop your VM instance. You cannot attach a new disk while the VM is running.

    Navigate to Compute Engine > Disks and click CREATE DISK.

    Configure the new disk:

        Name: grchombo-data-disk-01

        Size: Choose a large size suitable for your output (e.g., 500 GB or 1 TB).

        Zone: CRITICAL: Select the exact same zone as your VM instance.

    Click Create.

    Go back to the VM instances page, click Edit on your VM, and under Additional disks, attach the grchombo-data-disk-01 you just created.

    Save the changes and Start your VM again.

### Step 3.2: Format and Mount the Disk on the VM

Once the VM has restarted, you must prepare the new disk for use.

1. **SSH into your VM**.

2. **Verify the disk is visible**. The new disk will likely appear as `/dev/sdb`:
   ```bash
   lsblk
   ```

3. **Format the disk**. This creates a filesystem:
   ```bash
   sudo mkfs.ext4 -m 0 -E lazy_itable_init=0,lazy_journal_init=0,discard /dev/sdb
   ```
   ⚠️ **Warning**: This erases any existing data on the new disk.

4. **Create a mount point**. This is the directory where the disk's contents will appear:
   ```bash
   sudo mkdir -p /mnt/data
   ```

5. **Mount the disk and set permissions**:
   ```bash
   sudo mount /dev/sdb /mnt/data
   sudo chmod 777 /mnt/data
   ```

6. **(Recommended) Configure automatic mounting**. To ensure the disk is mounted automatically every time the VM boots:
   
   a. Get the unique ID (UUID) of the disk:
   ```bash
   sudo blkid /dev/sdb
   ```
   
   b. Copy the UUID value from the output, then add it to the fstab file:
   ```bash
   # Replace YOUR_DISK_UUID with the actual UUID from the previous command
   echo "UUID=YOUR_DISK_UUID /mnt/data ext4 discard,defaults,nofail 0 2" | sudo tee -a /etc/fstab
   ```

Your large data disk is now ready! 🎉

## Phase 4: Production Run with Data Disk

With your data disk prepared, you can now proceed to the final production run. When you run your Docker container, you will map this data directory as a second volume and configure your simulation to write output there:

```bash
docker run -v $(pwd):/my_project -v /mnt/data:/output -it us-central1-docker.pkg.dev/rock-wonder-466311-g6/grchombo-repo/grchombo-dev
```

To ensure all simulation data is written to the persistent disk, you must update your `params.txt` file.

1.  **Open your parameter file**, for example, `Examples/Wormhole_MT/params.txt`.

2.  **Find the `output_path` parameter**. It will look like this:
    ```
    # location / naming of output files
    #output_path = "/home/nik/GRChombo_runs/Wormhole_Collapse"
    output_path = "simulation_output/"
    ```

3.  **Change it to point to the `/output` directory** inside the container. We recommend creating a subdirectory for each run:
    ```
    # location / naming of output files
    #output_path = "/home/nik/GRChombo_runs/Wormhole_Collapse"
    output_path = "/output/wormhole_run_01/"
    ```

Now, when you run the simulation, all HDF5 data, log files, and other outputs will be saved to `/mnt/data/wormhole_run_01` on your VM, which is your persistent data disk.

### Step 4.2: Verifying the Output on the VM

Once the simulation is running inside the container, you can monitor its progress and check the output data from a **separate SSH terminal connected to your VM** (not the Docker container terminal).

1.  **Navigate to your data disk's mount point**:
    ```bash
    cd /mnt/data
    ```

2.  **List the contents**. After a minute, you should see the directory created by the simulation:
    ```bash
    ls -l
    ```
    The output should contain your run directory, e.g., `wormhole_run_01`.

3.  **Check for data files**. The main scientific data is saved in the `hdf5` subdirectory:
    ```bash
    # Replace wormhole_run_01 with your actual output directory name
    ls -l /mnt/data/wormhole_run_01/hdf5/
    ```
    You will see files like `Wormhole_..._.3d.hdf5` appear here as the simulation progresses.

4.  **Watch the live log file**. This is the best way to see the simulation's status in real-time:
    ```bash
    # Replace wormhole_run_01 with your actual output directory name
    tail -f /mnt/data/wormhole_run_01/pout/pout.0
    ```
    This will show you the current timestep and simulation time. Press `Ctrl+C` to stop watching.

## Phase 5: Troubleshooting

### Problem: Output data does not appear in `/mnt/data`

You may encounter a rare but serious issue where the Docker volume mount fails silently.

**Symptom**: You have followed all the steps, set `output_path` correctly, and started the simulation. When you run `ls -l /output` **inside the container**, you can see your data directory (e.g., `wormhole_run_01`). However, when you run `ls -l /mnt/data` **on your VM**, the directory is missing.

This means the link between the container's `/output` folder and the VM's `/mnt/data` folder is broken.

**Step 1: Confirm the Diagnosis**

1.  From **inside the Docker container** (`root@...` prompt), try to create a test file:
    ```bash
    touch /output/test_file.txt
    ```
2.  From your **VM terminal** (`nikita_dash_sh1rokov@...` prompt), check if the file appeared:
    ```bash
    ls -l /mnt/data
    ```
If `test_file.txt` is NOT visible, the volume mount is broken.

**Step 2: Restart the Docker Service**

The most reliable way to fix this is to restart the Docker service on your VM. This will clear any corrupt state.

1.  From your **VM terminal**, stop your current container by restarting Docker:
    ```bash
    sudo systemctl restart docker
    ```

2.  Wait 15-30 seconds for the service to fully restart.

**Step 3: Start a Fresh Container**

Start a new container using the full, correct command which includes the data disk volume mount:
```bash
# Make sure you are in your GRChombo directory on the VM
cd ~/GRChombo
docker run -v $(pwd):/my_project -v /mnt/data:/output -it us-central1-docker.pkg.dev/rock-wonder-466311-g6/grchombo-repo/grchombo-dev
```

After starting the new container and running your simulation, the output data should now appear correctly in `/mnt/data` on your VM.