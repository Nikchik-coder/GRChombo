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

3. **(CRITICAL) Configure Docker Permissions to Avoid Auth Errors**

   By default, running `docker` commands requires `sudo`. However, if you run `sudo docker pull`, it will fail with an `Unauthenticated` error because the `gcloud auth` command (in the next step) configures credentials for your local user (`${USER}`), not for the `root` user that `sudo` uses.

   To fix this, add your user to the `docker` group. This allows you to run `docker` without `sudo`.

   ```bash
   sudo usermod -aG docker ${USER}
   ```

4. **(CRITICAL) Refresh Your Shell Session**

   The `usermod` command added you to the `docker` group, but this change **will not take effect in your current session**. You must start a new shell to avoid the `permission denied` error when running `docker`.

   **Option A (Recommended): Log Out and Log Back In**
   This is the simplest and most reliable method. Close your current SSH connection, then reconnect to the VM.

   **Option B (Quicker): Use `newgrp`**
   If you do not want to log out, you can run the following command. This will start a *new sub-shell* with the correct group permissions.
   ```bash
   newgrp docker
   ```
   > **Note:** If you use this method, you must run all subsequent commands in the new shell that appears.

5. **Authenticate Docker (In Your New Shell)**
   Now that your user permissions are correct, you can configure Docker to access the Artifact Registry.
   ```bash
   # Replace us-central1 with the region of your Artifact Registry
   gcloud auth configure-docker us-central1-docker.pkg.dev
   ```

6. **Pull Your Custom Image**
   Pull the image from the registry. Note that `sudo` is not required.
   ```bash
   # Use the image name you built and pushed
   docker pull us-central1-docker.pkg.dev/rock-wonder-466311-g6/grchombo-repo/grchombo-dev
   ```

