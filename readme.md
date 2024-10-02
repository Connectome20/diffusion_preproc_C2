# Diffusion MRI Pre-processing Pipeline

This repository contains a comprehensive pipeline for pre-processing diffusion MRI data. The pipeline includes setting up the environment, processing the data using various tools, and generating the final outputs.

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
- **Freesurfer** version 7.4.1 installed at `/usr/local/freesurfer/7.4.1`
- **MRtrix3** version 3.0.3 installed
- **Miniforge3** for managing Python environments
- Necessary permissions to edit files and install packages

## Setup Instructions

### 1. Configure Environment Variables

Open a terminal on the cluster and edit your `~/.bashrc` file:

```bash
gedit ~/.bashrc
Add the following lines to include the necessary toolboxes:
export PATH="/autofs/cluster/pubsw/2/pubsw/Linux2-2.3-x86_64/packages/mrtrix/3.0.3/bin:$PATH"
export FREESURFER_HOME="/usr/local/freesurfer/7.4.1"
export FSFAST_HOME="/usr/local/freesurfer/7.4.1/fsfast"
export SUBJECTS_DIR="/usr/local/freesurfer/7.4.1/subjects"
export MNI_DIR="/usr/local/freesurfer/7.4.1/mni"
source $FREESURFER_HOME/SetUpFreeSurfer.sh
### 1. Configure Environment Variables

