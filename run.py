#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import sys
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as msgbox
from tkinter import filedialog
import os
import nibabel as nib
import numpy as np
import glob
import shutil
import subprocess
import tempfile

from helpers.concat_dwis import create_output_folders, get_total_runs, modify_bvals
from helpers.dcm2bids_exportparam_concat_helper import (
    dcm2bids_command,
    export_diffusion_parameters_command,
    concatenate_dwi_data_command,
)
from helpers.degibbs_helper import degibbs_commands
from helpers.topup_helper import topup_commands
from helpers.generate_masks_helper import generate_masks_commands
from helpers.eddy_helper import eddy_commands
from helpers.gnc_helper import gnc_commands
from helpers.interpolation_eddy_gnc_helper import interpolation_eddy_gnc
from helpers.gnc_anat_helper import gnc_anat_commands
from helpers.denoise_helper import denoise_commands

# Global list to store the executed commands
executed_commands = []

def get_subject_ids():
    subject_ids = subj_entry.get("1.0", 'end-1c').strip()
    return [sid.strip() for sid in subject_ids.split(',') if sid.strip()]

def update_paths(*args):
    # Get all subject IDs from the entry widget
    subject_ids = get_subject_ids()
    
    # Get the c2path from c2path_entry
    c2path = c2path_entry.get("1.0", 'end-1c').strip()
    
    # Initialize the variables with default values
    new_dwi_path = ""
    new_dwi_process_path = ""
    new_anat_process_path = ""
    new_fsInput_path = ""
    new_image_to_run_gnc_path = ""

    # Check if there are valid subject IDs
    if subject_ids and c2path:
        for subject_id in subject_ids:
            # Update paths for the current subject
            new_dwi_path = f"{c2path}/sub-{subject_id}/dwi"
            new_dwi_process_path = f"{c2path}/sub-{subject_id}/dwi_process"
            new_anat_process_path = f"{c2path}/sub-{subject_id}/anat_process"
            new_fsInput_path = f"{c2path}/sub-{subject_id}/anat/sub-{subject_id}_run-02_T1w.nii.gz"
            new_image_to_run_gnc_path = f"{c2path}/sub-{subject_id}/anat/sub-{subject_id}_run-01_T1w.nii.gz"
    
    # Update the GUI elements with paths for the last subject_id
    subj_raw_dir_entry.delete("1.0", 'end')
    subj_raw_dir_entry.insert("1.0", new_dwi_path)
    
    subj_process_dir_entry.delete("1.0", 'end')
    subj_process_dir_entry.insert("1.0", new_dwi_process_path)
    
    anat_process_dir_entry.delete("1.0", 'end')
    anat_process_dir_entry.insert("1.0", new_anat_process_path)
    
    fsInput_entry.delete("1.0", 'end')
    fsInput_entry.insert("1.0", new_fsInput_path)  
    
    image_to_run_gnc_dir_entry.delete("1.0", 'end')
    image_to_run_gnc_dir_entry.insert("1.0", new_image_to_run_gnc_path)


def on_key_release(event):
    update_paths()


def append_command_to_script(command, base_dir, subject):
    script_dir = f"{base_dir}/s0_script"
    os.makedirs(script_dir, exist_ok=True)
    script_path = f"{script_dir}/{subject}_script_to_run.sh"
    
    with open(script_path, 'a') as file:  # Note 'a' for append mode
        file.write(command + '\n')
    
    #msgbox.showinfo("Success", f"Command appended successfully to {script_path}")

def output_shell_script(commands, base_dir, subject):
    script_dir = f"{base_dir}/s0_script"
    os.makedirs(script_dir, exist_ok=True)
    script_path = f"{script_dir}/{subject}_executed_script.sh"
    
    with open(script_path, 'w') as file:
        file.write("#!/bin/bash\n\n")
        file.write("# Auto-generated script logging all preprocessing commands executed.\n\n")
        file.writelines(commands)
    
    msgbox.showinfo("Success", f"Script saved successfully to {script_path}")

# Function to remove a script file
def remove_script(base_dir, subject):
    script_path = f"{base_dir}/s0_script/{subject}_script_to_run.sh"
    if os.path.exists(script_path):
        os.remove(script_path)
        msgbox.showinfo("Success", f"Script {script_path} removed successfully.")
    else:
        msgbox.showerror("Error", f"Script {script_path} does not exist.")

import threading  # Import threading module

def execute_script_commands(base_dir, subject):
    def run_script():
        script_path = f"{base_dir}/s0_script/{subject}_script_to_run.sh"
        if os.path.exists(script_path):
            with open(script_path, 'r') as file:
                for command in file:  # Read line by line
                    command = command.strip()
                    if command:  # Check if the line is not empty
                        try:
                            # Run the command, capture output and errors
                            completed_process = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                            
                            # Get the standard output and error
                            stdout = completed_process.stdout
                            stderr = completed_process.stderr
                            
                            # Update the status_text widget with the command and its output
                            status_text.insert('end', f"Command executed successfully:\n{command}\nOutput:\n{stdout}\n")
                            if stderr:
                                # If there is an error message, display it as well
                                status_text.insert('end', f"Errors:\n{stderr}\n")
                            
                        except subprocess.CalledProcessError as e:
                            # If a command fails, capture the error and display it
                            status_text.insert('end', f"An error occurred:\n{e.stderr}\n")
                            break  # Stop executing the next commands if an error occurs
                        finally:
                            status_text.see('end')  # Auto-scroll to the end

            # Auto-scroll the status_text widget to the bottom after each command
            status_text.see(tk.END)
        else:
            status_text.insert('end', f"Script {script_path} does not exist.\n")
            status_text.see('end')  # Auto-scroll to the end
    
    # Create a new thread for running the script
    script_thread = threading.Thread(target=run_script)
    script_thread.start()  # Start the thread
    
def execute_command_and_log_output(cmd, success_message):
    # Display the command first
    status_text.insert('end', f"Executing Command:\n{cmd}\n")
    status_text.see('end')  # Auto-scroll to the end
    
    try:
        # Run the command, capture output and errors
        completed_process = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Get the standard output and error
        stdout = completed_process.stdout
        stderr = completed_process.stderr
        
        # Update the status_text widget with the command's output
        if stdout:
            status_text.insert('end', f"{success_message} Output:\n{stdout}\n")
        if stderr:
            # If there is an error message, display it as well
            status_text.insert('end', f"Errors:\n{stderr}\n")
        
    except subprocess.CalledProcessError as e:
        # If a command fails, capture the error and display it
        status_text.insert('end', f"An error occurred:\n{e.stderr}\n")
    finally:
        status_text.see('end')  # Auto-scroll to the end
    
def execute_dcm2bids():
    subject_ids = get_subject_ids()
    
    for subject_id in subject_ids:
        c2path = c2path_entry.get("1.0", 'end-1c').strip()
        config = config_entry.get("1.0", 'end-1c').strip()
        dcm_source = dcm_source_entry.get("1.0", 'end-1c').strip()
        cmd = dcm2bids_command(subject_id, c2path, config, dcm_source)
        execute_command_and_log_output(cmd, f"dcm2bids executed successfully for {subject_id}.")

def execute_export_diffusion_parameters():
    subject_ids = get_subject_ids()
    
    for subject_id in subject_ids:
        subj_raw_dir = f"/autofs/cluster/connectome2/Bay8_C2/bids/sub-{subject_id}/dwi"
        cmd = export_diffusion_parameters_command(subject_id, subj_raw_dir)
        execute_command_and_log_output(cmd, f"Diffusion parameters exported successfully for {subject_id}.")

