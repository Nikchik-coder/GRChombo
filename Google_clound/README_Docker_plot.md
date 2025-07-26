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
    python plot_wormhole.py --data_dir /mnt/data/wormhole_run_cheap/hdf5/

    python plot_wormhole.py --data_dir /mnt/data/wormhole_run_medium/hdf5/

    python create_animation.py all

    python plot_wormhole.py --data_dir /mnt/data/wormhole_run_high_res/hdf5/




    ```

3.  The script will process the data and save image files into new directories named `plots_<variable_name>` (e.g., `plots_chi`, `plots_Ham`). You can see the generated images by listing the contents of one of these new directories:
    ```bash
    ls -l plots_chi/
    ```

## Step 3: Copy the Plot to Your Local Computer

Since the VM does not have a graphical user interface, you must copy the generated image files to your local machine to view them.

1.  **Open a new terminal on your LOCAL computer** (not the VM).

2.  **Use the `gcloud compute scp` command** to securely copy the files.

    > **Important**: You must use the full, absolute path to the directory on the VM. The `~` shortcut does not work reliably with `scp` and may cause a "No such file or directory" error.

    To copy an entire folder of plots (e.g., all `chi` plots), use the `--recurse` flag.
    ```bash
    # Replace with your actual instance name, VM username, and zone
    gcloud compute scp --recurse YOUR_INSTANCE_NAME:/home/YOUR_VM_USERNAME/GRChombo/Animation/plots_chi . --zone=YOUR_VM_ZONE
    ```
    - `YOUR_INSTANCE_NAME`: e.g., `instance-20250720-085524`
    - `YOUR_VM_USERNAME`: The username on your VM (e.g., `nikita_dash_sh1rokov`).
    - `plots_chi`: The name of the plot folder you want to copy.
    - `.`: This final dot means "copy the folder to my current local directory".

    For example, a complete, working command would look like this:
    ```bash
    gcloud compute scp --recurse instance-20250726-070656:/home/nikita_dash_sh1rokov/GRChombo/Animation/plots_chi . --zone=us-central1-c

    gcloud compute scp --recurse instance-20250723-185724:/home/nikita_dash_sh1rokov/GRChombo/Animation/GRChombo_animations . --zone=us-central1-c
    ```

3.  A new folder named `plots_chi` will now be on your local computer, containing all the generated images. You can repeat this `scp` command for any other plot directories you want to view.

#### Finding Your Instance Name and Zone

If you don't know your VM's instance name or zone, you can find them easily. On your **local computer's terminal**, run the following command:
```bash
gcloud compute instances list
```
This will display a table of all your VM instances. The `NAME` and `ZONE` columns will contain the information you need for the `scp` command.

### Deactivating the Virtual Environment

When you are finished with plotting, you can deactivate the virtual environment on your VM by simply typing:
```bash
deactivate
```

### Cleaning Up Old Plots

The plotting scripts will automatically overwrite any existing images if you run them again on the same data.

If you are analyzing data from a new simulation and want to clear out all the old plots, you can delete all `plots_*` directories at once. From the `~/GRChombo/Animation` directory on your VM, run:
```bash
rm -rf plots_*
```
This command will remove all directories starting with `plots_`, giving you a clean slate for your next run.

## Step 4: Creating Animations and Advanced Plots

Beyond simple slice plots, the repository contains scripts for creating animations and analyzing specific data like gravitational waves.

### Creating Animations from Slice Plots

After you have generated a set of slice plots (e.g., `plots_chi`), you can combine them into a GIF animation.

1.  **Ensure you are in the `Animation` directory** with the virtual environment active.

2.  **Run the `create_animation.py` script**. You must tell it where to find the `plots_*` directories.
    ```bash
    # The '.' means look for 'plots_*' directories in the current folder
    python create_animation.py all --plots_dir .
    ```
    This will find all `plots_*` directories and create a GIF for each one. The output animations will be saved in a new directory named `GRChombo_animations/run_<timestamp>/`.

### Plotting Gravitational Waves

If your simulation extracted Weyl4 data, you can analyze and plot it.

1.  **Ensure you are in the `Animation` directory** with the virtual environment active.

2.  **Run the `plot_gravitational_waves.py` script**. You must provide the path to your simulation's `data` directory, which contains the `Weyl4_*.dat` files.
    ```bash
    # Replace wormhole_run_01 with your simulation output folder name
    python plot_gravitational_waves.py --data_dir /mnt/data/wormhole_run_01/data
    ```
    This script will create a new directory named `gw_plots/` containing several images of the gravitational wave signal analysis. It will also save processed data (like the calculated strain) into `gw_plots/processed_data/`.