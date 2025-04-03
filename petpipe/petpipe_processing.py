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
import nibabel as nib
import numpy as np
import ants

# Load utilities functions from utils.py
from utils import *

# Set the working directory to the script's location
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = os.path.dirname(script_dir)

# Argument Parsing
parser = argparse.ArgumentParser(add_help=True)
parser.add_argument("-sub", type=str, required=True, help="Subject identification")
parser.add_argument("-ses", type=str, required=True, help="Session")
parser.add_argument("-bids", dest="bids_dir", type=str, required=True, help="Path to BIDS directory ( . or FULL PATH)")
parser.add_argument("-out", dest="out_dir", type=str, required=True, help="Path to derivatives directory ( . or FULL PATH)")
parser.add_argument("-surf_dir", dest="micapipe_dir", type=str, required=True, help="Path to the Subject surface directory (freesurfer or fastsurfer)")
parser.add_argument("-pet_str", dest="pet_str", type=str, required=False, help="String to identify the PET image in the BIDS directory")
parser.add_argument("-pet_ref", dest="pet_ref", type=str, required=False, help="Image in PET space to be used as reference for registration")
parser.add_argument("-T1w_str", dest="T1w_str", type=str, required=False, help="String to identify the T1w image in the BIDS directory")
parser.add_argument("-surf_recon", type=str, dest="surf_recon", default="freesurfer", help="Software used for surface reconstruction (freesurfer or fastsurfer)")
parser.add_argument("-threads", type=int, dest="threads", default=6, help="Number of threads to use for processing (default: 6)")
parser.add_argument("-tmpDir", type=str, default="/tmp", help="Specify location of temporary directory (default: /tmp)")
parser.add_argument("-force", action="store_true", help="Overwrite files")
args = parser.parse_args()

# Validate mandatory arguments
if not all([args.sub, args.ses, args.bids, args.surf_dir, args.out]):
    print("Error: One or more mandatory arguments are missing.")
    parser.print_help()
    sys.exit(1)

# Normalize paths and variables
session = f"{args.ses.replace('ses-', '')}"
subject = f"{args.sub.replace('sub-', '')}"
bids_dir = os.path.realpath(args.bids_dir)
out_dir = os.path.realpath(f"{args.out_dir}/petpipe_beta")
surf_dir = os.path.realpath(args.surf_dir)
subject_dir = os.path.join(f"{bids_dir}/sub-{subject}/ses-{session}")
surf_recon = args.surf_recon
threads = args.threads

# -------------------------------------------------------------------------
# >>>>>> Future change the imputs to be handle with class BIDSpetName or BIDSName
# Check if the pet string is provided
if args.pet_str == False:
    pet_trc = glob.glob(os.path.join(f"{subject_dir}/pet/sub-{subject}_ses-{session}_*trc-*_pet.nii.gz"))
else:
    pet_trc = glob.glob(os.path.join(f"{subject_dir}/pet/sub-{subject}_ses-{session}_{args.pet_str}.nii.gz"))
trc = pet_trc.split("trc-")[1].split("_")[0]

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

# Check if surf_dir
if not os.path.isdir(surf_dir):
    error(f"The surface directory {surf_dir} does not exist")
# Check if the output directory exists
if os.path.isdir(out_dir):
    t1w_fs = glob.glob(f"{surf_dir}/mri/orig.mgz")
    parc_fs = glob.glob(f"{surf_dir}/mri/aparc+aseg.nii.gz")
    lh_pial = glob.glob(f"{surf_dir}/surf/lh.pial")
    rh_pial = glob.glob(f"{surf_dir}/surf/rh.pial")
    lh_white = glob.glob(f"{surf_dir}/surf/lh.white")
    rh_white = glob.glob(f"{surf_dir}/surf/rh.white")
    lh_thickness = glob.glob(f"{surf_dir}/surf/lh.thickness")
    rh_thickness = glob.glob(f"{surf_dir}/surf/rh.thickness")

print(f"\n{bcolors.TEAL}-------------------------------------------------------------")
print("         PET pipeline - Processing")
print("-------------------------------------------------------------{bcolors.ENDC}")
print(f"   {bcolors.TEAL}Subject:{bcolors.ENDC} {subject}")
print(f"   {bcolors.TEAL}Session:{bcolors.ENDC} {session}")
print(f"   {bcolors.TEAL}BIDS subject directory:{bcolors.ENDC} {subject_dir}")
print(f"   {bcolors.TEAL}Output directory:{bcolors.ENDC} {out_dir}")
print(f"   {bcolors.TEAL}Surface directory:{bcolors.ENDC} {surf_dir}")
print(f"   {bcolors.TEAL}Surface recon:{bcolors.ENDC} {surf_recon}")
print(f"   {bcolors.TEAL}PET tracer:{bcolors.ENDC} {trc}")
print(f"   {bcolors.TEAL}T1w image:{bcolors.ENDC} {t1w}")
print(f"   {bcolors.TEAL}Reference image:{bcolors.ENDC} {pet_ref}")
print(f"   {bcolors.TEAL}Threads:{bcolors.ENDC} {threads}")

# Set default values
tmpDir = tempfile.mkdtemp() if not args.tmpDir else os.path.realpath(args.tmpDir)
print(f"Temporary Directory: {tmpDir}")

# Timer & beginning
import time
start_time = time.time()

# Print today's date in mm.dd.yyyy format
today=datetime.today().strftime('%m.%d.%Y')