def execute_concatenate_dwi_data():
    subject_ids = get_subject_ids()
    for subject_id in subject_ids:
        # Dynamically construct paths for the current subject ID
        subj_raw_dir = f"/autofs/cluster/connectome2/Bay8_C2/bids/sub-{subject_id}/dwi"
        subj_process_dir = f"/autofs/cluster/connectome2/Bay8_C2/bids/sub-{subject_id}/dwi_process"
        
        # Update the GUI entries if needed (optional, for user feedback)
        subj_raw_dir_entry.delete("1.0", 'end')
        subj_raw_dir_entry.insert("1.0", subj_raw_dir)
        subj_process_dir_entry.delete("1.0", 'end')
        subj_process_dir_entry.insert("1.0", subj_process_dir)

        cmd = concatenate_dwi_data_command(subj_raw_dir, f'sub-{subject_id}', subj_process_dir)
        execute_command_and_log_output(cmd, f"DWI series concatenated successfully for {subject_id}.")

def concatenate_nifti_with_mrcat(file_paths, output_file):
    """
    Uses MRtrix3's mrcat to concatenate NIfTI files along the 4th dimension.
    """
    if not file_paths:
        raise ValueError("No valid NIfTI files provided for concatenation.")
    
    status_text.insert('end', f"Concatenating NIfTI files:\n")
    for fp in file_paths:
        status_text.insert('end', f" - {fp}\n")
    status_text.insert('end', f"Output file: {output_file}\n")
    status_text.see('end')
    
    command = ['mrcat'] + file_paths + ['-axis', '3', output_file, '-force']
    subprocess.run(command, check=True)


import numpy as np

def concatenate_text_files(file_paths, output_file):
    """
    Concatenates the content of multiple text files (e.g., bvals, bvecs, etc.) into a single output file.
    Handles 1-dimensional and 2-dimensional input data (e.g., bvecs) and concatenates along the first dimension.
    All files (except bvecs and bvals) are reshaped to (1, N).
    
    Parameters:
    - file_paths: List of file paths to be concatenated.
    - output_file: The output file where the concatenated data will be written.
    """
    try:
        concatenated_data = []

        # Define file names that are treated differently
        bvecs_file = "bvec"
        bvals_file = "bval"

        # Read and process each file
        for file_path in file_paths:
            with open(file_path, 'r') as file:
                # Load data into an array, split lines and then split elements on each line
                data = [line.strip().split() for line in file.readlines()]
                
                # Convert the list of lists into a numpy array
                data_array = np.array(data, dtype=float)

                # Check the shape of the data and handle it appropriately
                if bvecs_file in file_path:  # Shape (3, N) for bvecs
                    concatenated_data.append(data_array)
                elif bvals_file in file_path:  # Shape (1, N) for bvals
                    concatenated_data.append(data_array.flatten())
                else:
                    # Reshape all other files to (1, N)
                    concatenated_data.append(data_array.flatten().reshape(1, -1))

        # Concatenate all data along the first dimension
        concatenated_result = np.concatenate(concatenated_data, axis=1) if concatenated_data[0].ndim == 2 else np.concatenate(concatenated_data)

        # Save the concatenated result to the output file
        np.savetxt(output_file, concatenated_result, fmt='%g')
        
        print(f"Concatenation successful! Output written to {output_file}.")
    
    except FileNotFoundError as fnf_error:
        print(f"Error: One of the files was not found: {fnf_error}")
    except ValueError as ve:
        print(f"Error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")



def concatenate_files(nii_paths, output_base, subject_id):
    """
    Concatenates DWI NIfTI files and their corresponding parameter files.
    """
    # Create the output directory if it doesn't exist
    output_dir = os.path.join(output_base, 's1_concat')
    os.makedirs(output_dir, exist_ok=True)
    
    # Concatenate NIfTI files
    output_nii_file = os.path.join(output_dir, f"sub-{subject_id}_dwi.nii.gz")
    concatenate_nifti_with_mrcat(nii_paths, output_nii_file)
    
    # File types to concatenate along with NIfTI files
    file_types = ['bval', 'bvec', 'phaseEncoding', 'diffusionTime', 'pulseWidth']
    
    for file_type in file_types:
        # For each DWI file, get the corresponding supporting file path
        file_paths = []
        for nii_path in nii_paths:
            base_path = nii_path.replace('.nii.gz', '')
            supporting_file = f"{base_path}.{file_type}"
            if os.path.exists(supporting_file):
                file_paths.append(supporting_file)
            else:
                status_text.insert('end', f"Warning: {file_type} file not found for {nii_path}\n")
        
        if not file_paths:
            status_text.insert('end', f"No {file_type} files found for concatenation for subject {subject_id}.\n")
            continue  # Skip to next file type
        
        output_file_type = os.path.join(output_dir, f"sub-{subject_id}.{file_type}")
        concatenate_text_files(file_paths, output_file_type)

def concatenate_dwi_data_from_gui_entries():
    """
    Concatenates DWI data and related parameter files based on paths provided through the GUI.
    """
    # Fetch a list of subject IDs
    subject_ids = get_subject_ids()
    
    for subject_id in subject_ids:
        output_base = subj_process_dir_entry.get("1.0", "end-1c").strip()
        output_dir = os.path.join(output_base, 's1_concat')
        create_output_folders(output_dir)
        
        # Reading NIfTI file paths from the GUI entries and filtering out empty entries
        nii_paths = [entry.get("1.0", "end-1c").strip() for entry in dwi_file_entries]
        nii_paths = [path for path in nii_paths if path and os.path.exists(path)]
        
        if not nii_paths:
            status_text.insert('end', f"No valid NIfTI files provided for subject {subject_id}.\n")
            status_text.see('end')
            continue  # Skip to next subject
        
        # Calculate the number of volumes for each run (if needed)
        n_volumes_per_file = [nib.load(path).shape[-1] for path in nii_paths]
        
        # Concatenate NIfTI files and parameter files
        concatenate_files(nii_paths, output_base, subject_id)
        
        # Modify bvals as necessary
        output_dir = os.path.join(output_base, 's1_concat')
        input_bval_file = os.path.join(output_dir, f"sub-{subject_id}.bval")
        output_bval_file = os.path.join(output_dir, f"sub-{subject_id}.bval_mod")
        modify_bvals(input_bval_file, output_bval_file)
        
        status_text.insert('end', f"Processing complete. Concatenated files are saved in {output_dir}\n")
        status_text.see('end')

def execute_denoise():
    # Fetch a list of subject IDs
    subject_ids = get_subject_ids()
    
    # Retrieve the denoise option value
    denoise_option_value = denoise_option.get()
    
    # Skip the denoise process if 'No Denoise' is selected
    if denoise_option_value == "no_denoise":
        status_text.insert('end', "Denoise skipped as per the selected option.\n")
        status_text.see('end')
        return
    
    # Iterate over each subject ID
    for subject_id in subject_ids:
        # Construct the subject and base_dir for the current subject ID
        subject = f'sub-{subject_id}'
        base_dir = f"/autofs/cluster/connectome2/Bay8_C2/bids/sub-{subject_id}/dwi_process"
        
        subj_process_dir_entry.delete("1.0", 'end')
        subj_process_dir_entry.insert("1.0", base_dir)
        
        cmd = denoise_commands(subject, base_dir, denoise_option_value)
        
        execute_command_and_log_output(cmd, f"{denoise_option_value.capitalize()} denoise completed successfully for {subject_id}.")

