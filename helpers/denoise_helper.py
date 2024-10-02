import os
import subprocess

def denoise_commands(subject, base_dir, denoise_option):
    input_file = f"{base_dir}/s1_concat/{subject}_dwi.nii.gz"
    output_dir = f"{base_dir}/s2_denoise"
    os.makedirs(output_dir, exist_ok=True)
    output_file = f"{output_dir}/{subject}_dwi.nii.gz"
    
    if denoise_option == "magnitude":
        cmd = f"sh denoise/rician_correct_mppca.sh -i {input_file} -o {output_file} -n 3"
    elif denoise_option == "real":
        cmd = f"dwidenoise {input_file} {output_file} -force"
    else:
        raise ValueError("Invalid denoise option selected.")
    
    return cmd

