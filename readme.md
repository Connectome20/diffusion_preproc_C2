# Diffusion MRI Pre-processing Pipeline

A fully-featured, step-by-step workflow for preparing diffusion MRI (dMRI) datasets for analysis. The pipeline wraps **dcm2bids**, **MRtrix3**, **FSL** (TopUp & Eddy), **FreeSurfer**, and in-house scripts behind a lightweight Python/Qt GUI.

<p align="center">
  <img width="700" alt="Screenshot of the preprocessing GUI" src="https://github.com/user-attachments/assets/de90d5e8-03b0-4e97-b7bc-ef2e6863b328" />
</p>

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Full Setup](#full-setup)
  - [1. Configure Environment Variables](#1-configure-environment-variables)
  - [2. Create / Activate a Python Environment](#2-create--activate-a-python-environment)
  - [3. Install Python Dependencies](#3-install-python-dependencies)
- [Running the GUI](#running-the-gui)
- [Pipeline Steps](#pipeline-steps)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## Prerequisites

| Component | Recommended version | Notes |
|-----------|--------------------|-------|
| **FreeSurfer** | 7.4.1 | `recon-all` used at the end of the pipeline |
| **MRtrix3** | 3.0.3 | Gibbs & MP-PCA modules |
| **Miniforge** | latest | for managing Conda environments |
| **FSL** | 6.0+ | provides *topup* & *eddy* |
| Access to **cluster** (SSH / NoMachine / VNC) and permission to install software |

> **Tip** Martinos Center users can activate a ready-to-go Conda environment—see [Quick Start](#quick-start).

---

## Quick Start

```bash
# 1) Locate your session (example)
findsession MS_C2_001

# 2) Activate the pre-built Conda environment
source /autofs/space/linen_001/users/Yixin/miniforge3/bin/activate
conda activate /autofs/space/linen_001/users/Yixin/miniforge3/envs/tractseg_env

# 4) Source related tools:
cd /autofs/cluster/connectome2/Bay8_C2/bids/code/preprocessing_dwi
source dwi_proc_env

# 3) Launch the preprocessing GUI 
cd /autofs/cluster/connectome2/Bay8_C2/bids/code/preprocessing_dwi
python main.py
```

Everything you need—GUI plus dependencies—is bundled in that environment, so no further installation is necessary.

---

## Full Setup

### 1. Configure Environment Variables

Append the following to `~/.bashrc` (or `~/.zshrc`) and reload the shell:

```bash
export PATH="/autofs/cluster/pubsw/2/pubsw/Linux2-2.3-x86_64/packages/mrtrix/3.0.3/bin:$PATH"
export FREESURFER_HOME="/usr/local/freesurfer/7.4.1"
export FSFAST_HOME="$FREESURFER_HOME/fsfast"
export SUBJECTS_DIR="$FREESURFER_HOME/subjects"
export MNI_DIR="$FREESURFER_HOME/mni"
source $FREESURFER_HOME/SetUpFreeSurfer.sh

# reload
source ~/.bashrc
```

### 2. Create / Activate a Python Environment

```bash
# Download Miniforge (64-bit Linux)
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
chmod +x Miniforge3-Linux-x86_64.sh
./Miniforge3-Linux-x86_64.sh    # accept license, choose install path

# Initialise Conda once
<miniforge>/bin/conda init
exec "$SHELL"   # restart shell so 'conda' is on PATH

# Create and activate an environment
conda create -n dmri_py312 python=3.12 -y
conda activate dmri_py312
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install numpy nibabel dcm2bids dcm2niix PySide6
```

---

## Running the GUI

If you followed **Full Setup**:

```bash
cd /autofs/cluster/connectome2/Bay8_C2/bids/code/preprocessing_dwi
python main.py
```

The Qt window lists each preprocessing module in order; click **Run** to advance.

---

## Pipeline Steps

1. **dcm2bids** – convert raw DICOMs to BIDS.  
2. **Export Diffusion Parameters** – writes `*_phenc.txt`, `bvecs`, `bvals`, `diffusionTime`, `pulseWidth`.  
3. **Concatenate DWI** – merge wedges in acquisition order.  
4. **Gibbs Ringing Removal**  
5. **TopUp** (≈ 2 h)  
6. **Mask Generation** – WM & brain masks.  
7. **Eddy** (≈ 6 h)  
8. **Gradient Non-linearity Correction (GNC)**  
9. **Eddy-GNC Interpolation** (≈ 3 h)  
10. **Noise Map (MP-PCA)** – needed for SANDI model-fitting.  
11. **Write outputs** to `derivatives/processed_dwi/`  
12. **FreeSurfer** `recon-all`  

> **Heads-up** Long steps run on the cluster queue—watch the log panel for job IDs and progress.

---

## License

[MIT](LICENSE)

---

## Acknowledgements

- FreeSurfer development team  
- MRtrix3 contributors  
- Miniforge / Conda-Forge community  
- Martinos Center colleagues  