def execute_degibbs():
    subject_ids = get_subject_ids()
    for subject_id in subject_ids:
        subject = f'sub-{subject_id}'
        base_dir = f"/autofs/cluster/connectome2/Bay8_C2/bids/sub-{subject_id}/dwi_process"
        selected_flow_value = selected_flow.get()
        
        subj_process_dir_entry.delete("1.0", 'end')
        subj_process_dir_entry.insert("1.0", base_dir)

        cmd = degibbs_commands(subject, base_dir, selected_flow_value)
        execute_command_and_log_output(cmd, f"Degibbs completed successfully for {subject_id}.")
        
def execute_topup():
    subject_ids = get_subject_ids()
    selected_flow_value = selected_flow.get()
    for subject_id in subject_ids:
        subject = f'sub-{subject_id}'
        base_dir = f"/autofs/cluster/connectome2/Bay8_C2/bids/sub-{subject_id}/dwi_process"
        subj_process_dir_entry.delete("1.0", 'end')
        subj_process_dir_entry.insert("1.0", base_dir)
        
        topup_cmds = topup_commands(base_dir, subject, selected_flow_value)
        for cmd in topup_cmds:
            execute_command_and_log_output(cmd, f"TopUp processing completed successfully for {subject_id}.")

def execute_generate_masks():
    subject_ids = get_subject_ids()
    for subject_id in subject_ids:
        subject = f'sub-{subject_id}'
        base_dir = f"/autofs/cluster/connectome2/Bay8_C2/bids/sub-{subject_id}/dwi_process"
        subj_process_dir_entry.delete("1.0", 'end')
        subj_process_dir_entry.insert("1.0", base_dir)
        cmds, temp_files = generate_masks_commands(subject, base_dir)
        for cmd in cmds:
            execute_command_and_log_output(cmd, f"Mask generation completed successfully for {subject_id}.")
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except OSError as e:
                print(f"Error: {e.filename} - {e.strerror}.")

def execute_eddy():
    subject_ids = get_subject_ids()
    selected_flow_value = selected_flow.get()
    for subject_id in subject_ids:
        subject = f'sub-{subject_id}'
        base_dir = f"/autofs/cluster/connectome2/Bay8_C2/bids/sub-{subject_id}/dwi_process"
        subj_process_dir_entry.delete("1.0", 'end')
        subj_process_dir_entry.insert("1.0", base_dir)
        cmd = eddy_commands(subject, base_dir, selected_flow_value)
        execute_command_and_log_output(cmd, f"Eddy processing completed successfully for {subject_id}.")

def execute_gnc_dwi():
    if gnc_option.get() == "no_gnc":
        status_text.insert('end', "GNC processing skipped.\n")
        status_text.see('end')
        return
    subject_ids = get_subject_ids()

    selected_flow_value = selected_flow.get()
    gnc_option_value = gnc_option.get()
    
    for subject_id in subject_ids:
        subject = f'sub-{subject_id}'
        base_dir = f"/autofs/cluster/connectome2/Bay8_C2/bids/sub-{subject_id}/dwi_process"
        subj_process_dir_entry.delete("1.0", 'end')
        subj_process_dir_entry.insert("1.0", base_dir)
        cmd = gnc_commands(subject, base_dir, selected_flow_value, gnc_option_value)
        execute_command_and_log_output(cmd, f"GNC processing for DWI completed successfully for {subject_id}.")

def execute_interpolation_eddy_gnc():
    subject_ids = get_subject_ids()  
    flow_value = selected_flow.get() 
    for subject_id in subject_ids:
        base_dir = f"/autofs/cluster/connectome2/Bay8_C2/bids/sub-{subject_id}/dwi_process"
        try:
            interpolation_eddy_gnc(subject_id, base_dir, flow_value)
            status_text.insert('end', f"Interpolation and Jacobian correction completed successfully for {subject_id}.\n")
        except Exception as e:
            msgbox.showerror("Error", f"An error occurred for {subject_id}: {str(e)}")
            status_text.insert('end', f"An error occurred for {subject_id}: {str(e)}\n")
        status_text.see('end')

def execute_gnc_anat():
    if gnc_anat_option.get() == "no_gnc":
        status_text.insert('end', "GNC Anat processing skipped.\n")
        status_text.see('end')
        return

    subject_ids = get_subject_ids()
    gnc_anat_option_value = gnc_anat_option.get()
    
    for subject_id in subject_ids:
        subject = f'sub-{subject_id}'
        anat_process_dir = f"/autofs/cluster/connectome2/Bay8_C2/bids/sub-{subject_id}/anat_process"
        image_to_run_gnc_dir = f"/autofs/cluster/connectome2/Bay8_C2/bids/sub-{subject_id}/anat/sub-{subject_id}_run-01_T1w.nii.gz"     
        cmd = gnc_anat_commands(subject, anat_process_dir, image_to_run_gnc_dir, gnc_anat_option_value)
        execute_command_and_log_output(cmd, f"{gnc_anat_option_value} GNC Anat completed successfully for {subject_id}.")

