# Running GRChombo with Docker on Google Cloud

This guide provides a complete workflow for running GRChombo simulations on Google Cloud Platform, from initial setup to production runs.

## Phase 1: One-Time Cloud Setup

Complete these steps once per Google Cloud project.

1.  **Create a Docker Repository:** Go to **Artifact Registry** and create a Docker repository to store your custom GRChombo images.
2.  **Build and Push Your Image:** Build your optimized `grchombo-dev` Docker image and push it to the repository you just created.
3.  **Create a Storage Bucket:** Go to **Cloud Storage** and create a bucket. This is for long-term archival of simulation data.

## Phase 2: VM and Environment Preparation

Complete these steps once for each new VM instance.

1.  **Create a VM Instance:**
    -   Go to **Compute Engine > VM Instances** and click **CREATE INSTANCE**.
    -   **Name:** `grchombo-node`
    -   **Machine type:** Choose a machine appropriate for your needs. `e2-medium` is good for cheap tests.
    -   **Access scopes:** Set to "Allow full access to all Cloud APIs".

2.  **SSH into the VM.**

3.  **Install Essential Tools:**
    ```bash
    sudo apt-get update
    sudo apt-get install -y docker.io git tmux
    ```

4.  **Configure Docker Permissions:**
    -   Add your user to the `docker` group to run Docker commands without `sudo`.
        ```bash
        sudo usermod -aG docker ${USER}
        ```
    -   **CRITICAL:** Refresh your session for the new group to take effect. The easiest way is to **log out and log back into the VM**.

5.  **Authenticate Docker and Clone Project:**
    -   Once reconnected, authenticate `gcloud` with Docker.
        ```bash
        # Replace us-central1 with the region of your Artifact Registry
        gcloud auth configure-docker us-central1-docker.pkg.dev
        ```
    -   Pull your custom image from the registry.
        ```bash
        docker pull us-central1-docker.pkg.dev/rock-wonder-466311-g6/grchombo-repo/grchombo-dev
        ```
    -   Clone your GRChombo project from your Git repository.
        ```bash
        git clone https://your-git-repo-url/GRChombo.git
        git clone https://github.com/Nikchik-coder/GRChombo.git
        ```

## Phase 3: The Core Simulation Workflow

This is the standard process you will follow for every simulation run.

**Step 1: Start a Persistent Session**

To prevent your simulation from being terminated when you disconnect, **always** start it inside a `tmux` session.

```bash
# From your VM terminal, start and name the session
    tmux new -s grchombo_run
```
You are now inside the protected `tmux` session. All subsequent commands are run here.

**Step 2: Start the Docker Container**

Navigate to your project directory and start the container.

```bash
cd GRChombo/
```

Choose **one** of the following commands:

-   **For a quick test** (output is discarded when the container stops):
    > Note: `--shm-size=2g` is important for MPI. It gives the container enough shared memory for the processes to communicate efficiently.
    ```bash
    docker run --shm-size=2g -v $(pwd):/my_project -it us-central1-docker.pkg.dev/rock-wonder-466311-g6/grchombo-repo/grchombo-dev
    ```
-   **For a production run** (output is saved to your persistent disk):
    > First, make sure you have created and mounted a persistent disk at `/mnt/data`. (See Phase 4).
    ```bash
    docker run --shm-size=2g -v $(pwd):/my_project -v /mnt/data:/output -it us-central1-docker.pkg.dev/rock-wonder-466311-g6/grchombo-repo/grchombo-dev
    ```

**Step 3: Compile and Configure**

You are now inside the Docker container (`root@...` prompt).

1.  **Navigate to the example directory:**
    ```bash
    cd /my_project/Examples/Wormhole_MT/
    ```
2.  **Compile the code:**
    ```bash
    make all
    ```
3.  **Set the output path:**
    -   Install a text editor: `apt-get update && apt-get install -y nano`
    -   Open the parameter file: `nano params.txt`
    -   Find `output_path` and set it correctly.
        -   For a test run, you can leave it as `"simulation_output/"`.
        -   For a production run, it **must** point to the mounted volume: `output_path = "/output/my_run_name/"`
    -   Save the file (`Ctrl+X`, `Y`, `Enter`).

**Step 4: Run and Detach**

