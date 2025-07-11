#!/usr/bin/env python3
"""
Quick Demo: Wormhole Embedding Diagram Visualization

This script demonstrates how to create embedding diagrams for wormhole collapse
showing the classic Einstein-Rosen bridge "funnel" shape.
"""

import sys
import os

# Add current directory to path to import our embedding module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from wormhole_embedding_diagram import WormholeEmbeddingVisualizer
except ImportError:
    print("Error: Could not import WormholeEmbeddingVisualizer")
    print("Please ensure wormhole_embedding_diagram.py is in the same directory")
    sys.exit(1)

def quick_demo():
    """Run a quick demo of the embedding visualization"""
    
    print("🌀 Wormhole Embedding Diagram Demo")
    print("=" * 40)
    
    # Create the visualizer
    visualizer = WormholeEmbeddingVisualizer()
    
    print("\n📊 Creating embedding diagrams...")
    
    # Analyze a single timestep (creates 3D and cross-section plots)
    print("1. Analyzing single timestep...")
    visualizer.analyze_single_timestep(show_plots=False)
    
    # Create animation (may take a few minutes depending on data size)
    print("\n2. Creating animation (this may take a few minutes)...")
    visualizer.create_animation(max_frames=20, duration=0.3)  # Limit to 20 frames for demo
    
    print("\n✅ Demo completed!")
    print(f"Check the '{visualizer.output_dir}' directory for:")
    print("  - Individual 3D embedding diagrams")
    print("  - Cross-section plots") 
    print("  - Animated GIF showing throat collapse")
    print("  - Throat evolution analysis")
    
    return visualizer

def create_single_embedding():
    """Create just a single embedding diagram"""
    
    print("🌀 Creating Single Wormhole Embedding Diagram")
    print("=" * 45)
    
    visualizer = WormholeEmbeddingVisualizer()
    visualizer.analyze_single_timestep(show_plots=True)  # Show plots interactively
    
    print("✅ Single embedding diagram created!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Demo wormhole embedding visualization")
    parser.add_argument("--mode", choices=["demo", "single"], default="demo",
                       help="Run full demo or just create single diagram")
    
    args = parser.parse_args()
    
    if args.mode == "demo":
        quick_demo()
    else:
        create_single_embedding() 