def execute_commands_with_env(commands, env_exports, success_message):
    # Create a temporary shell script file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as temp_script:
        script_path = temp_script.name
        # Write the environment exports and commands to the script
        temp_script.write('#!/bin/bash\n')
        temp_script.write(env_exports + '\n')
        for cmd in commands:
            temp_script.write(cmd + '\n')

    # Make the script executable
    os.chmod(script_path, 0o775)

    # Execute the script
    status_text.insert('end', f"Executing Script: {script_path}\n")
    status_text.see('end')

    try:
        completed_process = subprocess.run(
            f"/bin/bash {script_path}", shell=True, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        stdout = completed_process.stdout
        stderr = completed_process.stderr

        if stdout:
            status_text.insert('end', f"{success_message}\nOutput:\n{stdout}\n")
        if stderr:
            status_text.insert('end', f"Standard Error:\n{stderr}\n")

        return True

    except subprocess.CalledProcessError as e:
        error_output = e.stderr or e.stdout
        status_text.insert('end', f"An error occurred:\n{error_output}\n")
        return False

    finally:
        status_text.see('end')
        # Clean up the temporary script file
        os.remove(script_path)

def execute_recon_all():
    subject_ids = get_subject_ids()
    
    for subject_id in subject_ids:
        subj_id = f"sub-{subject_id}"
        
        # Retrieve the anatomical processing directory from the GUI entry
        anat_process_dir_template = anat_process_dir_entry.get("1.0", 'end-1c').strip()
        
        # Replace placeholders in the anatomical processing directory path with the actual subject ID
        anat_process_dir = anat_process_dir_template.replace('{subj_id}', subj_id)
        
        # Create the anat_process directory if it doesn't exist
        if not os.path.exists(anat_process_dir):
            os.makedirs(anat_process_dir)
            status_text.insert('end', f"Created directory: {anat_process_dir}\n")
        
        # Set SUBJECTS_DIR environment variable
        SUBJECTS_DIR = anat_process_dir
        os.environ['SUBJECTS_DIR'] = SUBJECTS_DIR
        status_text.insert('end', f"Set SUBJECTS_DIR to {SUBJECTS_DIR}\n")
        
        # Change directory to SUBJECTS_DIR
        os.chdir(SUBJECTS_DIR)
        status_text.insert('end', f"Changed directory to {SUBJECTS_DIR}\n")
        
        # Retrieve the input image path from the FreeSurfer Input Image entry
        input_image_template = fsInput_entry.get("1.0", 'end-1c').strip()
        
        # Replace placeholders in the input image path with the actual subject ID
        input_image = input_image_template.replace('{subj_id}', subj_id)
        
        # Set the environment variables and source the FreeSurfer setup script
        env_exports = f"""
export FREESURFER_HOME=/usr/local/freesurfer/7.4.1
export FSFAST_HOME=/usr/local/freesurfer/7.4.1/fsfast
export SUBJECTS_DIR={SUBJECTS_DIR}
export MNI_DIR=/usr/local/freesurfer/7.4.1/mni
source $FREESURFER_HOME/SetUpFreeSurfer.sh
"""
        
        # Commands to execute
        cmd1 = f"recon-all -subjid fs -i {input_image} -autorecon1"
        
        freesurfer_dir = f"{anat_process_dir}/fs"
        input_nii = f"{freesurfer_dir}/mri/T1.mgz"
        output_nii = f"{freesurfer_dir}/mri/brainmask.mgz"
        cmd2 = f"mri_synthstrip -i {input_nii} -o {output_nii}"
        
        cmd3 = f"recon-all -autorecon2 -autorecon3 -s fs"
        
        # Execute Command 1
        success = execute_commands_with_env(
            [cmd1], env_exports, f"recon-all -autorecon1 executed successfully for {subject_id}."
        )
        if not success:
            status_text.insert('end', f"Command 1 failed for {subject_id}, skipping remaining commands.\n")
            continue
        
        # Execute Command 2
        success = execute_commands_with_env(
            [cmd2], env_exports, f"mri_synthstrip executed successfully for {subject_id}."
        )
        if not success:
            status_text.insert('end', f"Command 2 failed for {subject_id}, skipping remaining commands.\n")
            continue
        
        # Execute Command 3
        success = execute_commands_with_env(
            [cmd3], env_exports, f"recon-all -autorecon2 and -autorecon3 executed successfully for {subject_id}."
        )
        if not success:
            status_text.insert('end', f"Command 3 failed for {subject_id}.\n")
            continue

def mppca_noise():
    subject_ids = get_subject_ids()
    scanner_type = gnc_option.get()
    
    if scanner_type == "C1":
        hcps_gnc_cmd = "/space/scheherazade/2/users/qfan/tools/preproc/hcps_diff_prep_v2/hcps_gnc.sh"  # Replace with the actual path for C1
    elif scanner_type == "C2":
        hcps_gnc_cmd = "/space/scheherazade/2/users/qfan/tools/preproc/hcps_diff_prep_v2/hcps_gnc_c2.sh"
    else:
        status_text.insert('end', f"Unknown scanner type: {scanner_type}. Skipping GNC processing.\n")
        return

    for subject_id in subject_ids:
        base_dir = f"/autofs/cluster/connectome2/Bay8_C2/bids/sub-{subject_id}/dwi_process"
        concat_dir = f"{base_dir}/s1_concat"

        dwiextract_cmd = f"dwiextract {concat_dir}/*dwi.nii.gz -fslgrad {concat_dir}/*bvec {concat_dir}/*bval -bzero {concat_dir}/sub-{subject_id}_b0s.nii.gz"
        dwidenoise_cmd = f"dwidenoise {concat_dir}/sub-{subject_id}_b0s.nii.gz {concat_dir}/sub-{subject_id}_b0s_denoised.nii.gz -noise {concat_dir}/sub-{subject_id}_sigma.nii.gz"
        hcps_gnc_sigma_cmd = f"{hcps_gnc_cmd} -i {concat_dir}/sub-{subject_id}_sigma.nii.gz -o {base_dir}/s9_noise/sub-{subject_id}_sigma.nii.gz -interp spline"
        mask_dir = f"{base_dir}/s5_mask"
        hcps_gnc_mask_cmd = f"{hcps_gnc_cmd} -i {mask_dir}/brain_mask.nii.gz -o {base_dir}/s5_mask/sub-{subject_id}_brain_mask_gnc.nii.gz -interp nn"
        hcps_gnc_wm_cmd = f"{hcps_gnc_cmd} -i {mask_dir}/wm.nii.gz -o {base_dir}/s5_mask/sub-{subject_id}_wm_gnc.nii.gz -interp nn"

        for cmd in [dwiextract_cmd, dwidenoise_cmd, hcps_gnc_sigma_cmd, hcps_gnc_mask_cmd, hcps_gnc_wm_cmd]:
            execute_command_and_log_output(cmd, f"Command '{cmd.split()[0]}' executed successfully for {subject_id}.")

def append_all_commands_to_script():
    subject_id = subj_entry.get("1.0", 'end-1c').strip()
    base_dir = subj_process_dir_entry.get("1.0", 'end-1c').strip()
    subject = 'sub-' + subject_id

    # Ensure the script directory exists
    script_dir = f"{base_dir}/s0_script"
    os.makedirs(script_dir, exist_ok=True)

    # Commands for each step
    # 1. DCM2BIDS
    dcm2bids_cmd = dcm2bids_command(subject_id, c2path_entry.get("1.0", 'end-1c').strip(), config_entry.get("1.0", 'end-1c').strip(), dcm_source_entry.get("1.0", 'end-1c').strip())
    append_command_to_script(dcm2bids_cmd, base_dir, subject)

    # 2. Export Diffusion Parameters
    export_diffusion_params_cmd = export_diffusion_parameters_command(subject_id, subj_raw_dir_entry.get("1.0", 'end-1c').strip())
    append_command_to_script(export_diffusion_params_cmd, base_dir, subject)

    # 3. Concatenate DWI Data
    concatenate_dwi_data_cmd = concatenate_dwi_data_command(subj_raw_dir_entry.get("1.0", 'end-1c').strip(), subject, base_dir)
    append_command_to_script(concatenate_dwi_data_cmd, base_dir, subject)

    # 4. Denoise (if applicable)
    denoise_option_value = denoise_option.get()
    if denoise_option_value != "no_denoise":
        denoise_cmd = denoise_commands(subject, base_dir, denoise_option_value)
        append_command_to_script(denoise_cmd, base_dir, subject)

    # 5. Degibbs
    degibbs_cmd = degibbs_commands(subject, base_dir, selected_flow.get())
    append_command_to_script(degibbs_cmd, base_dir, subject)

    # 6. TopUp
    topup_cmds = topup_commands(base_dir, subject, selected_flow.get())
    for cmd in topup_cmds:
        append_command_to_script(cmd, base_dir, subject)

    # 7. Generate Masks
    generate_masks_cmds, _ = generate_masks_commands(subject, base_dir)
    for cmd in generate_masks_cmds:
        append_command_to_script(cmd, base_dir, subject)

    # 8. Eddy
    eddy_cmd = eddy_commands(subject, base_dir, selected_flow.get())
    append_command_to_script(eddy_cmd, base_dir, subject)

    # 9. GNC DWI
    gnc_cmd = gnc_commands(subject, base_dir, selected_flow.get(), gnc_option.get())
    append_command_to_script(gnc_cmd, base_dir, subject)

    # 10. GNC Anat
    gnc_anat_cmd = gnc_anat_commands(subject, anat_process_dir_entry.get("1.0", 'end-1c').strip(), image_to_run_gnc_dir_entry.get("1.0", 'end-1c').strip(), gnc_anat_option.get())
    append_command_to_script(gnc_anat_cmd, base_dir, subject)

    # 11. recon-all
    expertFile = "/autofs/cluster/connectome2/Bay8_C2/TractCaliber_script/freesurfer/expertFile"
    fsInput = fsInput_entry.get("1.0", 'end-1c').strip()
    recon_all_cmd = f"export SUBJECTS_DIR={base_dir}; recon-all -subjid fs -i {fsInput} -all -hires -expert {expertFile}"
    append_command_to_script(recon_all_cmd, base_dir, subject)

    # 12. MP-PCA Noise Map Generation
    subject_id = subj_entry.get("1.0", 'end-1c').strip()
    base_dir = subj_process_dir_entry.get("1.0", 'end-1c').strip()
    concat_dir = f"{base_dir}/s1_concat"

    # Commands for mppca_noise
    dwiextract_cmd = f"dwiextract {concat_dir}/*dwi.nii.gz -fslgrad {concat_dir}/*bvec {concat_dir}/*bval -bzero {concat_dir}/sub-{subject_id}_b0s.nii.gz"
    dwidenoise_cmd = f"dwidenoise {concat_dir}/sub-{subject_id}_b0s.nii.gz {concat_dir}/sub-{subject_id}_b0s_denoised.nii.gz -noise {concat_dir}/sub-{subject_id}_sigma.nii.gz"
    hcps_gnc_c2_cmd = f"/space/scheherazade/2/users/qfan/tools/preproc/hcps_diff_prep_v2/hcps_gnc_c2.sh -i {concat_dir}/sub-{subject_id}_sigma.nii.gz -o {base_dir}/s9_noise/sub-{subject_id}_sigma.nii.gz -interp spline"
    hcps_gnc_wm_cmd = f"{hcps_gnc_cmd} -i {mask_dir}/wm.nii.gz -o {base_dir}/s5_mask/sub-{subject_id}_wm_gnc.nii.gz -interp nn"

    mask_dir = f"{base_dir}/s5_mask"
    hcps_gnc_mask_cmd = f"/space/scheherazade/2/users/qfan/tools/preproc/hcps_diff_prep_v2/hcps_gnc_c2.sh -i {mask_dir}/brain_mask.nii.gz -o {base_dir}/s5_mask/sub-{subject_id}_brain_mask_gnc.nii.gz -interp nn"

    # Append commands to script
    for cmd in [dwiextract_cmd, dwidenoise_cmd, hcps_gnc_c2_cmd, hcps_gnc_mask_cmd,hcps_gnc_wm_cmd]:
        append_command_to_script(cmd, base_dir, subject)

    msgbox.showinfo("Success", "All commands appended successfully to the script.")

def write_output_to_processed_dwi():
    # Fetch a list of subject IDs
    subject_ids = get_subject_ids()
    
    for subject_id in subject_ids:
        source_base_dir = f"/autofs/cluster/connectome2/Bay8_C2/bids/sub-{subject_id}"
        destination_dir = f"/autofs/cluster/connectome2/Bay8_C2/bids/derivatives/processed_dwi/sub-{subject_id}"
        freesurfer_destination_dir = f"/autofs/cluster/connectome2/Bay8_C2/bids/derivatives/FreeSurfer/sub-{subject_id}"

        # Create destination directories if they do not exist
        os.makedirs(destination_dir, exist_ok=True)
        os.makedirs(freesurfer_destination_dir, exist_ok=True)

        # Files to be copied for processed DWI
        file_patterns = {
            "s1_concat/*.bval_mod": "sub-{subject_id}.bval",
            "s1_concat/*.phaseEncoding": "sub-{subject_id}.phaseEncoding",
            "s1_concat/*.pulseWidth": "sub-{subject_id}.pulseWidth",
            "s1_concat/*.diffusionTime": "sub-{subject_id}.diffusionTime",
            "*eddy/*rotated_bvecs": "sub-{subject_id}.bvec",
            "s8_final/*_dwi.nii.gz": "sub-{subject_id}_dwi.nii.gz",
            "s9_noise/*_sigma.nii.gz": "sub-{subject_id}_sigma.nii.gz"
        }
        
        # Copy the files for processed DWI
        try:
            for pattern, output_name in file_patterns.items():
                file_pattern = os.path.join(source_base_dir, "dwi_process", pattern)
                files_found = glob.glob(file_pattern)
                if not files_found:
                    status_text.insert('end', f"No files found for pattern: {file_pattern}\n")
                    continue
                
                for file_path in files_found:
                    # Determine the destination path
                    destination_file_path = os.path.join(destination_dir, output_name.format(subject_id=subject_id))
                    
                    # Copy the file
                    shutil.copy(file_path, destination_file_path)
                    status_text.insert('end', f"Copied to: {destination_file_path}\n")
        except Exception as e:
            status_text.insert('end', f"An error occurred for {subject_id}: {e}\n")
        
        # Copy the FreeSurfer data
        freesurfer_source_dir = os.path.join(source_base_dir, "anat_process/fs")
        if os.path.exists(freesurfer_source_dir):
            try:
                # Copy the entire FreeSurfer directory for the subject
                dest_fs_dir = os.path.join(freesurfer_destination_dir, "fs")
                if os.path.exists(dest_fs_dir):
                    shutil.rmtree(dest_fs_dir)
                shutil.copytree(freesurfer_source_dir, dest_fs_dir)
                status_text.insert('end', f"Copied FreeSurfer data to: {dest_fs_dir}\n")
            except Exception as e:
                status_text.insert('end', f"An error occurred while copying FreeSurfer data for {subject_id}: {e}\n")
        else:
            status_text.insert('end', f"FreeSurfer source directory does not exist for {subject_id}: {freesurfer_source_dir}\n")

        status_text.see('end')
    
def execute_all_steps():
    """
    Sequentially executes all the processing steps, waiting for each to complete before proceeding.
    """
    def check_dwi_file_entries():
        """Check if any of the DWI file entries contains a valid path."""
        for entry in dwi_file_entries:
            if entry.get("1.0", 'end-1c').strip():  # Check if any entry is not empty
                return True
        return False
    
    def run_step(step_function, next_steps):
        try:
            step_function()  # Execute the step
            if next_steps:  # If there are more steps, proceed with the next one
                root.after(100, run_step, next_steps[0], next_steps[1:])
            else:
                msgbox.showinfo("Success", "All steps executed successfully.")
        except Exception as e:
            msgbox.showerror("Error", f"An error occurred during processing: {str(e)}")

    # Determine which concatenate DWI step to include
    if check_dwi_file_entries():
        concatenate_step = concatenate_dwi_data_from_gui_entries
    else:
        concatenate_step = execute_concatenate_dwi_data
    
    # Add execute_recon_all to the list of steps
    steps = [
        execute_dcm2bids,
        execute_export_diffusion_parameters,
        concatenate_step,  # Use the chosen concatenate function
        execute_degibbs,
        execute_topup,
        execute_generate_masks,
        execute_eddy,
        execute_gnc_dwi,
        execute_interpolation_eddy_gnc,
        mppca_noise,
        write_output_to_processed_dwi,
        execute_recon_all  # Added recon-all to the sequence
    ]

    run_step(steps[0], steps[1:])


# Function to create a horizontal scrollable entry field with copy/paste functionality
def make_horizontal_scrollable_entry(parent, width, height):
    entry_frame = ttk.Frame(parent)
    entry = tk.Text(entry_frame, width=width, height=height, wrap='none', undo=True)
    scrollbar_x = ttk.Scrollbar(entry_frame, command=entry.xview, orient="horizontal", style='Thin.Horizontal.TScrollbar')
    entry.config(xscrollcommand=scrollbar_x.set)
    entry.grid(row=0, column=0, sticky="nsew")
    entry_frame.columnconfigure(0, weight=1)  # Make the entry expand
    scrollbar_x.grid(row=1, column=0, sticky="ew")
    
    # Right-click context menu
    menu = tk.Menu(entry, tearoff=0)
    menu.add_command(label="Cut", command=lambda: entry.event_generate("<<Cut>>"))
    menu.add_command(label="Copy", command=lambda: entry.event_generate("<<Copy>>"))
    menu.add_command(label="Paste", command=lambda: entry.event_generate("<<Paste>>"))
    
    def show_context_menu(event):
        menu.post(event.x_root, event.y_root)
        
    entry.bind("<Button-3>", show_context_menu)
    return entry, entry_frame

# Create the main window
root = tk.Tk()
root.title("Diffusion pre-processing")
#root.geometry("800x810")  # Adjusted size to give more room

# Create a canvas and a scrollbar
canvas = tk.Canvas(root)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill="y")

