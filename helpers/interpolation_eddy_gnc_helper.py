import os
import subprocess
import nibabel as nib
import numpy as np
import shutil
from numpy import gradient

def evaluate_jacobian(field_data, pixdim):
    siemens_max_det = 10
    dFxdx, dFxdy, dFxdz = gradient(field_data[..., 0], pixdim[0], pixdim[1], pixdim[2])
    dFydx, dFydy, dFydz = gradient(field_data[..., 1], pixdim[0], pixdim[1], pixdim[2])
    dFzdx, dFzdy, dFzdz = gradient(field_data[..., 2], pixdim[0], pixdim[1], pixdim[2])
    jacdet = np.abs(dFxdx * dFydy * dFzdz - dFxdx * dFydz * dFzdy - dFxdy * dFydx * dFzdz 
                    + dFxdy * dFydz * dFzdx + dFxdz * dFydx * dFzdy - dFxdz * dFydy * dFzdx)
    jacdet[jacdet > siemens_max_det] = siemens_max_det
    return jacdet

def interpolation_eddy_gnc(subject_id, base_dir, selected_flow):
    subject = f'sub-{subject_id}'
    input_dir_suffix = "s3_denoise_degibbs" if selected_flow == "concat_denoise_degibbs" else "s3_degibbs"
    eddy_dir_suffix = "s6_denoise_degibbs_eddy" if selected_flow == "concat_denoise_degibbs" else "s6_degibbs_eddy"
    input_file = f"{base_dir}/{input_dir_suffix}/{subject}_dwi.nii.gz"
    eddy_dir = f"{base_dir}/{eddy_dir_suffix}"
    gnc_dir = f"{base_dir}/s7_gnc"
    apply_dir = f"{base_dir}/s8_applywarp"
    os.makedirs(apply_dir, exist_ok=True)

    fpGncfield = f"{gnc_dir}/{subject}_dwi_eddy_1_deform_grad_rel.nii.gz"
    eddy_warps = sorted([f for f in os.listdir(eddy_dir) if 'eddy_displacement_fields' in f], key=lambda x: int(x.split('.eddy_displacement_fields.')[-1].split('.')[0]))

    img_4d = nib.load(input_file)
    data_4d = img_4d.get_fdata()
    
    for jj in range(data_4d.shape[3]):
        img_3d_data = data_4d[:, :, :, jj]
        img_3d = nib.Nifti1Image(img_3d_data, affine=img_4d.affine)
        fpVol = os.path.join(apply_dir, f'imgvol{str(jj).zfill(4)}.nii.gz')
        nib.save(img_3d, fpVol)
        
        fpWarpEddy = os.path.join(eddy_dir, eddy_warps[jj])
        fpWarpComb = os.path.join(apply_dir, f'warpcomb{str(jj).zfill(4)}.nii.gz')
        fpRsp = os.path.join(apply_dir, f'rsp_imgvol{str(jj).zfill(4)}.nii.gz')
        
        subprocess.run(f'convertwarp -o {fpWarpComb} -r {fpVol} --warp1={fpWarpEddy} --warp2={fpGncfield} --rel --absout -v', shell=True)
        subprocess.run(f'applywarp -i {fpVol} -r {fpVol} -o {fpRsp} -w {fpWarpComb} --interp=spline --datatype=float', shell=True)
        
        data = nib.load(fpWarpComb).get_fdata()
        jacdet = evaluate_jacobian(data, img_4d.header.get_zooms()[:3])
        jac_img = nib.Nifti1Image(jacdet, affine=img_4d.affine)
        fpJac = os.path.join(apply_dir, f'jac{str(jj).zfill(4)}.nii.gz')
        nib.save(jac_img, fpJac)
        
        subprocess.run(f'fslmaths {fpRsp} -mul {fpJac} {fpRsp}', shell=True)

    output_file = f"{base_dir}/s8_final/{subject}_dwi.nii.gz"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    cmd_fslmerge = f'fslmerge -t {output_file} ' + ' '.join([os.path.join(apply_dir, f'rsp_imgvol{str(jj).zfill(4)}.nii.gz') for jj in range(data_4d.shape[3])])
    subprocess.run(cmd_fslmerge, shell=True)

    shutil.rmtree(apply_dir)
    print(f"Interpolation and Jacobian correction completed for subject {subject}")

# Example Usage
#subject_id = '018'
#base_dir = '/autofs/cluster/connectome2/bids/sub-018/dwi_process'
#selected_flow = 'concat_degibbs'
#interpolation_eddy_gnc(subject_id, base_dir, selected_flow)