7. **Clone Your Project Code**
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
   make all 
   ```

5. Run the simulation with a test parameter file:
   ```bash
   mpirun -np 2 --allow-run-as-root --oversubscribe ./Main_Wormhole_collapse3d_ch.Linux.64.mpicxx.gfortran.OPT.MPI.OPENMPCC.ex params_cheap.txt

   mpirun -np 8 --allow-run-as-root --oversubscribe ./Main_Wormhole_collapse3d_ch.Linux.64.mpicxx.gfortran.OPT.MPI.OPENMPCC.ex params.txt

   mpirun -np 8 --allow-run-as-root --oversubscribe ./Main_Wormhole_collapse3d_ch.Linux.64.mpicxx.gfortran.OPT.MPI.OPENMPCC.ex params_cheap.txt

   docker run --shm-size=2g -it -v /mnt/data/wormhole_run_medium:/my_project us-central1-docker.pkg.dev/rock-wonder-466311-g6/grchombo-repo/grchombo-dev
   ```
   This should complete quickly and generate a small amount of data.

Phase 3: Adding a Persistent Disk for Simulation Data

For production runs, you need a large, dedicated disk to store your simulation output. This keeps your data separate from the OS and prevents the boot disk from filling up.
### Step 3.1: Create and Attach the Data Disk

1.  **Stop your VM instance**. You cannot attach a new disk while the VM is running.

2.  Navigate to **Compute Engine > Disks** and click **CREATE DISK**.

3.  Configure the new disk:
    -   **Name**: `grchombo-data-disk-01`
    -   **Size**: Choose a large size suitable for your output (e.g., 500 GB or 1 TB).
    -   **Zone**: **CRITICAL**: Select the exact same zone as your VM instance.

4.  Click **Create**.

5.  Go back to the VM instances page, click **Edit** on your (stopped) VM, and under **Additional disks**, attach the `grchombo-data-disk-01` you just created.

    > **Troubleshooting Tip:** If you do not see your disk in the list of available disks to attach, try these steps:
    > 1.  **Refresh the page.** The Google Cloud console can sometimes be slow to update.
    > 2.  **Check the "Disks" page.** Make sure the "In use by" column for your disk is empty. A disk can only be attached to one VM at a time.
    > 3.  **Verify the Zone again.** It is critical that the disk and the VM are in the exact same zone (e.g., `us-central1-a`).

6.  Save the changes and **Start** your VM again.

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

To ensure all simulation data is written to the persistent disk, you must update your `params.txt` file **inside the container**.

1.  **Navigate to your example directory** (if you're not already there):
    ```bash
    cd /my_project/Examples/Wormhole_MT/
    ```

2.  **Install a text editor**. The base Docker image is minimal and may not include one. You can install `nano` with this command:
    ```bash
    apt-get update && apt-get install -y nano
    ```

3.  **Open your parameter file** with `nano`:
    ```bash
    nano params.txt
    ```

4.  **Find the `output_path` parameter**. It will look like this:
    ```
    # location / naming of output files
    #output_path = "/home/nik/GRChombo_runs/Wormhole_Collapse"
    output_path = "simulation_output/"
    ```

5.  **Change it to point to the `/output` directory** inside the container. We recommend creating a subdirectory for each run:
    ```
    # location / naming of output files
    #output_path = "/home/nik/GRChombo_runs/Wormhole_Collapse"
    output_path = "/output/wormhole_run_01/"
    ```
    Once edited, save the file in `nano` by pressing `Ctrl+X`, then `Y`, then `Enter`.

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

## Phase 5: Debugging Common Issues

This section covers the most common problems encountered when running simulations.

### Issue: Simulation Data Does Not Appear in `/mnt/data`

This is the most frequent problem. You start a simulation, but the output directory never appears on your persistent disk (`/mnt/data` on the VM). There are two likely causes.

#### Cause A: Incorrect `output_path` in Parameter File

The simulation writes data to the path specified by the `output_path` parameter in your `params.txt` or `params_cheap.txt` file. For data to be saved to the persistent disk, this path **must** be an absolute path starting with `/output/`.

**Symptom:**
- The simulation runs without error.
- No new directory appears in `/mnt/data` on the VM.
- If you `ls` the project directory *inside the container* (e.g., `/my_project/Examples/Wormhole_MT/`), you will find a `simulation_output` directory there.

**Solution:**

1.  **Stop the simulation** inside the container (`Ctrl+C`).
2.  **Edit your parameter file** (e.g., `nano params_cheap.txt`).
3.  **Change the `output_path`** to an absolute path.

    - **Incorrect (relative path):**
      ```
      output_path = "simulation_output/"
      ```
    - **Correct (absolute path):**
      ```
      output_path = "/output/my_cheap_run/"
      ```
4.  **Save the file and restart the simulation.** The data will now be written to `/mnt/data/my_cheap_run/` on your VM.

---

#### Cause B: Silent Docker Volume Mount Failure

You may encounter a rare but serious issue where the Docker volume mount (`-v /mnt/data:/output`) fails silently.

**Symptom**:
- You have verified that `output_path` is correct (e.g., `/output/my_run/`).
- When you run `ls -l /output` **inside the container**, you can see your data directory.
- However, when you run `ls -l /mnt/data` **on your VM**, the directory is missing.

This means the link between the container's `/output` folder and the VM's `/mnt/data` folder is broken.

**Solution: Restart the Docker Service**

The most reliable way to fix this is to restart the Docker service on your VM, which will clear any corrupt state.

1.  From your **VM terminal**, stop your current container by restarting Docker:
    ```bash
    sudo systemctl restart docker
    ```

2.  Wait 15-30 seconds for the service to fully restart.

3.  **Start a Fresh Container**. Use the full, correct command which includes the data disk volume mount:
    ```bash
    # Make sure you are in your GRChombo directory on the VM
    cd ~/GRChombo
    docker run -v $(pwd):/my_project -v /mnt/data:/output -it us-central1-docker.pkg.dev/rock-wonder-466311-g6/grchombo-repo/grchombo-dev
    ```

After starting the new container and running your simulation, the output data should now appear correctly in `/mnt/data` on your VM.

---
### Problem: `docker pull` fails with `Unauthenticated` error

**Symptom**: When you run `docker pull`, you get an error like:
`denied: Unauthenticated request. Unauthenticated requests do not have permission "artifactregistry.repositories.downloadArtifacts"`

**Cause**: This usually happens if you run the command as `sudo docker pull`. The `gcloud auth` command configures credentials for your user, but `sudo` runs the command as the `root` user, which doesn't have the required permissions.

**Solution**:
1.  Make sure you have added your user to the `docker` group as described in **Phase 2, Step 2.2**.
    ```bash
    sudo usermod -aG docker ${USER}
    ```
2.  **Log out of the VM and log back in** for the group change to take effect.
3.  Run the `docker pull` command again **without `sudo`**.