canvas.configure(yscrollcommand=scrollbar.set)

# Create a frame inside the canvas
main_frame = ttk.Frame(canvas)

# Add the main_frame to the canvas
canvas.create_window((0, 0), window=main_frame, anchor="nw")

def on_frame_configure(event=None):
    # Update the scrollable size of the canvas
    canvas.configure(scrollregion=canvas.bbox("all"))

def on_mousewheel(event):
    # Allow scrolling with the mouse wheel
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

main_frame.bind("<Configure>", on_frame_configure)
canvas.bind_all("<MouseWheel>", on_mousewheel)  # This might need adjustment on Linux or macOS

# Style configuration
style = ttk.Style()
style.theme_use('clam')  # or another theme that fits the application

# Set default font
default_font = ('Arial', 8)
root.option_add('*Font', default_font)

# Configure style for the large buttons
button_style = ttk.Style()
button_style.configure('Large.TButton', font=('Arial', 8, 'bold'), background='white')
button_style = ttk.Style()
button_style.configure('Small.TButton', font=('Arial', 8))

# Configure style for the thinner horizontal scrollbar
style.configure('Thin.Horizontal.TScrollbar', gripcount=0, borderwidth=1, arrowcolor='blue')

# Subject ID Entry
tk.Label(main_frame, text="Subject ID:").grid(row=0, column=0, sticky='w')
subj_entry, subj_entry_frame = make_horizontal_scrollable_entry(main_frame, width=50, height=1)
subj_entry_frame.grid(row=0, column=1, sticky='ew')
subj_entry.insert('1.0', "011")
# Bind the key release event to the subj_entry widget
subj_entry.bind("<KeyRelease>", on_key_release)

