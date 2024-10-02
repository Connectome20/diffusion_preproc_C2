#!/bin/bash
#
# This is a shell script to perform rician noise floor corrected
# MP-PCA
#
# Dependencies: (1)MRtrix (2) FSL
#
# Creator: Kwok-Shing Chan @ MGH
# kchan2@mgh.harvard.edu
#
# Adopted from rician_correct_mppca.m by Hong-Hsi Lee 
# Date created: 5 October 2023
# Date edit: 1 December 2023
# Date edit: 30 January 2024 (replace 0 to a very small number 1e-10 to avoid division by zeros)
############################################################
set -e

# Check if FSL is in the PATH, if not then add it 
if [ -n "${PATH##*fsl*}" ] ; then
FSLDIR=/usr/pubsw/packages/fsl/6.0.1
. ${FSLDIR}/etc/fslconf/fsl.sh
PATH=${FSLDIR}/bin:${PATH}
export FSLDIR PATH
fi

# constructor
in_nii=''
out_nii=''
niter=3
mask_nii=''
nthreads=64

# Usage
print_usage() {
  printf "Example usage: sh $0 -i /path/input.nii.gz -o /path/output.nii.gz "
  echo ""
  echo "Options"
  echo "-i        Input NIFTI filename (.nii or .nii.gz)"
  echo "-o        Output NIFTI filename (.nii or .nii.gz)"
  echo "-n        (Optional) Number of iterations (default '-n 3')"
  echo "-m        (Optional) Input mask NIFTI file (.nii or .nii.gz)"
  echo "-c        (Optional) Number of threads for parallel processing (default '-nthreads 8')"
  echo "-h        Print this help"
  exit 1
}

# get input based on flags
while getopts ':hi:o:n:m:c:' flag; do
  case "${flag}" in
    i) in_nii="${OPTARG}" ;;
    o) out_nii="${OPTARG}" ;;
    n) niter=${OPTARG} ;;
    m) mask_nii="${OPTARG}" ;;
    c) nthreads="${OPTARG}" ;;
    h) print_usage
       exit 1 ;;
  esac
done

# check input file
if ! [ -f "${in_nii}" ]; then
echo "Cannot find input file. Please specify the input file using '-i' flag."
print_usage
exit 1
fi
# check output file
if [ -z "${out_nii}" ]; then
echo "Please specify the output filename using '-o' flag."
print_usage
exit 1
fi

# Define other output filename
in_basename=$(basename -- "${in_nii}")
ext_i="${in_basename#*.}"
in_basename="${in_basename%%.*}"
output_dir="$(dirname "${out_nii}")/"
out_basename=$(basename -- "${out_nii}")
ext_o="${out_basename#*.}"
out_basename="${out_basename%%.*}"

tmp_dir=${output_dir}temp_rician_corr_mppca/
sigma_nii=${tmp_dir}${out_basename}_sigma.nii

# create temporary directory for intermediate files
mkdir -p ${tmp_dir}

## Main
if [ "${ext_i}" == "nii.gz" ]; then
# uncompress input image to speed up computation
echo "Uncompressing input data..."
in_tmp_nii=${tmp_dir}${in_basename}.nii
gunzip -c ${in_nii} > ${in_tmp_nii}
else
in_tmp_nii=${in_nii}
fi
# temporary output file
out_tmp_nii=${tmp_dir}${out_basename}.nii

# pre-iteration processing
if [ -f "$mask_nii" ]; then
dwidenoise -noise ${sigma_nii} -mask ${mask_nii} ${in_tmp_nii} ${out_tmp_nii} -nthreads ${nthreads} -force
else
dwidenoise -noise ${sigma_nii} ${in_tmp_nii} ${out_tmp_nii} -nthreads ${nthreads} -force
fi

# run iterations
for ((i=1;i<=$niter;i++)); do

echo ""
echo "########## Iteration #${i} ##########"

p_over_sigma_pow_r_nii=${tmp_dir}${out_basename}_p_over_sigma_pow_r.nii
mrcalc ${out_tmp_nii} 0.0000000001 -max ${sigma_nii} -div -log 2.25 -mult -exp ${p_over_sigma_pow_r_nii} -force

q_nii=${tmp_dir}${out_basename}_q.nii
mrcalc ${p_over_sigma_pow_r_nii} 1.65 -add -log 2.25 -div -exp ${sigma_nii} -mult ${q_nii} -force

s_over_sigma_nii=${tmp_dir}${out_basename}_s_over_sigma.nii
mrcalc ${p_over_sigma_pow_r_nii} 1.12 -add ${p_over_sigma_pow_r_nii} 1.7 -add -div ${s_over_sigma_nii} -force

m_nii=${tmp_dir}${out_basename}_m.nii
mrcalc ${in_tmp_nii} ${q_nii} -subtract ${s_over_sigma_nii} -div ${out_tmp_nii} 0.0000000001 -max -add ${m_nii} -force

# use the user defined output filename at the last iteration
if [ ${i} == ${niter} ]; then
sigma_nii=${output_dir}${out_basename}_sigma.${ext_o}
out_tmp_nii=${out_nii}
fi

if [ -f "$maskfile" ]; then
dwidenoise -noise ${sigma_nii} -mask ${maskfile} ${m_nii} ${out_tmp_nii} -nthreads ${nthreads} -force
else
dwidenoise -noise ${sigma_nii} ${m_nii} ${out_tmp_nii} -nthreads ${nthreads} -force
fi

done

# replace NaN by 0
fslmaths ${out_nii} -nan ${out_nii}

# clean up
rm -rf ${tmp_dir}

echo "########## The processing is finished. ##########"