1.  **Launch the simulation:**
    ```bash
    mpirun -np 8 --allow-run-as-root --oversubscribe ./Main_Wormhole_collapse3d_ch.Linux.64.mpicxx.gfortran.OPT.MPI.OPENMPCC.ex params.txt
    ```

    > **Note on Performance and CPU Configuration:**
    > The performance of your simulation depends heavily on the problem size (i.e., the settings in your `params.txt` file) and how you configure the `mpirun` command to use the VM's CPUs.
    >
    > **Optimizing for your VM's CPUs (e.g., a 60-vCPU machine)**
    >
    > Using `-np 60` on a 60-vCPU machine is **not always the fastest option**. Most cloud VMs use hyper-threading, where 1 physical CPU core is presented as 2 vCPUs. This means a 60-vCPU instance typically has **30 physical cores**. Running too many separate processes can lead to high communication overhead and resource contention.
    >
    > The GRChombo executable is built for **hybrid parallelism (MPI + OpenMP)**. The best performance is often achieved by running **one MPI rank per physical core** and using OpenMP threads to utilize all the vCPUs on that core.
    >
    > Here are configurations to benchmark on a 60-vCPU machine. Run each for 15-20 minutes and see which completes the most timesteps.
    >
    > -   **Option 1: Pure MPI (High Communication)**
    >     One MPI process per vCPU. Simple, but can be slow due to communication overhead.
    >     ```bash
    mpirun -np 60 --allow-run-as-root --oversubscribe ./Main_Wormhole_collapse3d_ch.Linux.64.mpicxx.gfortran.OPT.MPI.OPENMPCC.ex params.txt

    mpirun -np 60 --allow-run-as-root --oversubscribe ./Main_Wormhole_collapse3d_ch.Linux.64.mpicxx.gfortran.OPT.MPI.OPENMPCC.ex params_cheap.txt
    >     ```
    > -   **Option 2: One MPI Rank per Physical Core**
    >     Reduces communication overhead but may leave some CPU resources idle.
    >     ```bash
    mpirun -np 30 --allow-run-as-root --oversubscribe ./Main_Wormhole_collapse3d_ch.Linux.64.mpicxx.gfortran.OPT.MPI.OPENMPCC.ex params.txt

    mpirun -np 30 --allow-run-as-root --oversubscribe ./Main_Wormhole_collapse3d_ch.Linux.64.mpicxx.gfortran.OPT.MPI.OPENMPCC.ex params_cheap.txt
    >     ```
    > -   **Option 3: Hybrid MPI + OpenMP (Recommended for Benchmarking)**
    >     Often the best balance. One MPI rank per physical core, with 2 OpenMP threads each to saturate the vCPUs.
    >     ```bash
    >     # First, set the number of threads for OpenMP
    >     export OMP_NUM_THREADS=2
    >
    >     # Then run with 30 MPI ranks (one for each physical core)
    mpirun -np 30 --allow-run-as-root --oversubscribe ./Main_Wormhole_collapse3d_ch.Linux.64.mpicxx.gfortran.OPT.MPI.OPENMPCC.ex params.txt
    >     ```

2.  **Detach from the session:**
    Press **`Ctrl+b` then `d`**. You can now safely close your SSH window.

**Step 5: Monitor the Simulation**

While the simulation runs inside `tmux`, you can check its progress from a *separate* SSH window without interrupting anything.

1.  **Open a new SSH connection** to your VM.

2.  **Navigate to your data directory.** This is where the simulation is writing its output files.
    ```bash
    cd /mnt/data
    ```

3.  **Find your simulation's output folder.** You should see the directory you specified in your `params.txt` file.
    ```bash
    ls -l
    ```

4.  **Watch the live log file.** The best way to see the simulation's status in real-time is to use `tail -f` on the main output file. This will continuously print new lines as they are written to the log.
    ```bash
    # Replace my_run_name with your actual output directory name
    tail -f my_run_name/pout/pout.0
    ```
    You will see the current timestep and simulation time. Press `Ctrl+C` in this second window to stop watching the log (this will not stop the simulation itself).

## Phase 4: Advanced Topics & Troubleshooting

**First-Time Setup for Persistent Data Disk**

For production runs, you need a dedicated disk for your data.

1.  **Create and Attach Disk:**
    -   Stop your VM instance.
    -   In the Google Cloud Console, go to **Compute Engine > Disks** and create a new persistent disk. **Ensure it is in the same zone as your VM.**
    -   Edit your VM instance and attach the newly created disk.
    -   Start your VM again.