# C2 Path Entry
tk.Label(main_frame, text="C2 Path:").grid(row=1, column=0, sticky='w')
c2path_entry, c2path_entry_frame = make_horizontal_scrollable_entry(main_frame, width=50, height=1)
c2path_entry_frame.grid(row=1, column=1, sticky='ew')
c2path_entry.insert('1.0', "/autofs/cluster/connectome2/Bay8_C2/bids")
# Bind the key release event to the c2path_entry widget
c2path_entry.bind("<KeyRelease>", lambda event: update_paths())


# Config Path Entry
tk.Label(main_frame, text="Config Path:").grid(row=2, column=0, sticky='w')
config_entry, config_entry_frame = make_horizontal_scrollable_entry(main_frame, width=50, height=1)
config_entry_frame.grid(row=2, column=1, sticky='ew')
config_entry.insert('1.0', "/autofs/cluster/connectome2/Bay8_C2/TractCaliber_script/dcm2bids/config.json")

# Dicom Source Entry
tk.Label(main_frame, text="Dicom Source:").grid(row=3, column=0, sticky='w')
dcm_source_entry, dcm_source_entry_frame = make_horizontal_scrollable_entry(main_frame, width=50, height=1)
dcm_source_entry_frame.grid(row=3, column=1, sticky='ew')
dcm_source_entry.insert('1.0', "/cluster/archive/348/siemens/MAGNETOM-Connectom.X-237551-20231122-131220-001197")

execute_dcm2bids_button = ttk.Button(main_frame, text="Execute dcm2bids", command=execute_dcm2bids, style='Large.TButton', width=30)
execute_dcm2bids_button.grid(row=4, column=1, padx=(10, 0))

# Separator after dcm2bids section
ttk.Separator(main_frame, orient='horizontal').grid(row=5, columnspan=5, sticky="ew")

# Subj Raw Directory Entry
tk.Label(main_frame, text="Subj Raw Directory:").grid(row=6, column=0, sticky='w')
subj_raw_dir_entry, subj_raw_dir_entry_frame = make_horizontal_scrollable_entry(main_frame, width=50, height=1)
subj_raw_dir_entry_frame.grid(row=6, column=1, sticky='ew')
subj_raw_dir_entry.insert('1.0', "/autofs/cluster/connectome2/Bay8_C2/bids/sub-011/dwi")

execute_export_diffusion_parameters_button = ttk.Button(main_frame, 
                                                        text="Export Diffusion Parameters", 
                                                        command=execute_export_diffusion_parameters, 
                                                        style='Large.TButton', width=30)
execute_export_diffusion_parameters_button.grid(row=7, column=1, padx=(10, 0))

# Separator after diffusion parameters section
ttk.Separator(main_frame, orient='horizontal').grid(row=8, columnspan=5, sticky="ew")

# Subj Processing Directory Entry
tk.Label(main_frame, text="Subj Processing Directory:").grid(row=9, column=0, sticky='w')
subj_process_dir_entry, subj_process_dir_entry_frame = make_horizontal_scrollable_entry(main_frame, width=50, height=1)
subj_process_dir_entry_frame.grid(row=9, column=1, sticky='ew')
subj_process_dir_entry.insert('1.0', "/autofs/cluster/connectome2/Bay8_C2/bids/sub-011/dwi_process")

def create_file_entry_widgets(parent):
    """Create entry widgets for DWI file paths and the output folder, with a button to open a file dialog."""
    dwi_file_labels = ["DWI File 1:", "DWI File 2:", "DWI File 3:", "DWI File 4:", "DWI File 5:"]
    dwi_file_entries = []
    for i, label in enumerate(dwi_file_labels, start=10):  # Adjust start index based on your layout
        # Create a row frame
        row_frame = ttk.Frame(parent)
        row_frame.grid(row=i, column=1, sticky='ew', padx=5)
        parent.columnconfigure(1, weight=1)
        row_frame.columnconfigure(0, weight=4)
        
        tk.Label(parent, text=label).grid(row=i, column=0, sticky='w', padx=5, pady=2)
        
        # Create entry with scrollable functionality
        entry, entry_frame = make_horizontal_scrollable_entry(row_frame, width=40, height=1)
        entry_frame.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        
        # Button to open file dialog
        def open_file_dialog(entry=entry):
            # Retrieve the subject ID from the subject ID entry widget
            subject_id = subj_entry.get("1.0", 'end-1c').strip()
            initial_directory = f"/autofs/cluster/connectome2/Bay8_C2/bids/sub-{subject_id}/dwi"
            
            # Define the function to open the file dialog and update the entry
            filename = filedialog.askopenfilename(
                initialdir=initial_directory,  # Use the dynamic initial directory based on subject ID
                title="Select file",
                filetypes=(("Nifti files", "*.nii *.nii.gz"), ("all files", "*.*")))
            entry.delete("1.0", 'end')
            entry.insert("1.0", filename)
        
        # Add button next to the entry
        browse_button = ttk.Button(row_frame, text="Browse", command=lambda e=entry: open_file_dialog(e))
        browse_button.grid(row=0, column=1, sticky='ew')
        
        dwi_file_entries.append(entry)
    
    return dwi_file_entries


