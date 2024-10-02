import os
import subprocess

def degibbs_commands(subject, base_dir, selected_flow):
    # Determine the input and output sub-folders based on the selected flow
    if selected_flow == "concat_denoise_degibbs":
        output_dir_suffix = "s3_denoise_degibbs"
        input_dir_suffix = "s2_denoise"
    else:
        output_dir_suffix = "s3_degibbs"
        input_dir_suffix = "s1_concat"
    
    # Construct input and output directory paths
    input_dir = f"{base_dir}/{input_dir_suffix}"
    output_dir = f"{base_dir}/{output_dir_suffix}"
    
    # Construct input and output file paths
    input_file = f"{input_dir}/{subject}_dwi.nii.gz"
    output_file = f"{output_dir}/{subject}_dwi.nii.gz"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Degibbs command
    cmd = f"mrdegibbs {input_file} {output_file} -force"
    return cmd