2.  **Format and Mount Disk (on VM):**
    -   SSH into your VM.
    -   Find your data disk's name with `lsblk`. It will be the large disk that is **not** mounted (e.g., `sda`, `sdb`). **Identify the correct device name for your data disk and use it in the following steps.** In the example `lsblk` output below, the OS is on `/dev/sdb` and the unformatted 100G data disk is `/dev/sda`.
        ```bash
        $ lsblk
        NAME    MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
        sda       8:0    0  100G  0 disk 
        sdb       8:16   0   10G  0 disk 
        ├─sdb1    8:17   0  9.9G  0 part /
        ├─sdb14   8:30   0    3M  0 part 
        └─sdb15   8:31   0  124M  0 part /boot/efi
        ```
    -   Format your data disk. **Use the device name you identified above.**
        ```bash
        # Replace /dev/sda with your data disk's name
        sudo mkfs.ext4 /dev/sda
        ```
    -   Create a mount point: `sudo mkdir -p /mnt/data`
    -   Mount it temporarily and set permissions:
        ```bash
        # Replace /dev/sda with your data disk's name
        sudo mount /dev/sda /mnt/data && sudo chmod 777 /mnt/data
        ```

    > **IMPORTANT:** This `mount` command is temporary and will not survive a VM reboot. If you start a simulation without making the mount permanent, all data will be written to the small primary disk of the VM, which can quickly fill up and cause the simulation and the VM to crash.

3.  **Verify and Make the Mount Permanent**
    -   **Verify the Mount:**
        Before proceeding, verify that the disk is correctly mounted. Run `df -h`. The output should include a new line for your disk, similar to this:
        ```bash
        # Your output will now look something like this:
        Filesystem      Size  Used Avail Use% Mounted on
        ... (all the other lines) ...
        /dev/sda        100G  60M   95G   1% /mnt/data
        ```
        If you do not see your disk (`/dev/sda` in this example) listed and mounted on `/mnt/data`, something is wrong. Do not proceed until it is correctly mounted.
    -   **Make the Mount Permanent:**
        To ensure the disk is automatically mounted every time the VM starts, you must add it to the `/etc/fstab` file. This is the recommended way to do it:
        ```bash
        # This command finds the unique ID of your disk and adds it to the fstab file
        # Make sure to replace /dev/sda with your data disk's name if it is different
        echo "UUID=$(sudo blkid -s UUID -o value /dev/sda) /mnt/data ext4 defaults,nofail 0 2" | sudo tee -a /etc/fstab
        ```
        This command makes the mount permanent and robust against reboots.

**How to Monitor or Stop a Running Simulation**

1.  **Reconnect to the Session:**
    -   SSH back into your VM.
    -   Attach to your running `tmux` session: `tmux attach -t grchombo_run`
2.  **To Monitor:** You can now see the live output. Or, from another VM terminal, you can watch the log file directly: `tail -f /mnt/data/my_run_name/pout/pout.0`
3.  **To Stop:** From inside the `tmux` session, press `Ctrl+C`.

**Troubleshooting Common Issues**

-   **Problem:** The simulation is running, but my persistent disk seems empty and the main VM disk is filling up.
    -   **Cause:** The `mount` command for your persistent disk was temporary, failed, or was undone by a reboot. Your simulation is writing all its data to the small 10GB root disk (`/dev/sda1`) instead of your large persistent disk. When you create a directory like `sudo mkdir -p /mnt/data`, it is just a normal, empty folder on your root filesystem. If the persistent disk is not mounted over it, Docker will happily use this folder, filling up the root disk.
    -   **Solution: How to Fix an Incorrect Mount**
        If you let the simulation continue, your root disk will become 100% full, and the simulation (and possibly the entire VM) will crash.
        1.  **Stop the Running Simulation:**
            Find the container ID and then stop it to prevent it from writing more data.
            ```bash
            # Find the container ID
            docker ps

            # Stop the container using its ID
            docker stop <your_container_id>
            ```
        2.  **Mount the Disk Correctly:**
            Properly mount the persistent disk to the mount point, then verify the mount was successful with `df -h`.
            ```bash
            # Replace /dev/sda with your data disk's name
            sudo mount /dev/sda /mnt/data
            ```
        3.  **Clean Up the Root Disk (Optional but Recommended):**
            The data written to the root disk is now "hidden" under the mount point, but it's still taking up space. To reclaim it:
            ```bash
            # Unmount the big disk temporarily
            sudo umount /mnt/data

            # !! DANGER !! This will permanently delete the simulation data written so far.
            # Make sure you are in the right directory before running!
            sudo rm -rf /mnt/data/*

            # Re-mount the big disk
            # Replace /dev/sda with your data disk's name
            sudo mount /dev/sda /mnt/data
            ```
        4.  **Make the Mount Permanent:**
            Follow the instructions in **Step 3** above to add the disk to `/etc/fstab` to prevent this from happening again.
        5.  **Restart your simulation.** All output will now go to the correct disk.

-   **Problem:** `docker pull` fails with `permission denied`.
    -   **Cause:** Your shell session hasn't recognized that you were added to the `docker` group.
    -   **Solution:** Log out of the VM and log back in.