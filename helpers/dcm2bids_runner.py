import subprocess

def run_dcm2bids(subj, c2path, config, dcm_source):
    """
    Run the dcm2bids command with given parameters.

    Parameters:
    subj (str): The subject identifier, e.g., '011'.
    c2path (str): The path to the TractCaliber directory.
    config (str): The path to the dcm2bids config.json file.
    dcm_source (str): The source directory for the DICOM files.
    """
    output_path = c2path
    command = f"dcm_source={dcm_source}; subj={subj}; output_path={output_path}; dcm2bids -d $dcm_source -p $subj -o $output_path -c {config}"
    
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"dcm2bids command executed successfully for subject {subj}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running dcm2bids: {e}")

