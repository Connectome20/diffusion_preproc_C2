import os
import nibabel as nib
import numpy as np
import subprocess


def create_output_folders(output_dir):
    os.makedirs(output_dir, exist_ok=True)


def get_total_runs(dwi_dir, subject_id):
    # Identify all run files for the subject
    run_files = [f for f in os.listdir(dwi_dir) if f.startswith(subject_id) and f.endswith('.nii.gz')]
    # Extract the run numbers, convert them to integers, and find the maximum
    run_numbers = [int(f.split('_run-')[1].split('_')[0]) for f in run_files]
    return max(run_numbers)

def modify_bvals(input_bval_file, output_bval_file):
    # Define the standard b-values (keys)
    keys = np.array([0, 50, 350, 800, 1500, 2400, 3450, 4750, 6000, 200, 950, 2300, 4250, 6750, 9850, 13500, 17800])

    # Read the original b-values from the file
    with open(input_bval_file, 'r') as file:
        bvals_orig = np.array([float(val) for val in file.read().strip().split()])

    # Calculate the differences between original b-values and keys
    differences = np.abs(bvals_orig - keys[:, None])
    
    # Find the closest standard b-value for each original b-value
    closest_key_indices = np.argmin(differences, axis=0)
    closest_keys = keys[closest_key_indices]

    # Apply specific adjustment
    closest_keys[closest_keys == 2400] = 2401

    # Write the modified b-values to a new file
    with open(output_bval_file, 'w') as file:
        file.write(' '.join(map(str, closest_keys)))

        