dwi_file_entries = create_file_entry_widgets(main_frame)

execute_concatenate_dwi_data_button = ttk.Button(main_frame, text="Concatenate DWI Data", command=execute_concatenate_dwi_data, style='Large.TButton', width=30)
execute_concatenate_dwi_data_button.grid(row=15, column=1, padx=(10, 0))

concatenate_dwi_button = ttk.Button(main_frame, text="Concatenate DWI data from entries", command=concatenate_dwi_data_from_gui_entries,style='Large.TButton',width=30)
concatenate_dwi_button.grid(row=16, column=1, padx=(10,0))  # Adjust the row and column indices appropriately

# Separator after concatenation section
ttk.Separator(main_frame, orient='horizontal').grid(row=17, columnspan=5, sticky="ew")

# Denoise Option Selection
tk.Label(main_frame, text="Select Denoise Option:").grid(row=18, column=0, sticky='w')
denoise_option = tk.StringVar(value="no_denoise")  # Default value is now "no_denoise"

# Internal frame for denoise radio buttons
denoise_radio_button_frame = tk.Frame(main_frame)  
denoise_radio_button_frame.grid(row=18, column=1, sticky='w')

# Radio Buttons for Denoise Option
no_denoise_rb = tk.Radiobutton(denoise_radio_button_frame, text="No Denoise", variable=denoise_option, value="no_denoise", background='lightblue')
no_denoise_rb.pack(side='left', padx=5)

magnitude_denoise_rb = tk.Radiobutton(denoise_radio_button_frame, text="Magnitude Denoise", variable=denoise_option, value="magnitude", background='lightblue')
magnitude_denoise_rb.pack(side='left', padx=5)

real_denoise_rb = tk.Radiobutton(denoise_radio_button_frame, text="Real Denoise", variable=denoise_option, value="real", background='lightblue')
real_denoise_rb.pack(side='left', padx=5)

execute_denoise_button = ttk.Button(
    main_frame, 
    text="MPPCA Denoise", 
    command=execute_denoise, 
    style='Large.TButton', 
    width=30
)
execute_denoise_button.grid(row=19, column=1, padx=(10, 0))  # Adjust the row and column as needed

# Separator after denoise section
ttk.Separator(main_frame, orient='horizontal').grid(row=20, columnspan=5, sticky="ew")

# Process Flow Selection
tk.Label(main_frame, text="Select processing flow:").grid(row=21, column=0, sticky='w')
selected_flow = tk.StringVar(value="concat_degibbs")

# Internal frame for process flow radio buttons
radio_button_frame = tk.Frame(main_frame)
radio_button_frame.grid(row=21, column=1, sticky='w')

# Radio Buttons for Process Flow
rb1 = tk.Radiobutton(radio_button_frame, text="Concat → Degibbs", variable=selected_flow, value="concat_degibbs", background='lightblue')
rb1.pack(side='left', padx=5)

rb2 = tk.Radiobutton(radio_button_frame, text="Concat → Denoise → Degibbs", variable=selected_flow, value="concat_denoise_degibbs", background='lightblue')
rb2.pack(side='left', padx=5)


execute_degibbs_button = ttk.Button(
    main_frame, 
    text="Gibbs Ringing Removal", 
    command=execute_degibbs, 
    style='Large.TButton', 
    width=30
)
execute_degibbs_button.grid(row=22, column=1, padx=(10, 0))  # Adjust the row and column as needed

# Separator after degibbs section
ttk.Separator(main_frame, orient='horizontal').grid(row=23, columnspan=5, sticky="ew")

# Execute TopUp Button
top_up_button = ttk.Button(main_frame, text="TopUp Correction", command=execute_topup, style='Large.TButton', width=30)
top_up_button.grid(row=24, column=1, padx=(10, 0))

# Separator after TopUp section
ttk.Separator(main_frame, orient='horizontal').grid(row=25, columnspan=5, sticky="ew")

# Execute Generate Masks Button
execute_generate_masks_button = ttk.Button(
    main_frame, 
    text="Generate WM/Brain Masks", 
    command=execute_generate_masks, 
    style='Large.TButton', 
    width=30
)
execute_generate_masks_button.grid(row=26, column=1, padx=(10, 0))  # Adjust the row and column as needed

# Separator after Mask Generation section
ttk.Separator(main_frame, orient='horizontal').grid(row=27, columnspan=5, sticky="ew")

# Execute Eddy Button
execute_eddy_button = ttk.Button(
    main_frame, 
    text=" Eddy Current Correction", 
    command=execute_eddy, 
    style='Large.TButton', 
    width=30
)
execute_eddy_button.grid(row=28, column=1, padx=(10, 0))  # Adjust the row and column as needed

# Separator after Eddy section
ttk.Separator(main_frame, orient='horizontal').grid(row=29, columnspan=5, sticky="ew")

# Label for GNC option selection
tk.Label(main_frame, text="Select Scanner Option:").grid(row=30, column=0, sticky='w')

# Variable to store the selected GNC option
gnc_option = tk.StringVar(value="C2")

# Internal frame for GNC option radio buttons
gnc_option_radio_button_frame = tk.Frame(main_frame)  
gnc_option_radio_button_frame.grid(row=30, column=1, sticky='w')

# Radio Buttons for GNC Option
gnc_c1_rb = tk.Radiobutton(gnc_option_radio_button_frame, text="C1 Scanner", variable=gnc_option, value="C1", background='lightblue')
gnc_c1_rb.pack(side='left', padx=5)

gnc_c2_rb = tk.Radiobutton(gnc_option_radio_button_frame, text="C2 Scanner", variable=gnc_option, value="C2", background='lightblue')
gnc_c2_rb.pack(side='left', padx=5)

gnc_no_gnc_rb = tk.Radiobutton(gnc_option_radio_button_frame, text="No GNC", variable=gnc_option, value="no_gnc", background='lightblue')
gnc_no_gnc_rb.pack(side='left', padx=5)

# Execute GNC DWI Button
execute_gnc_dwi_button = ttk.Button(
    main_frame,
    text="Execute GNC DWI",
    command=execute_gnc_dwi,
    style='Large.TButton',
    width=30
)
execute_gnc_dwi_button.grid(row=31, column=1, padx=(10, 0))


# Separator after GNC section
ttk.Separator(main_frame, orient='horizontal').grid(row=32, columnspan=5, sticky="ew")

execute_interpolation_eddy_gnc_button = ttk.Button(
    main_frame,
    text="Combine Eddy GNC interpolation",
    command=execute_interpolation_eddy_gnc,  # Updated to use the new function
    style='Large.TButton',
    width=30
)
execute_interpolation_eddy_gnc_button.grid(row=33, column=1, padx=(10, 0))


# Separator after GNC section
ttk.Separator(main_frame, orient='horizontal').grid(row=34, columnspan=5, sticky="ew")

# Anat Process Directory Entry
tk.Label(main_frame, text="Anat Process Directory:").grid(row=35, column=0, sticky='w')
anat_process_dir_entry, anat_process_dir_entry_frame = make_horizontal_scrollable_entry(main_frame, width=50, height=1)
anat_process_dir_entry_frame.grid(row=35, column=1, sticky='ew')
anat_process_dir_entry.insert('1.0','/autofs/cluster/connectome2/Bay8_C2/bids/sub-011/anat_process')

