# generate_masks_helper.py
import os

def generate_masks_commands(subject, base_dir):
    topup_dir = f"{base_dir}/s4_topup"
    mask_dir = f"{base_dir}/s5_mask"
    os.makedirs(mask_dir, exist_ok=True)

    topup_result = f"{topup_dir}/b0s_topup.nii.gz"
    topup_mean = f"{mask_dir}/b0s_topup_mean.nii.gz"
    synthseg_output = f"{mask_dir}/b0s_topup_mean_synthseg.nii.gz"
    wm_temp = f"{mask_dir}/wm_temp.nii.gz"
    wm_mask = f"{mask_dir}/wm.nii.gz"
    brain_mask_temp = f"{mask_dir}/brain_mask_temp.nii.gz"
    brain_mask = f"{mask_dir}/brain_mask.nii.gz"

    cmds = [
        f"export FREESURFER_HOME=/usr/local/freesurfer/7.4.1",        f"export FSFAST_HOME=/usr/local/freesurfer/7.4.1/fsfast",        f"export SUBJECTS_DIR=/usr/local/freesurfer/7.4.1/subjects",        f"export MNI_DIR=/usr/local/free-surfer/7.4.1/mni",        f"source $FREESURFER_HOME/SetUpFreeSurfer.sh",
        f"mrmath {topup_result} mean {topup_mean} -axis 3 -force",
        f"mri_synthseg --i {topup_mean} --o {synthseg_output}",
        f"mrcalc {synthseg_output} 2 -eq {synthseg_output} 41 -eq -add {wm_temp} -force",
        f"mrgrid {wm_temp} regrid -template {topup_mean} {wm_mask} -interp nearest -force",
        f"mrcalc {synthseg_output} 0 -gt {brain_mask_temp} -force",
        f"mrgrid {brain_mask_temp} regrid -template {topup_mean} {brain_mask} -interp nearest -force"
    ]

    return cmds, [wm_temp, brain_mask_temp]