# Make Subject Directory
os.makedirs(out_dir, exist_ok=True)
dirs = ["anat", "pet", "xfm", "surf"]
for d in dirs:
    os.makedirs(os.path.join(out_dir, d), exist_ok=True)

# -----------------------------------------------------------------------------------
# Computing AVERAGE of if the PET image is 4D 
pet_avg = compute_average_4D_image(pet_trc)

# Save the NIfTI image
pet_avg_file = BIDSderivativeName(sub=subject, ses=session, desc="average", trc=trc, suffix="pet")
nib.save(pet_avg, f"{out_dir}/pet/{pet_avg_file}.nii.gz")

# -----------------------------------------------------------------------------------
# Register the PET image to the T1w image 
fixed = ants.image_read(t1w)
moving = ants.image_read(pet_avg)
reg_name = f"{out_dir}/xfm/sub-{subject}_ses-{session}_from-pet_to-T1w_trc-{trc}_"
transforms = ants.registration(fixed=fixed, moving=moving, type_of_transform="Affine", outprefix=reg_name, 
                               verbose=False, initial_transform=None,interpolator="nearestNeighbor", dimension=3, num_threads=threads)

# The result of the registration is a dictionary containing, among other keys:
registered = ants.apply_transforms(fixed=fixed, moving=moving, transformlist=transforms["fwdtransforms"], interpolator="nearestNeighbor")

# Save the registered moving image
pet_file=BIDSderivativeName(sub=subject, ses=session, space="T1w", desc="average", trc=trc, suffix="pet")
ants.image_write(registered, f"{out_dir}/pet/{pet_file}.mat")

# Registration QC

# -----------------------------------------------------------------------------------
# Register the fsT1w image to T1w, fs: {freesurfer or fastsurfer}
moving = ants.image_read(t1w_fs)
reg_name = f"{out_dir}/xfm/sub-{subject}_ses-{session}_from-{surf_recon}_to-T1w_"
transforms = ants.registration(fixed=fixed, moving=moving, type_of_transform="Affine", outprefix=reg_name, 
                               verbose=False, initial_transform=None,interpolator="nearestNeighbor", dimension=3, num_threads=threads)

# The result of the registration is a dictionary containing, among other keys:
registered = ants.apply_transforms(fixed=fixed, moving=moving, transformlist=transforms["fwdtransforms"], interpolator="nearestNeighbor")

# Save the registered moving image
pet_file=BIDSderivativeName(sub=subject, ses=session, space="T1w", desc="average", trc=trc, suffix="T1w")
ants.image_write(registered, f"{out_dir}/pet/{pet_file}.mat")

# Registration QC

# -----------------------------------------------------------------------------------
# Copy parcellation from freesurfer/fastsurfer to the output directory

# -----------------------------------------------------------------------------------
# Noise estimation

# -----------------------------------------------------------------------------------
# Calculate probabilistic gray matter mask (ARTROPOS)
# https://antspyx.readthedocs.io/en/latest/ants.segmentation.html
# https://antspyx.readthedocs.io/en/latest/ants.segmentation.html#module-ants.segmentation.atropos
ants.segmentation.atropos.atropos(a, x, i='Kmeans[3]', m='[0.2,1x1]', c='[5,0]', priorweight=0.25, **kwargs)

# -----------------------------------------------------------------------------------
# Calculate the Standarized uptake value ratio
# methods = {compositeROI, cerebellarGM, brainsteam} 

# -----------------------------------------------------------------------------------
# Partial volume correction
# methods = {MG, GMprob} MG:Muller-Gartner
info("Performing Partial volume correction")
for norm in [cerebellarGM compositeROI]; do
	command= "petpvc -i ${out_dir}/ses-${ses}/tmp/sub-${subj}_ses-${ses}_MK6240_norm_${norm}_nativepro.nii.gz \
	-m ${out_dir}/ses-${ses}/tmp/sub-${subj}_ses-${ses}_tissue_mask.nii.gz \
	-o ${out_dir}/ses-${ses}/pet/sub-${subj}_ses-${ses}_MK6240_norm_${norm}_PVC-MG_nativepro.nii.gz \
	--pvc MG -x 2.4 -y 2.4 -z 2.4"

# -----------------------------------------------------------------------------------
# Map the PET volume to the cortical surface

# -----------------------------------------------------------------------------------
# Smooth PET on cortical surface

# -----------------------------------------------------------------------------------
# Convert mgh to gii cortical thickness into derivatives
lh_thickness_file = BIDSderivativeName(sub=subject, ses=session, surf="fsnative", label="thickness", hemi="L", suffix="surf")
rh_thickness_file = BIDSderivativeName(sub=subject, ses=session, surf="fsnative", label="thickness", hemi="R", suffix="surf")
convert_freesurfer_to_gifti(lh_thickness, f"{out_dir}/surf/{lh_thickness_file}.shape.gii")
convert_freesurfer_to_gifti(rh_thickness, f"{out_dir}/surf/{rh_thickness_file}.shape.gii")

# -----------------------------------------------------------------------------------
# Smooth cortical thickness on surface
# wb_command = f"wb_command -metric-smoothing {lh_thickness_file}.shape.gii {lh_thickness_file}.shape.gii 5 0.5"
# wb_command = f"wb_command -metric-smoothing {rh_thickness_file}.shape.gii {rh_thickness_file}.shape.gii 5 0.5"

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
