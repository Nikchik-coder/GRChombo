# Plotting Simulation Data on Google Cloud

This guide explains how to generate plots from your simulation data on your Google Cloud VM and how to copy them to your local computer for viewing.

This entire process is done on the VM, not inside the Docker container.

## Step 1: Set Up the Python Plotting Environment

You only need to perform this setup once on your VM.

1.  **SSH into your VM instance**.

2.  **Navigate to the `Animation` directory** within your project:
    ```bash
    cd ~/GRChombo/Animation
    ```

3.  **Install the necessary system packages** for Python and virtual environments:
    ```bash
    sudo apt-get update
    sudo apt-get install -y python3-pip python3-venv
    ```

4.  **Create a dedicated Python virtual environment**. This prevents conflicts with system packages.
    ```bash
    python3 -m venv venv
    ```

5.  **Activate the virtual environment**:
    ```bash
    source venv/bin/activate
    ```
    Your command prompt will change to show `(venv)` at the beginning. This indicates the virtual environment is active.

6.  **Install the required Python libraries** using the `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```

Your VM is now fully prepared for plotting.

## Step 2: Generate a Plot

With the environment set up, you can now run any of the Python plotting scripts.

1.  **Ensure you are in the `Animation` directory** with the virtual environment still active (you should see `(venv)` in your prompt). If not, reactivate it with `source venv/bin/activate`.

2.  **Run a plotting script**. As an example, let's use `plot_wormhole.py`. You must provide the path to your simulation data on the persistent disk (`/mnt/data/...`).
    ```bash
    # Replace wormhole_run_01 with the name of your simulation output folder
    python plot_wormhole.py --data_dir /mnt/data/wormhole_run_01/hdf5/
    ```

3.  The script will process the data and save an image file (e.g., `wormhole_slice.png`) into the current directory (`~/GRChombo/Animation`). You can verify its creation with `ls -l`.

## Step 3: Copy the Plot to Your Local Computer

Since the VM does not have a graphical user interface, you must copy the generated image files to your local machine to view them.

1.  **Open a new terminal on your LOCAL computer** (not the VM).

2.  **Use the `gcloud compute scp` command** to securely copy the file. You will need your VM's instance name and zone.
    ```bash
    # Replace with your actual instance name and zone
    gcloud compute scp YOUR_INSTANCE_NAME:~/GRChombo/Animation/wormhole_slice.png . --zone=YOUR_VM_ZONE
    ```
    - `YOUR_INSTANCE_NAME`: e.g., `instance-20250720-085524`
    - `wormhole_slice.png`: The name of the plot file you want to copy.
    - `.`: This final dot means "copy the file to my current local directory".

3.  The image file will now be on your local computer, ready to be viewed. You can repeat this `scp` command for any plots you generate.

### Deactivating the Virtual Environment

When you are finished with plotting, you can deactivate the virtual environment on your VM by simply typing:
```bash
deactivate
``` 