import os
import subprocess

def topup_commands(base_dir, subject, selected_flow):
    input_dir = f"{base_dir}/{'s3_denoise_degibbs' if selected_flow == 'concat_denoise_degibbs' else 's3_degibbs'}"
    topup_dir = f"{base_dir}/s4_topup"
    os.makedirs(topup_dir, exist_ok=True)

    phase_encoding_file = f"{base_dir}/s1_concat/{subject}.phaseEncoding"
    dwi_file = f"{input_dir}/{subject}_dwi.nii.gz"
    pa_output_file = f"{topup_dir}/PA.nii.gz"
    ap_output_file = f"{topup_dir}/AP.nii.gz"
    b0s_output_file = f"{topup_dir}/b0s.nii.gz"
    
    # Command to get indices
    cmd_get_indices = """
    encoding_values=$(cat {phase_encoding_file})
    index_for_firstAP=$(echo "$encoding_values" | tr ' ' '\\n' | grep -n -m 1 '1' | cut -d: -f1)
    index_for_lastPA=$(echo "$encoding_values" | tr ' ' '\\n' | tac | grep -n -m 1 '-1' | cut -d: -f1)
    echo $index_for_firstAP $index_for_lastPA
    """

    cmd_pa = f"mrconvert {dwi_file} -coord 3 9 {pa_output_file} -force"
    cmd_ap = f"mrconvert {dwi_file} -coord 3 10 {ap_output_file} -force"
    cmd_mrcat = f"mrcat {ap_output_file} {pa_output_file} -axis 3 {b0s_output_file} -force"
    print(cmd_pa)
    # Remaining commands
    acqparam_path = "/autofs/cluster/connectome2/Bay8_C2/TractCaliber_script/topup_eddy/acqparams.txt"
    config_path = "/autofs/cluster/connectome2/Bay8_C2/TractCaliber_script/topup_eddy/b02b0_yixin_421.cnf"
    imain_path = f"{topup_dir}/b0s.nii.gz"
    out_path = f"{topup_dir}/b0s_topup"
    iout_path = f"{topup_dir}/b0s_topup"
    fField_path = f"{topup_dir}/b0s_topup_field"
    fWarp_path = f"{topup_dir}/b0s_topup_warp"
    topup_cmd = f"topup --imain={imain_path} --datain={acqparam_path} --config={config_path} --out={out_path} --iout={iout_path} --fout={fField_path} --dfout={fWarp_path}"

    return [cmd_get_indices, cmd_pa, cmd_ap, cmd_mrcat, topup_cmd]
