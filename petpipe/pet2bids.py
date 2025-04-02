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
    -bids_validator: Run BIDS validator
The script creates a temporary directory for processing and cleans up after itself.
It also checks for the existence of required files and directories before proceeding.
The script is designed to be run from the command line and requires Python 3.x.
It is recommended to run this script in a controlled environment where the necessary dependencies are installed.
The script uses the argparse library for command-line argument parsing and the os, shutil, sys, and tempfile libraries for file and directory operations.
The script is intended for use by researchers and developers working with PET imaging data, particularly in the context of the MICA lab at McGill University.
It is part of a larger pipeline for processing and analyzing neuroimaging data.
This script is licensed under the MIT License. See the LICENSE file for details.
Copyright (c) 2025 MICA-MNI
"""
import argparse
import os
import sys
import glob
import shutil

import pandas as pd
from datetime import datetime

# Load utilities functions from utils.py
from utils import *

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
parser.add_argument("-bids_validator", action="store_true", help="Run BIDS validator")
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
print(f"micapipe directory: {micapipe_dir}\n")

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
info("Creating NIFTIS from source ECAT")
# Create the mk6240 NIFTI
# OPTIONAL json keys: {"InjectionTime", "MolarActivity_decay_corrected", "ScanTime"}
pet_image = BIDSpetName(trc="mk6240", sub=subject, ses=session, rec="acdyn").build()
convert_ecat_to_bids(f'{pet_dir}/*EM_4D_MC01.v', pet_image, f"{subject_dir}/pet", json=os.path.join(repo_dir, "files/subject_trc-MK6240_pet.json"))

# Create the mk6240 transmission
tx_image = BIDSpetName(sub=subject, ses=session, desc="LinearAtenuationMap").build()
convert_ecat_to_bids(f"{pet_dir}/Transmission/*TX.v", tx_image, f"{subject_dir}/pet")

# -----------------------------------------------------------------------------------
# Copy the T1w image to BIDS directory
t1_str = BIDSName(suffix="T1w", sub=subject, ses=session).build()

# Copy the files
shutil.copy2(f"{t1_files}.json", os.path.join(subject_dir, f"anat/{t1_str}.json"))
shutil.copy2(f"{t1_files}.nii.gz", os.path.join(subject_dir, f"anat/{t1_str}.nii.gz"))

# -----------------------------------------------------------------------------------
# Copy mandatory files for BIDS compliance
mandatory_files = ["CITATION.cff", "dataset_description.json", ".bidsignore", "participants.json", "trc-mk6240_rec-acdyn_pet.json", "README"]
for file in mandatory_files:
    source_path = os.path.join(repo_dir, "files", file)
    dest_path = os.path.join(bids_dir, file)
    shutil.copy2(source_path, dest_path)

# ----------------------------------------------------------------------------------
# Count number of gzipped NIfTI files in different directories
anat = len(glob.glob(os.path.join(subject_dir, "anat", "**", "*.nii.gz"), recursive=True))
pet = len(glob.glob(os.path.join(subject_dir, "pet", "**", "*.nii.gz"), recursive=True))

# Check if participants TSV file exists, create it if not
tsv_file = os.path.join(bids_dir, "participants_bic2bids.tsv")
if not os.path.isfile(tsv_file):
    # Create the header if the file does not exist
    header = ["subject_id", "date", "N.anat", "N.pet", "source", "user", "processing.time"]
    df = pd.DataFrame(columns=header)
    df.to_csv(tsv_file, sep='\t', index=False)

# Add subject info to participants.tsv
participants_tsv = os.path.join(bids_dir, "participants.tsv")
if not os.path.isfile(participants_tsv):
    # Create header if it doesn't exist
    header = ["participant_id", "site", "group"]
    df = pd.DataFrame(columns=header)
    df.to_csv(participants_tsv, sep='\t', index=False)

# Remove existing entry if it exists
df = pd.read_csv(participants_tsv, sep='\t')
df = df[df["participant_id"] != f"sub-{subject}"]

# Add new subject info
group = "Patient" if "PX" in subject else "Healthy"
new_subject = {"participant_id": f"sub-{subject}", "site": "Montreal_SiemmensPET-HRRT", "group": group}
df = pd.concat([df, pd.DataFrame([new_subject])], ignore_index=True)
df.to_csv(participants_tsv, sep='\t', index=False)

# Handle sessions
sessions_tsv = os.path.join(bids_dir, f"sub-{subject}/sub-{subject}_sessions.tsv")
all_ses = glob.glob(os.path.join(f"{bids_dir}/sub-{subject}/ses-*"))
all_ses = [os.path.basename(s)[4:] for s in all_ses]

# Create a dataframe with columns=["session_id"] and all the  all_ses
df_sessions = pd.DataFrame(all_ses, columns=["session_id"])
df_sessions.to_csv(sessions_tsv, sep='\t', index=False)

# -----------------------------------------------------------------------------------
# Capture the end time
end_time = time.time()  # End time in seconds (wall time)

# Calculate the time difference in seconds
time_difference = end_time - start_time

# Convert the time difference to minutes
time_difference_minutes = time_difference / 60

# Format the time difference to 3 decimal places
formatted_time = f"{time_difference_minutes:.3f}"

# -----------------------------------------------------------------------------------
# Run BIDS validator
bids_validator = "{bids_dir}/bids_validator_output.txt"
if args.bids_validator:
    command = f'deno run --allow-write -ERN jsr:@bids/validator {bids_dir} --ignoreWarnings --outfile {bids_validator}'
    run_command(command)
os.chmod(bids_validator, 0o777)

# Print the result with some colored output (for terminal)
print(f"Ecat to BIDS running time: \033[38;5;220m {formatted_time} minutes \033[38;5;141m")
print("----------------------------------------------------------------------------\n")

# -----------------------------------------------------------------------------------
# Add data to participants_7t2bids.tsv
df_participants_bic2bids = pd.read_csv(tsv_file, sep='\t')

# Remove any rows with the same subject and session (id)
id = f"{subject}_{session}"
df_participants_bic2bids = df_participants_bic2bids[df_participants_bic2bids["subject_id"] != id]

# Create the new row as a dictionary
new_row = {
    "subject_id": id,
    "date": today,
    "N.anat": anat,
    "N.pet": pet,
    "source": pet_dir,
    "user": os.getenv("USER"),
    "processing.time": formatted_time
}

# Convert the dictionary to a DataFrame
new_row_df = pd.DataFrame([new_row])

# Concatenate the new row DataFrame with the existing DataFrame
df_participants_bic2bids = pd.concat([df_participants_bic2bids, new_row_df], ignore_index=True)

# Write the updated DataFrame back to the tsv file
df_participants_bic2bids.to_csv(tsv_file, sep='\t', index=False)