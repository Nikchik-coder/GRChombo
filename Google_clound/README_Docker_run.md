# Running GRChombo with Docker on Google Cloud

## Phase 1: Pre-flight Check (One-Time Setup)

Before you begin, ensure you have completed the following one-time setup tasks:

1. **Custom Docker Image Built**: You have created a modern, optimized Docker image (e.g., `grchombo-optimized:v1.2`).

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
   docker pull us-central1-docker.pkg.dev/rock-wonder-466311-g6/grchombo-repo/grchombo-optimized:v1.2
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

2. Start the Docker container, using the full image name from the registry:
   ```bash
   docker run -v $(pwd):/my_project -it us-central1-docker.pkg.dev/rock-wonder-466311-g6/grchombo-repo/grchombo-optimized:v1.2
   ```
   

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
docker run -v $(pwd):/my_project -v /mnt/data:/output -it us-central1-docker.pkg.dev/rock-wonder-466311-g6/grchombo-repo/grchombo-optimized:v1.2
```

In your `params.txt` file, set the output path to `/output/your_run_name/` to ensure all simulation data is written to the persistent disk.