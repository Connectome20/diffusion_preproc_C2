# eddy_helper.py
from create_index_helper import create_index_file
def eddy_commands(subject, base_dir, selected_flow):
    input_dir_suffix = "s3_denoise_degibbs" if selected_flow == "concat_denoise_degibbs" else "s3_degibbs"
    eddy_dir_suffix = "s6_denoise_degibbs_eddy" if selected_flow == "concat_denoise_degibbs" else "s6_degibbs_eddy"
    eddy_dir = f"{base_dir}/{eddy_dir_suffix}"

    # Path where the index file will be created
    index_file = f"{eddy_dir}/index.txt"
    phase_encoding_file = f"{base_dir}/s1_concat/{subject}.phaseEncoding"

    # Call the function to create the index file
    create_index_file(phase_encoding_file, index_file)
    
    input_file = f"{base_dir}/{input_dir_suffix}/{subject}_dwi.nii.gz"
    mask_file = f"{base_dir}/s5_mask/brain_mask.nii.gz"
    acqp_file = "/autofs/cluster/connectome2/Bay8_C2/TractCaliber_script/topup_eddy/acqparams.txt"
    bvecs_file = f"{base_dir}/s1_concat/{subject}.bvec"
    bvals_file = f"{base_dir}/s1_concat/{subject}.bval_mod"
    topup_file = f"{base_dir}/s4_topup/b0s_topup"
    output_file = f"{eddy_dir}/{subject}_dwi_eddy"

    eddy_cuda_path = "/usr/pubsw/packages/fsl/6.0.7.3/bin/eddy_cuda10.2"  

    cmd = (
        f"{eddy_cuda_path} --imain={input_file} "
        f"--mask={mask_file} "
        f"--acqp={acqp_file} "
        f"--index={index_file} "
        f"--bvecs={bvecs_file} "
        f"--bvals={bvals_file} "
        f"--topup={topup_file} "
        f"--out={output_file} "
        f"--flm=cubic --interp=spline --niter=8 --data_is_shelled --verbose --dfields")
    
    return cmd

