import os
import nibabel as nib
import numpy as np
import subprocess


def concatenate_nifti_with_mrcat(file_paths, output_file):
    command = ['mrcat'] + file_paths + ['-axis', '3', output_file, '-force']
    subprocess.run(command, check=True)

def concatenate_text_files(file_paths, output_file, n_volumes_per_file, is_bvec=False):
    if is_bvec:
        # Initialize lists to hold x, y, z components
        x_components, y_components, z_components = [], [], []
        for file_path, n_volumes in zip(file_paths, n_volumes_per_file):
            with open(file_path, 'r') as file:
                contents = file.read().strip()
                rows = contents.split('\n')
                if len(rows) != 3:
                    raise ValueError(f"Unexpected format in file {file_path}: expected 3 rows, got {len(rows)}")
                
                # Extract x, y, z components from each row
                x, y, z = [row.split() for row in rows]
                if not (len(x) == len(y) == len(z) == n_volumes):
                    raise ValueError(f"Data length mismatch in file {file_path}: expected {n_volumes} volumes, got {len(x)}")
                
                # Append components for concatenation
                x_components.extend(x)
                y_components.extend(y)
                z_components.extend(z)
        
        # Write concatenated components to the output file without extra newlines
        with open(output_file, 'w') as outfile:
            outfile.write(' '.join(x_components) + '\n')
            outfile.write(' '.join(y_components) + '\n')
            outfile.write(' '.join(z_components))
    else:
        concatenated_data = []
        for file_path, n_volumes in zip(file_paths, n_volumes_per_file):
            with open(file_path, 'r') as file:
                data = file.read().strip().split()
                if len(data) != n_volumes:
                    raise ValueError(f"Data length mismatch in file {file_path}: "
                                     f"expected {n_volumes} data points, got {len(data)}")
                concatenated_data.extend(data)
        
        with open(output_file, 'w') as outfile:
            outfile.write(' '.join(concatenated_data).strip())

def concatenate_files(subj_dir, output_dir, order, subject_id, n_volumes_per_file):
    # Concatenate NIfTI files using mrcat
    nii_paths = [os.path.join(subj_dir, f"{subject_id}_run-{str(i).zfill(2)}_dwi.nii.gz") for i in order]
    output_nii_file = os.path.join(output_dir, f"{subject_id}_dwi.nii.gz")
    concatenate_nifti_with_mrcat(nii_paths, output_nii_file)

    # Concatenate other files
    for file_type in ['bval', 'diffusionTime', 'pulseWidth', 'phaseEncoding']:
        file_paths = [os.path.join(subj_dir, f"{subject_id}_run-{str(i).zfill(2)}_dwi.{file_type}") for i in order]
        output_file_type = os.path.join(output_dir, f"{subject_id}.{file_type}")
        concatenate_text_files(file_paths, output_file_type, n_volumes_per_file, is_bvec=False)

    # Concatenate bvec files
    bvec_paths = [os.path.join(subj_dir, f"{subject_id}_run-{str(i).zfill(2)}_dwi.bvec") for i in order]
    output_bvec_file = os.path.join(output_dir, f"{subject_id}.bvec")
    concatenate_text_files(bvec_paths, output_bvec_file, n_volumes_per_file, is_bvec=True)


def create_output_folders(output_dir):
    os.makedirs(output_dir, exist_ok=True)

def get_phase_encoding_order(phase_encoding_dir, subject_id):
    phase_encoding_files = [f for f in os.listdir(phase_encoding_dir) if f.endswith('.phaseEncoding')]
    for file_name in sorted(phase_encoding_files):
        if subject_id in file_name:
            with open(os.path.join(phase_encoding_dir, file_name), 'r') as f:
                contents = f.read().strip()
                if '-1' in contents:
                    # Extract the run number from the filename
                    run_number = int(file_name.split('_run-')[1].split('_')[0])
                    return run_number
    return None

def get_total_runs(dwi_dir, subject_id):
    # Identify all run files for the subject
    run_files = [f for f in os.listdir(dwi_dir) if f.startswith(subject_id) and f.endswith('.nii.gz')]
    # Extract the run numbers, convert them to integers, and find the maximum
    run_numbers = [int(f.split('_run-')[1].split('_')[0]) for f in run_files]
    return max(run_numbers)

def get_concatenation_order(pa_index, total_runs):
    if pa_index == 1:
        return list(range(1, total_runs + 1))
    else:
        return list(range(pa_index, pa_index + 2)) + list(range(1, pa_index)) + list(range(pa_index + 2, total_runs + 1))

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

        
def concatenate_dwi_data(subj_dir, subject_id, output_base):
    # Create the output directory
    output_dir = os.path.join(output_base, 's1_concat')
    create_output_folders(output_dir)

    # Get the PA index and total number of runs
    pa_index = get_phase_encoding_order(subj_dir, subject_id)
    if pa_index is None:
        raise ValueError("PA file with '-1' in phaseEncoding not found")
    total_runs = get_total_runs(subj_dir, subject_id)

    # Establish the order for concatenation
    order = get_concatenation_order(pa_index, total_runs)
    
    # Generate file paths for nii files and calculate the number of volumes for each run
    nii_paths = [os.path.join(subj_dir, f"{subject_id}_run-{str(i).zfill(2)}_dwi.nii.gz") for i in order]
    n_volumes_per_file = [nib.load(f).header.get_data_shape()[-1] for f in nii_paths]

    # Concatenate the files based on the order
    concatenate_files(subj_dir, output_dir, order, subject_id, n_volumes_per_file)
    
    # Mod bvals
    input_bval_file = os.path.join(output_dir, f"{subject_id}.bval")
    output_bval_file = os.path.join(output_dir, f"{subject_id}.bval_mod")
    modify_bvals(input_bval_file, output_bval_file)

    print(f"Processing complete. Concatenated files are saved in {output_dir}")
    
