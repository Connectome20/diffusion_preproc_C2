import sys
directory_path = "/autofs/space/linen_001/users/Yixin/TractCaliber"
sys.path.append(directory_path)

def dcm2bids_command(subject_id, c2path, config, dcm_source):
    cmd = f"python3 -c 'from helpers.dcm2bids_runner import run_dcm2bids; run_dcm2bids(\"{subject_id}\", \"{c2path}\", \"{config}\", \"{dcm_source}\")'"
    return cmd

def export_diffusion_parameters_command(subject_id, subj_raw_dir):
    cmd = f"python3 -c 'from helpers.diffusion_parameters_exporter import export_diffusion_parameters; export_diffusion_parameters(\"{subject_id}\", \"{subj_raw_dir}\")'"
    return cmd

def concatenate_dwi_data_command(subj_raw_dir, subject, subj_process_dir):
    cmd = f"python3 -c 'from helpers.concat_dwis import concatenate_dwi_data; concatenate_dwi_data(\"{subj_raw_dir}\", \"{subject}\", \"{subj_process_dir}\")'"
    return cmd

