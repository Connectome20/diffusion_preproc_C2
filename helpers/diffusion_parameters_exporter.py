import json
import os
import re
import nibabel as nib

def export_diffusion_parameters(subject_id, data_directory):
    """
    Export diffusion parameters to corresponding files based on DWI JSON data.
    The output files will have values repeated to match the length of the .bval file.

    Parameters:
    subject_id (str): The subject identifier, e.g., '011'.
    data_directory (str): The directory path where the subject's DWI files are located.
    """
    def read_bval_file(file_path):
        """Read b-values from a file and return a list of b-values."""
        with open(file_path, 'r') as file:
            return file.read().split()

    def create_value_file(file_path, values):
        """Create a file with a list of values."""
        with open(file_path, 'w') as file:
            file.writelines(f"{value}\n" for value in values)

    def extract_values_from_json(json_file_path):
        """Extract phase encoding, diffusion time, and pulse width values from a JSON file."""
        if not os.path.exists(json_file_path):
            return '0', '0', '0'

        with open(json_file_path, 'r') as file:
            data = json.load(file)

        pe_direction = data.get('PhaseEncodingDirection', '')
        series_desc = data.get('SeriesDescription', '')

        pe_value = '1' if pe_direction == 'j-' else '-1' if pe_direction == 'j' else '0'

        d_match = re.search(r'd(\d+)', series_desc)
        d_value = d_match.group(1) if d_match else '0'

        D_match = re.search(r'D(\d+)', series_desc)
        D_value = D_match.group(1) if D_match else '0'

        return d_value, D_value, pe_value


    # Process files
    for file_name in os.listdir(data_directory):
        if file_name.startswith(f"sub-{subject_id}") and file_name.endswith('.json'):
            base_file_name = file_name[:-5]  # Remove .json extension
            nifti_path = os.path.join(data_directory, base_file_name + '.nii.gz')
            bval_path = os.path.join(data_directory, base_file_name + '.bval')
            bvec_path = os.path.join(data_directory, base_file_name + '.bvec')
            json_path = os.path.join(data_directory, file_name)
            
            if not os.path.exists(bval_path) or not os.path.exists(bvec_path):
                # Process the .nii.gz file
                if os.path.exists(nifti_path):
                    nifti_img = nib.load(nifti_path)
                    n_volumes = nifti_img.shape[-1]  # Get the 4th dimension

                    # Write .bval and .bvecs files
                    zeros = '0 ' * n_volumes
                    with open(bval_path, 'w') as bval_file:
                        bval_file.write(zeros.strip())

                    with open(bvec_path, 'w') as bvecs_file:
                        for _ in range(3):  # x, y, and z components
                            bvecs_file.write(' '.join(['0'] * n_volumes) + '\n')
                  # Write .diffusionTime, .pulseWidth, .phaseEncoding files
                    diffusion_time_values = ['30'] * n_volumes
                    pulse_width_values = ['6'] * n_volumes
                    _, _, pe_value = extract_values_from_json(os.path.join(data_directory, file_name))
                    phase_encoding_values = [pe_value] * n_volumes

                    create_value_file(os.path.join(data_directory, base_file_name + '.diffusionTime'), diffusion_time_values)
                    create_value_file(os.path.join(data_directory, base_file_name + '.pulseWidth'), pulse_width_values)
                    create_value_file(os.path.join(data_directory, base_file_name + '.phaseEncoding'), phase_encoding_values)

            else:
                bvals = read_bval_file(bval_path)
                d_value, D_value, pe_value = extract_values_from_json(json_path)

                # Repeat the values to match the length of the .bval file
                pulse_width_values = [d_value] * len(bvals)
                diffusion_time_values = [D_value] * len(bvals)
                phase_encoding_values = [pe_value] * len(bvals)

                # Create output files with the repeated values
                create_value_file(bval_path.replace('.bval', '.pulseWidth'), pulse_width_values)
                create_value_file(bval_path.replace('.bval', '.diffusionTime'), diffusion_time_values)
                create_value_file(bval_path.replace('.bval', '.phaseEncoding'), phase_encoding_values)

    print(f"Exported diffusion parameters for subject {subject_id}.")

