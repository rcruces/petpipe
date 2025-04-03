#!/bin/bash
# ----------------------------------------------------------------
# This script is part of the PETPIPE pipeline
# This script runs the FASTSURFER pipeline for a given subject
# Usage: bash run_fastsurfer.sh <sub> <threads> <out>
# ----------------------------------------------------------------
#
# Usage: 
# bash run_fastsurfer.sh <sub> <ses> <bids_dir> <out>
# 
# Example:
# run_fastsurfer.sh HC010 01 /data_/mica3/MICA-PET/BIDS_mk6240/rawdata /data_/mica3/MICA-PET/BIDS_mk6240/derivatives
# 
# This is a functional draft, current paths are local or hardcoded!
sub=$1
ses=$2
bids_dir=$3
out=$4
threads=15
fs_license=/data_/mica1/01_programs/freesurfer-7.3.2/license.txt
FASTSURFER_IMG="/data/mica1/01_programs/fastsurfer/fastsurfer-cpu-v2.4.2.sif"
TMPDIR="/host/yeatman/local_raid/rcruces/tmp/tmpfiles"

# Handle variables
sub=${sub/sub-}
ses=${ses/ses-}
subject_id="sub-${sub}_ses-${ses}"

# Temporary directory path
tmp=${TMPDIR}

# MRI|IMG to process
t1=${bids_dir}/sub-${sub}/ses-${ses}/anat/${subject_id}_T1w.nii.gz

# Output directory
SUBJECTS_DIR=${out}/fastsurfer/
export SUBJECTS_DIR

# Create output directory if it does not exist
if [ ! -d "${SUBJECTS_DIR}" ]; then
    mkdir -p ${SUBJECTS_DIR}
fi

# Run singularity
singularity exec --writable-tmpfs --containall \
                      -B "${SUBJECTS_DIR}":/output \
                      -B "${tmp}":/tmpdir \
                      -B "${t1}":/tmpdir/${subject_id}_T1w.nii.gz \
                      -B "${fs_license}":/output/license.txt \
                      "${FASTSURFER_IMG}" \
                      /fastsurfer/run_fastsurfer.sh \
                      --fs_license /output/license.txt \
                      --vox_size min \
                      --t1 /tmpdir/${subject_id}_T1w.nii.gz \
                      --sid "${subject_id}" --sd /output \
                      --parallel --threads "${threads}" --device cpu --3T \
                      --no_hypothal