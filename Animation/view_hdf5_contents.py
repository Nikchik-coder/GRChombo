import h5py
import numpy as np
import argparse
import os

def print_hdf5_structure(file_path):
    """
    Opens a GRChombo HDF5 file and prints its structure, including
    global attributes, available variables, and a tree of its contents.
    This version is updated to read variables from the root attributes.

    Args:
        file_path (str): The path to the HDF5 file.
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        return

    print("=" * 70)
    print(f"Inspecting HDF5 file: {os.path.basename(file_path)}")
    print("=" * 70)

    with h5py.File(file_path, 'r') as f:
        # --- 1. Print Global Attributes ---
        print("\n[+] Global Attributes:")
        if not f.attrs.keys():
            print("    No global attributes found.")
        else:
            for key, value in f.attrs.items():
                # Try to decode byte strings for cleaner printing
                if isinstance(value, bytes):
                    value = value.decode('utf-8', errors='ignore')
                print(f"    - {key}: {value}")

        # --- 2. Print Available Variables (Updated Logic) ---
        print("\n[+] Available Plot Variables:")
        
        # Find all attributes that look like 'component_X'
        comp_vars = {}
        for key, value in f.attrs.items():
            if key.startswith('component_'):
                try:
                    # Extract the number from 'component_0' -> 0
                    comp_num = int(key.split('_')[1])
                    # Store the decoded variable name
                    comp_vars[comp_num] = value.decode('utf-8')
                except (ValueError, IndexError):
                    # Ignore malformed component keys
                    pass

        if not comp_vars:
            print("    Could not find any 'component_X' attributes in the file root.")
        else:
            # Sort by component number and print
            for i in sorted(comp_vars.keys()):
                print(f"    - Component {i}: {comp_vars[i]}")
        
        # --- 3. Print the full file structure ---
        print("\n[+] Full File Structure Tree:")
        
        def print_item(name, obj):
            indent = '    ' * name.count('/')
            if isinstance(obj, h5py.Dataset):
                # Shorten the dtype output for readability
                dtype_str = str(obj.dtype)
                if len(dtype_str) > 30:
                    dtype_str = "structured"
                print(f"{indent} L-- Dataset: {os.path.basename(name)} (Shape: {obj.shape}, Dtype: {dtype_str})")
            elif isinstance(obj, h5py.Group):
                print(f"{indent} +-- Group: {os.path.basename(name)}")
        
        f.visititems(print_item)

    print("\n" + "=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Inspect the contents of a GRChombo HDF5 plot file."
    )
    parser.add_argument(
        "file_path",
        type=str,
        help="The full path to the HDF5 file (e.g., 'output/hdf5/Wormhole_p_000000.3d.hdf5')."
    )

    args = parser.parse_args()
    print_hdf5_structure(args.file_path)