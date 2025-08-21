# RTIST UI - Modern Textual Interface

## Overview

The new `mtrip-ui` command provides a modern, colorful, and user-friendly Terminal User Interface (TUI) for the RTIST phylogenetic analysis tool using the Textual framework.

## Features

### 🎨 Colorful Design
- Modern TUI with rich colors and emojis
- Intuitive navigation with clear visual feedback
- Professional appearance while remaining fun and engaging

### 📁 Easy File Selection
- Browse filesystem with directory tree widget
- Filter for Newick (.nwk) and text files
- Built-in example file loading

### ⚙️ Parameter Configuration
- User-friendly options for all analysis parameters:
  - Thread count selection (auto-detect or manual)
  - Output file settings
  - Validation options
  - Binary file export

### 📊 Real-time Progress Tracking
- Visual progress bar with ETA
- Detailed analysis log with colored status messages
- Step-by-step progress updates

### 🎯 Results Visualization
- Beautiful display of median triplet trees
- Easy navigation through multiple results
- Option to save results to file

## Installation

The UI requires the Textual framework. Install with:

```bash
pip install textual>=0.50.0
```

## Usage

Launch the UI with:

```bash
mtrip-ui
```

Or run directly:

```bash
python src/mtrip/cli/mtrip_ui.py
```

## Workflow

1. **Welcome Screen**: Introduction and feature overview
2. **Main Menu**: Choose to load files or examples
3. **Parameters**: Configure analysis settings
4. **Analysis**: Watch real-time progress
5. **Results**: View and save findings

## Example Session

```
🧬 RTIST - Phylogenetic Tree Analysis

Welcome to the modern interface for median triplet tree analysis!

Features:
• 🎨 Colorful and intuitive interface
• 📁 Easy file selection  
• ⚙️ Simple parameter configuration
• 📊 Real-time progress tracking
• 🎯 Beautiful results visualization

Press ENTER to begin or Q to quit
```

The interface guides users through each step with clear visual cues and helpful messages, making phylogenetic analysis more accessible to both beginners and experts.

## Benefits

- **Accessibility**: No command-line expertise required
- **Visual Feedback**: Clear progress and status indication  
- **Error Prevention**: Validation and user-friendly error messages
- **Efficiency**: Streamlined workflow reduces setup time
- **Enjoyable**: Modern, colorful design makes analysis more engaging