# Image to Run GNC Directory Entry
tk.Label(main_frame, text="GNC Input Image:").grid(row=36, column=0, sticky='w')
image_to_run_gnc_dir_entry, image_to_run_gnc_dir_entry_frame = make_horizontal_scrollable_entry(main_frame, width=50, height=1)
image_to_run_gnc_dir_entry_frame.grid(row=36, column=1, sticky='ew')
image_to_run_gnc_dir_entry.insert('1.0','/autofs/cluster/connectome2/Bay8_C2/bids/sub-011/anat/sub-011_run-01_T1w.nii.gz')

# GNC Anat Option Selection
tk.Label(main_frame, text="Select Scanner Option:").grid(row=37, column=0, sticky='w')
gnc_anat_option = tk.StringVar(value="C2")  # Default value is "C2"

# Internal frame for GNC Anat option radio buttons
gnc_anat_radio_button_frame = tk.Frame(main_frame)  
gnc_anat_radio_button_frame.grid(row=37, column=1, sticky='w')

# Radio Buttons for GNC Anat Option
gnc_c1_anat_rb = tk.Radiobutton(gnc_anat_radio_button_frame, text="C1 Scanner", variable=gnc_anat_option, value="C1", background='lightblue')
gnc_c1_anat_rb.pack(side='left', padx=5)

gnc_c2_anat_rb = tk.Radiobutton(gnc_anat_radio_button_frame, text="C2 Scanner", variable=gnc_anat_option, value="C2", background='lightblue')
gnc_c2_anat_rb.pack(side='left', padx=5)

gnc_anat_no_gnc_rb = tk.Radiobutton(gnc_anat_radio_button_frame, text="No GNC", variable=gnc_anat_option, value="no_gnc", background='lightblue')
gnc_anat_no_gnc_rb.pack(side='left', padx=5)

# Execute GNC Anat Button
execute_gnc_anat_button = ttk.Button(
    main_frame,
    text="Execute GNC Anat",
    command=execute_gnc_anat,
    style='Large.TButton',
    width=30
)
execute_gnc_anat_button.grid(row=38, column=1, padx=(10, 0))

# Separator before buttons
ttk.Separator(main_frame, orient='horizontal').grid(row=39, columnspan=5, sticky="ew")


# Freesurfer Input Directory Entry
tk.Label(main_frame, text="FreeSurfer Input Image:").grid(row=40, column=0, sticky='w')
fsInput_entry, fsInput_entry_frame = make_horizontal_scrollable_entry(main_frame, width=50, height=1)
fsInput_entry_frame.grid(row=40, column=1, sticky='ew')
fsInput_entry.insert("1.0","/autofs/cluster/connectome2/Bay8_C2/bids/sub-011/anat/sub-011_run-02_T1w.nii.gz")
execute_recon_all_button = ttk.Button(
    main_frame, 
    text="Execute recon-all", 
    command=execute_recon_all, 
    style='Large.TButton', 
    width=30
)
execute_recon_all_button.grid(row=41, column=1, padx=(10, 0))  # Adjust the row and column as needed

# Separator before buttons
ttk.Separator(main_frame, orient='horizontal').grid(row=42, columnspan=5, sticky="ew")

# Button to execute mppca_noise
execute_mppca_noise_button = ttk.Button(
    main_frame, 
    text="Generate noise map from MP-PCA", 
    command=mppca_noise, 
    style='Large.TButton', 
    width=30
)
execute_mppca_noise_button.grid(row=43, column=1, padx=(10, 0))  # Adjust the row and column as needed
# Separator before buttons
ttk.Separator(main_frame, orient='horizontal').grid(row=44, columnspan=5, sticky="ew")

write_output_button = ttk.Button(
    main_frame, 
    text="Write Output to processed_dwi", 
    command=write_output_to_processed_dwi, 
    style='Large.TButton', 
    width=30
)
write_output_button.grid(row=45, column=1, padx=(10, 0))  # Adjust the row and column as needed
ttk.Separator(main_frame, orient='horizontal').grid(row=46, columnspan=5, sticky="ew")

# Function to copy text from the status_text widget
def copy_text(event=None):
    root.clipboard_clear()
    text = status_text.get("sel.first", "sel.last")
    root.clipboard_append(text)

# Function to paste text into the status_text widget
def paste_text(event=None):
    try:
        text = root.clipboard_get()
        status_text.insert("insert", text)
    except tk.TclError:
        pass


ttk.Separator(main_frame, orient='horizontal').grid(row=47, columnspan=5, sticky="ew")

# Configure the status area on the right side (column=2)
status_frame = ttk.Frame(main_frame)
status_frame.grid(row=0, column=2, rowspan=48, sticky='nsew', padx=5, pady=5)  # Adjust rowspan as needed
main_frame.rowconfigure(0, weight=1)  # This will make the status frame expand vertically

# Configure the status frame to use all available space
status_frame.columnconfigure(0, weight=1)
status_frame.rowconfigure(0, weight=1)

# Create a Text widget for status messages inside the frame with a specific width
status_text = tk.Text(status_frame, wrap='word', width=30)  # Width set to 30 characters
status_text.grid(row=0, column=0, sticky='nsew')

# Create a context menu for the status_text widget
context_menu = tk.Menu(status_text, tearoff=0)
context_menu.add_command(label="Copy", command=copy_text)
context_menu.add_command(label="Paste", command=paste_text)

# Function to display the context menu
def show_context_menu(event):
    try:
        context_menu.tk_popup(event.x_root, event.y_root)
    finally:
        context_menu.grab_release()
# Create a Scrollbar and attach it to status_text
scrollbar = ttk.Scrollbar(status_frame, orient='vertical', command=status_text.yview)
scrollbar.grid(row=0, column=1, sticky='ns')
status_text['yscrollcommand'] = scrollbar.set
# Bind the right-click event to the status_text widget
status_text.bind("<Button-3>", show_context_menu)


# Create a 'Clear Status' button and place it below the status_text
clear_button = ttk.Button(status_frame, text='Clear Status', command=lambda: status_text.delete(1.0, 'end'))
clear_button.grid(row=1, column=0, columnspan=2, pady=5, sticky='ew')


# Create a frame to hold the buttons
buttons_frame = ttk.Frame(main_frame)
buttons_frame.grid(row=47, column=0, columnspan=2, pady=(10, 0), sticky='ew')

# Button to remove the script
remove_script_button = ttk.Button(
    buttons_frame,
    text="Clear Script",
    command=lambda: remove_script(subj_process_dir_entry.get("1.0", 'end-1c').strip(), 'sub-' + subj_entry.get("1.0", 'end-1c').strip()),
    style='Large.TButton',
    width=20
)
remove_script_button.grid(row=0, column=0, padx=(0, 5), pady=(0, 5), sticky='ew')

# Button to append all commands to the script
append_all_commands_button = ttk.Button(
    buttons_frame,
    text="Append All to Script",
    command=append_all_commands_to_script,
    style='Large.TButton',
    width=30
)
append_all_commands_button.grid(row=0, column=1, padx=(5, 5), pady=(0, 5), sticky='ew')

# Button to execute commands from the script file
execute_script_button = ttk.Button(
    buttons_frame,
    text="Run script",
    command=execute_all_steps,  # Set the command to the execute_all_steps function
    style='Large.TButton',
    width=30
)
execute_script_button.grid(row=0, column=2, padx=(5, 0), pady=(0, 5), sticky='ew')

# Make sure the buttons_frame expands to fill the available space
buttons_frame.columnconfigure(0, weight=1)
buttons_frame.columnconfigure(1, weight=1)
buttons_frame.columnconfigure(2, weight=1)


root.mainloop()


# In[ ]:




