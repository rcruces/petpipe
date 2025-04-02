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
import json
import subprocess
import pandas as pd
from datetime import datetime

# Set the working directory to the script's location
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = os.path.dirname(script_dir)

# Argument Parsing
parser = argparse.ArgumentParser(add_help=True)
parser.add_argument("-sub", type=str, required=True, help="Subject identification")
parser.add_argument("-ses", type=str, required=True, help="Session")
parser.add_argument("-pet_dir", dest="pet_dir", type=str, required=True, help="Input directory with raw PET images")
parser.add_argument("-bids", dest="bids_dir", type=str, required=True, help="Path to BIDS directory ( . or FULL PATH)")
parser.add_argument("-micapipe", dest="micapipe_dir", type=str, required=False, help="Path to micapipe derivatives directory", default="/data_/mica3/BIDS_MICs/derivatives/micapipe_v0.2.0")
parser.add_argument("-tmpDir", type=str, default="/tmp", help="Specify location of temporary directory (default: /tmp)")
parser.add_argument("-force", action="store_true", help="Overwrite files")
args = parser.parse_args()

# Validate mandatory arguments
if not all([args.sub, args.pet_dir, args.bids_dir, args.ses, args.micapipe_dir]):
    print("Error: One or more mandatory arguments are missing.")
    parser.print_help()
    sys.exit(1)

# Normalize paths and variables
session = f"{args.ses.replace('ses-', '')}"
subject = f"{args.sub.replace('sub-', '')}"
pet_dir = os.path.realpath(args.pet_dir)
bids_dir = os.path.realpath(args.bids_dir)
micapipe_dir = os.path.realpath(args.micapipe_dir)
subject_dir = os.path.join(f"{bids_dir}/sub-{subject}/ses-{session}")
t1_files_glob = glob.glob(f"{micapipe_dir}/sub-{subject}/ses-01/anat/*_space-nativepro_T1w.json")

if not t1_files_glob:
    error(f"No T1w file found for subject {subject} in session ses-01.")
else:
    t1_files = os.path.splitext(t1_files_glob[0])[0]

print("\n-------------------------------------------------------------")
print("         PET pipeline - ECAT to BIDS conversion")
print("-------------------------------------------------------------")
print(f"Subject: {subject}")
print(f"Session: {session}")
print(f"Source directory: {pet_dir}")
print(f"BIDS subject directory: {subject_dir}")
print(f"micapipe directory: {micapipe_dir}")
print("-------------------------------------------------------------\n\n")

tmpDir = os.path.realpath(args.tmpDir) if args.tmpDir else tempfile.mkdtemp()

# Set default values
tmpDir = tempfile.mkdtemp() if not args.tmpDir else os.path.realpath(args.tmpDir)
print(f"Temporary Directory: {tmpDir}")

# Overwrite output directory if force is enabled
if args.force and os.path.exists(subject_dir):
    shutil.rmtree(subject_dir)

# Check inputs
if not os.path.exists(f"{t1_files}.json"):
    warning(f"Subject {subject}_{session} does NOT have a T1")
if not os.path.isdir(args.pet_dir):
    error(f"Input directory does not exist: {pet_dir}")
    sys.exit(1)
if not os.path.isdir(args.bids_dir):
    print(f"Output directory does not exist: {bids_dir}")
    sys.exit(1)
if os.path.isdir(subject_dir):
    error(f"Output directory already exists. Use -force to overwrite: {subject_dir}")
    sys.exit(1)

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
# Partial volume correction
# methods = {MG, GMprob} MG:Muller-Gartner

# Calculate probabilistic gray matter mask




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
