#!/usr/bin/env python
# coding: utf-8
"""
This script is part of the PET pipeline for converting PET ecat data to BIDS format.
It processes PET images and organizes them into a BIDS-compliant directory structure.
The script requires the following arguments:
    -sub        : Subject identification.
    -ses        : Session.
    -pet_dir    : Input directory with raw PET images.
    -bids       : Path to BIDS directory ( . or FULL PATH)
    -micapipe   : Path to micapipe derivatives directory
    -tmpDir     : Specify location of temporary directory <path> (Default is /tmp)
    -force      : Will overwrite files

The script is intended for use by researchers and developers working with PET imaging data, particularly in the context of the MICA lab at McGill University.
It is part of a larger pipeline for processing and analyzing neuroimaging data.
This script is licensed under the MIT License. See the LICENSE file for details.
Copyright (c) 2025 MICA-MNI
"""
import argparse
import os
import glob
import shutil
import sys
import tempfile
import pandas as pd
from datetime import datetime
import ants

# Set the working directory to the script's location
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = os.path.dirname(script_dir)

# Argument Parsing
parser = argparse.ArgumentParser(add_help=True)
parser.add_argument("-sub", type=str, required=True, help="Subject identification")
parser.add_argument("-ses", type=str, required=True, help="Session")
parser.add_argument("-bids", dest="bids_dir", type=str, required=True, help="Path to BIDS directory ( . or FULL PATH)")
parser.add_argument("-pet_str", dest="pet_str", type=str, required=False, help="String to identify the PET image in the BIDS directory")
parser.add_argument("-pet_ref", dest="pet_ref", type=str, required=False, help="Image in PET space to be used as reference for registration")
parser.add_argument("-T1w_str", dest="T1w_str", type=str, required=False, help="String to identify the T1w image in the BIDS directory")
parser.add_argument("-surf_dir", dest="micapipe_dir", type=str, required=False, help="Path to the surface directory (freesurfer or fastsurfer)")
parser.add_argument("-tmpDir", type=str, default="/tmp", help="Specify location of temporary directory (default: /tmp)")
parser.add_argument("-force", action="store_true", help="Overwrite files")
args = parser.parse_args()

# Validate mandatory arguments
if not all([args.sub, args.ses, args.bids]):
    print("Error: One or more mandatory arguments are missing.")
    parser.print_help()
    sys.exit(1)

# Normalize paths and variables
session = f"{args.ses.replace('ses-', '')}"
subject = f"{args.sub.replace('sub-', '')}"
bids_dir = os.path.realpath(args.bids_dir)
subject_dir = os.path.join(f"{bids_dir}/sub-{subject}/ses-{session}")

# Check if the pet string is provided
if args.pet_str == False:
    pet_trc = glob.glob(os.path.join(f"{subject_dir}/pet/sub-{subject}_ses-{session}_*trc-*_pet.nii.gz"))
else:
    pet_trc = glob.glob(os.path.join(f"{subject_dir}/pet/sub-{subject}_ses-{session}_{args.pet_str}.nii.gz"))

# Check if the T1w string is provided
if args.T1w_str == False:
    t1w = glob.glob(os.path.join(f"{subject_dir}/anat/sub-{subject}_ses-{session}_*T1w*.nii.gz"))
else:
    t1w = glob.glob(os.path.join(f"{subject_dir}/anat/sub-{subject}_ses-{session}_{args.T1w_str}.nii.gz"))

# If the reference is proved pet_ref is __self__ otherwise is the pet_trc
if args.pet_ref == False:
    pet_ref = pet_trc
else:
    pet_ref = glob.glob(os.path.join(f"{subject_dir}/pet/sub-{subject}_ses-{session}_{args.pet_ref}.nii.gz"))
    # Check if the pet reference exists
    if not pet_ref:           
        print(f"Error: The reference image {args.pet_ref} does not exist in the directory {subject_dir}/pet")
        sys.exit(1)

print("\n-------------------------------------------------------------")
print("         PET pipeline - Processing")
print("-------------------------------------------------------------")
print(f"Subject: {subject}")
print(f"Session: {session}")
print(f"BIDS subject directory: {subject_dir}")
print(f"PET tracer: {pet_trc}")
print(f"T1w image: {t1w}")
print(f"Reference image: {pet_ref}")
print("-------------------------------------------------------------\n\n")

tmpDir = os.path.realpath(args.tmpDir) if args.tmpDir else tempfile.mkdtemp()

# Set default values
tmpDir = tempfile.mkdtemp() if not args.tmpDir else os.path.realpath(args.tmpDir)
print(f"Temporary Directory: {tmpDir}")

# Timer & beginning
import time
start_time = time.time()

# Print today's date in mm.dd.yyyy format
today=datetime.today().strftime('%m.%d.%Y')

# Make Subject Directory
os.makedirs(subject_dir, exist_ok=True)
os.makedirs(os.path.join(subject_dir, "anat"), exist_ok=True)
os.makedirs(os.path.join(subject_dir, "pet"), exist_ok=True)

# -----------------------------------------------------------------------------------
# Computing AVERAGE of if the PET image is 4D 

# -----------------------------------------------------------------------------------
# Register the PET image to the T1w image 

# Registration QC

# -----------------------------------------------------------------------------------
# Register the fsT1w image to T1w, fs: {freesurfer or fastsurfer}

# -----------------------------------------------------------------------------------
# Noise estimation

# -----------------------------------------------------------------------------------
# Calculate the Standarized uptake value ratio
# methods = {compositeROI, cerebellarGM, brainsteam} 

# -----------------------------------------------------------------------------------
# Calculate probabilistic gray matter mask (ARTROPOS)
# https://antspyx.readthedocs.io/en/latest/ants.segmentation.html
# https://antspyx.readthedocs.io/en/latest/ants.segmentation.html#module-ants.segmentation.atropos
ants.segmentation.atropos.atropos(a, x, i='Kmeans[3]', m='[0.2,1x1]', c='[5,0]', priorweight=0.25, **kwargs)

# -----------------------------------------------------------------------------------
# Partial volume correction
# methods = {MG, GMprob} MG:Muller-Gartner
echo "Performing PVC"
for norm in cerebellarGM compositeROI; do
	/host/fladgate/local_raid/jack/programs/scripts/anaconda3/bin/petpvc -i ${out_dir}/ses-${ses}/tmp/sub-${subj}_ses-${ses}_MK6240_norm_${norm}_nativepro.nii.gz \
	-m ${out_dir}/ses-${ses}/tmp/sub-${subj}_ses-${ses}_tissue_mask.nii.gz \
	-o ${out_dir}/ses-${ses}/pet/sub-${subj}_ses-${ses}_MK6240_norm_${norm}_PVC-MG_nativepro.nii.gz \
	--pvc MG -x 2.4 -y 2.4 -z 2.4
done

# -----------------------------------------------------------------------------------
# Capture the end time
end_time = time.time()  # End time in seconds (wall time)

# Calculate the time difference in seconds
time_difference = end_time - start_time

# Convert the time difference to minutes
time_difference_minutes = time_difference / 60

# Format the time difference to 3 decimal places
formatted_time = f"{time_difference_minutes:.3f}"

# Print the result with some colored output (for terminal)
print("----------------------------------------------------------------------------")
print(f"Ecat to BIDS running time: \033[38;5;220m {formatted_time} minutes \033[38;5;141m")
