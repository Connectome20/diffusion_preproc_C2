# Diffusion MRI Pre-processing Pipeline

This repository contains a comprehensive pipeline for preprocessing diffusion MRI data. 

<img width="771" alt="image" src="https://github.com/user-attachments/assets/de90d5e8-03b0-4e97-b7bc-ef2e6863b328">


The instructions include setting up the environment, processing the data, and generating the final outputs.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
  - [1. Configure Environment Variables](#1-configure-environment-variables)
  - [2. Set Up Python Environment](#2-set-up-python-environment)
- [Running the Pre-processing GUI](#running-the-pre-processing-gui)
- [Usage Instructions](#usage-instructions)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## Prerequisites

- **Access to the cluster** (via NoMachine or VNC)
- **Freesurfer** version 7.4.1 installed 
- **MRtrix3** version 3.0.3 installed
- **Miniforge3** for managing Python environments
- Necessary permissions to edit files and install packages

## Setup Instructions

### 1. Configure Environment Variables

Open a terminal on the cluster and edit your `~/.bashrc` file:

```bash
gedit ~/.bashrc

#Add the following lines to include the necessary toolboxes:
export PATH="/autofs/cluster/pubsw/2/pubsw/Linux2-2.3-x86_64/packages/mrtrix/3.0.3/bin:$PATH"
export FREESURFER_HOME="/usr/local/freesurfer/7.4.1"
export FSFAST_HOME="/usr/local/freesurfer/7.4.1/fsfast"
export SUBJECTS_DIR="/usr/local/freesurfer/7.4.1/subjects"
export MNI_DIR="/usr/local/freesurfer/7.4.1/mni"
source $FREESURFER_HOME/SetUpFreeSurfer.sh

```
### 2. Set Up Python Environment
In the terminal, execute the following commands to set up a Python environment:
```bash
# Download the latest Miniforge installer for Linux (64-bit)
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh

# Make the installer executable
chmod +x Miniforge3-Linux-x86_64.sh

# Run the installer (accept the agreement and choose a directory other than the home directory)
./Miniforge3-Linux-x86_64.sh

# Initialize conda
{your_chosen_directory}/conda init

# Install necessary Python packages
pip install requirement.txt
```
---
## Running the Pre-processing GUI
Navigate to the pre-processing code directory and run the GUI:
```bash
cd /autofs/cluster/connectome2/Bay8_C2/bids/code/preprocessing_dwi
python run.py
```
---
## Usage instructions

Input Subject Id, C2 Path, Dicom Source

Provide the path obtained from the findsession command in the Dicom Source field.
Ensure there are no extra spaces or line breaks.

Execute Processing Steps:

Click through the processing steps in order:
- **Execute dcm2bids**
- **Export Diffusion Parameters** diffusionTime, pulseWidth, and phaseEncoding files will be exported along with bvecs and bvals
- **Concatenate DWI Data from entries** (in the order of the wedges)
- **Gibbs Ringing Removal**
- **TopUp Correction** (approx. 2 hours)
- **Generate WM/Brain Masks**
- **Eddy Current Correction** (approx. 6 hours)
- **Execute GNC DWI** (gradient non-linearity correction on C1 or C2 scanner)
- **Combined Eddy GNC Interpolation** (approx. 3 hours)
- **Generate Noise Map from MP-PCA** (the output file will be necessary for SANDI diffusion model-fitting)
- **Write Output to derivative/processed_dwi folder**

**Additional Notes**

The GUI provides fields to input necessary paths and options.
Ensure all paths are correct and accessible.
Monitor the status messages for progress and any potential errors.

---
## License
This project is licensed under the MIT License - see the LICENSE file for details.

---
## Acknowledgements
Thanks to the development teams of Freesurfer, MRtrix3, and Miniforge3.
Special appreciation to the contributors who have made this pipeline possible.





