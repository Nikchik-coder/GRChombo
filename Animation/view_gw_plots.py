#!/usr/bin/env python3
"""
Simple viewer for gravitational wave analysis plots
"""

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os
import argparse

def view_plot(plot_name):
    """View a specific gravitational wave plot"""
    
    plot_files = {
        'weyl4': 'gw_plots/weyl4_overview.png',
        'strain': 'gw_plots/strain_analysis.png', 
        'imr': 'gw_plots/inspiral_merger_ringdown.png'
    }
    
    if plot_name not in plot_files:
        print(f"Available plots: {list(plot_files.keys())}")
        return
    
    filename = plot_files[plot_name]
    
    if not os.path.exists(filename):
        print(f"Plot file {filename} not found. Run plot_gravitational_waves.py first.")
        return
    
    # Load and display image
    img = mpimg.imread(filename)
    plt.figure(figsize=(12, 8))
    plt.imshow(img)
    plt.axis('off')
    plt.title(f"Gravitational Wave Analysis - {plot_name.upper()}")
    plt.tight_layout()
    plt.show()
    
    print(f"Displaying: {filename}")

def main():
    parser = argparse.ArgumentParser(description='View gravitational wave plots')
    parser.add_argument('plot', choices=['weyl4', 'strain', 'imr', 'all'], 
                       help='Which plot to view')
    
    args = parser.parse_args()
    
    if args.plot == 'all':
        for plot_name in ['weyl4', 'strain', 'imr']:
            view_plot(plot_name)
    else:
        view_plot(args.plot)

if __name__ == "__main__":
    main() 