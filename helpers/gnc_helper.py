# gnc_helper.py
import os
def gnc_commands(subject, base_dir, selected_flow, gnc_option):
    eddy_dir_suffix = "s6_denoise_degibbs_eddy" if selected_flow == "concat_denoise_degibbs" else "s6_degibbs_eddy"
    eddy_dir = f"{base_dir}/{eddy_dir_suffix}"
    input_file = f"{eddy_dir}/{subject}_dwi_eddy.nii.gz"
    output_dir = f"{base_dir}/s7_gnc"
    os.makedirs(output_dir, exist_ok=True)
    output_file = f"{output_dir}/{subject}_dwi.nii.gz"
    
    roothcp = '/space/scheherazade/2/users/qfan/tools/preproc/hcps_diff_prep_v2'
    # Determine the path to the 'scripts' directory    #script_dir = os.path.abspath(os.path.join(os.getcwd(), 'scripts'))
    script_name = "hcps_gnc_c2.sh" if gnc_option == "C2" else "hcps_gnc.sh"
        cmd = (        f"{roothcp}/{script_name} -i {input_file} -o {output_file} "        "-interp spline"    )
    return cmd

