# gnc_anat_helper.py
import os
def gnc_anat_commands(subject, anat_process_dir, image_to_run_gnc_dir, gnc_anat_option):
    input_file = image_to_run_gnc_dir
    output_dir = f"{anat_process_dir}/s1_gnc"
    os.makedirs(output_dir, exist_ok=True)
    output_file = f"{output_dir}/{subject}_T1w.nii.gz"
    
    roothcp = '/space/scheherazade/2/users/qfan/tools/preproc/hcps_diff_prep_v2'
    script_dir = os.path.abspath(os.path.join(os.getcwd(), 'scripts'))
    
    script_name = "hcps_gnc_c2.sh" if gnc_anat_option == "C2" else "hcps_gnc.sh"
    
    cmd = (
        f"{roothcp}/{script_name} -i {input_file} -o {output_file} "
        "-interp spline"
    )
    return cmd

