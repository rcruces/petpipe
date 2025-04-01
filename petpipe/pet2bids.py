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

def info(message):
    print(f"[ INFO ] ... {message}")

def warning(message):
    print(f"[ WARNING ] ... {message}")

def error(message):
    print(f"[ ERROR ] ... {message}")

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
session = f"ses-{args.ses.replace('ses-', '')}"
subject = f"sub-{args.sub.replace('sub-', '')}"
pet_dir = os.path.realpath(args.pet_dir)
bids_dir = os.path.realpath(args.bids_dir)
micapipe_dir = os.path.realpath(args.micapipe_dir)
subject_dir = os.path.join(f"{bids_dir}/sub-{subject}/ses-{session}")
t1_files_glob = glob.glob(os.path.join(micapipe_dir, f"sub-{subject}", "ses-01", "anat", "*_space-nativepro_T1w.json"))
if not t1_files_glob:
    error(f"No T1w file found for subject {subject} in session ses-01.")
tmpDir = os.path.realpath(args.tmpDir) if args.tmpDir else tempfile.mkdtemp()
t1_files = os.path.splitext(t1_files_glob[0])[0]

# Set default values
tmpDir = tempfile.mkdtemp() if not args.tmpDir else os.path.realpath(args.tmpDir)

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

print("-------------------------------------------------------------")
print("         PET pipeline - ECAT to BIDS conversion")
print("-------------------------------------------------------------")
print(f"Subject: {subject}")
print(f"Session: {session}")
print(f"Input Directory: {pet_dir}")
print(f"BIDS subject directory: {subject_dir}")
print(f"Temporary Directory: {tmpDir}")
print("-------------------------------------------------------------")

# Make Subject Directory
os.makedirs(subject_dir, exist_ok=True)
os.makedirs(os.path.join(subject_dir, "anat"), exist_ok=True)
os.makedirs(os.path.join(subject_dir, "pet"), exist_ok=True)

class BIDSpet_name:
    def __init__(self, **kwargs):
        self.keys = ["sub", "ses", "task", "trc", "rec", "run", "desc"]
        self.values = kwargs
    
    def build(self):
        parts = []
        for key in self.keys:
            if key in self.values:
                parts.append(f"{key}-{self.values[key]}")
        parts.append("pet")
        return "_".join(parts)
    
class BIDS_name:
    ALLOWED_SUFFIXES = ["FLAIR", "PDT2", "PDw", "T1w", "T2starw", "T2w", "UNIT1", "angio", "inplaneT1", "inplaneT2"] 
    def __init__(self, **kwargs):
        self.keys = ["sub", "ses", "task", "acq", "ce", "rec", "run", "echo","part", "chunk", "suffix"]
        self.values = kwargs    
        # Validate suffix
        if 'suffix' in self.values and self.values['suffix'] not in self.ALLOWED_SUFFIXES:
            raise ValueError(f"Invalid suffix: {self.values['suffix']}. Must be one of {self.ALLOWED_SUFFIXES}")
    
    def build(self):
        parts = []
        for key in self.keys:
            if key in self.values:
                if key == "suffix":
                    # Directly append the suffix without a prefix "suffix-"
                    suffix = self.values[key]
                    parts.append(suffix)
                elif isinstance(self.values[key], str):
                    parts.append(f"{key}-{self.values[key]}")
                elif isinstance(self.values[key], int):
                    parts.append(f"{key}-{self.values[key]}")
        
        return "_".join(parts)

def merge_json_files(json_pet, json_subject):
    """
    Merge the newly created JSON file with an existing JSON file,
    overwriting the existing file with the merged content.

    Args:
        json_pet (str): Path to the newly created JSON file.
        json_subject (str): Path to the subject's JSON file.
    """
    # Load existing JSON if it exists
    if os.path.exists(json_subject):
        with open(json_subject, 'r') as f:
            existing_data = json.load(f)
    else:
        existing_data = {}

    # Load new JSON
    if os.path.exists(json_pet):
        with open(json_pet, 'r') as f:
            new_data = json.load(f)
    else:
        raise FileNotFoundError(f"New JSON file not found: {json_pet}")

    # Merge JSONs (existing data takes priority in case of conflicts)
    merged_data = {**new_data, **existing_data}

    # Overwrite the existing JSON file
    with open(json_pet, 'w') as f:
        json.dump(merged_data, f, indent=4)

    print(f"Updated JSON saved to: {json_pet}")

def convert_ecat_to_bids(in_file, out_file, output_dir, json=None):
    """
    Convert ECAT files to BIDS format using dcm2niix.
    Args:
        in_file (str): Input ECAT file path.
        out_file (str): Output BIDS file path.
        output_dir (str): Output directory for converted files.
    """
    
    command = f'dcm2niix -b y -v n -z y -o {output_dir} -f {out_file} {in_file}'
    print(command)
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        
        # Check if the output file was generated
        nifti_file = os.path.join(output_dir, f"{out_file}.nii.gz")
        if not os.path.isfile(nifti_file):
            print(f"Conversion failed, NIfTI file not generated: {nifti_file}")
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error running dcm2niix: {e.stderr}")
        sys.exit(1)

    if json is not None:
        # Update JSON sidecar
        merge_json_files(os.path.join(output_dir, f"{out_file}.json"), json)

# -----------------------------------------------------------------------------------
# Create the mk6240 NIFTI
pet_image = BIDSpet_name(trc="mk6240", sub=subject, ses=session, rec="acdyn").build()
convert_ecat_to_bids(f'{pet_dir}/*EM_4D_MC01.v', pet_image, subject_dir, json=os.path.join(repo_dir, "files/subject_trc-MK6240_pet.json"))

# Create the mk6240 transmission
tx_image = BIDSpet_name(sub=subject, ses=session, desc="LinearAtenuationMap").build()
convert_ecat_to_bids(f"{pet_dir}/Transmission/*TX.v", tx_image, f"{subject_dir}/pet")

# -----------------------------------------------------------------------------------
# Copy the T1w image to BIDS directory
t1_str = BIDS_name(suffix="T1w", sub=subject, ses=session).build()

# Copy the files
shutil.copy2(f"{t1_files}.json", os.path.join(subject_dir, f"anat/{t1_str}.json"))
shutil.copy2(f"{t1_files}.nii.gz", os.path.join(subject_dir, f"anat/{t1_str}.nii.gz"))

# -----------------------------------------------------------------------------------
# Copy mandatory files for BIDS compliance
mandatory_files = ["CITATION.cff", "dataset_description.json", ".bidsignore", "participants.json", "trc-MK6240_pet.json", "README"]
for file in mandatory_files:
    source_path = os.path.join(repo_dir, "files", file)
    dest_path = os.path.join(bids_dir, file)
    shutil.copy2(source_path, dest_path)

# ----------------------------------------------------------------------------------
# Count number of gzipped NIfTI files in different directories
anat = len(glob.glob(os.path.join(bids_dir, "anat", "**", "*.nii.gz"), recursive=True))
pet = len(glob.glob(os.path.join(bids_dir, "pet", "**", "*.nii.gz"), recursive=True))

# Check if participants TSV file exists, create it if not
tsv_file = os.path.join(bids_dir, "participants_bic2bids.tsv")
if not os.path.isfile(tsv_file):
    # Create the header if the file does not exist
    header = ["sub", "ses", "date", "N.anat", "N.pet", "source", "user", "processing.time"]
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

# Create and update sessions TSV for the subject
sessions_tsv = os.path.join(bids_dir, f"sub-{subject}/sub-{subject}_sessions.tsv")
if not os.path.isfile(sessions_tsv):
    # Create the header if the file doesn't exist
    pd.DataFrame(columns=["session_id"]).to_csv(sessions_tsv, sep='\t', index=False)

# Remove existing entry if it exists
df_sessions = pd.read_csv(sessions_tsv, sep='\t')
df_sessions = df_sessions[df_sessions["session_id"] != session]

# Add session info
new_session_row = pd.DataFrame([{"session_id": session}])
df_sessions = pd.concat([df_sessions, new_session_row], ignore_index=True)
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

# Print the result with some colored output (for terminal)
print("----------------------------------------------------------------------------")
print(f"Ecat to BIDS running time: \033[38;5;220m {formatted_time} minutes \033[38;5;141m")

# -----------------------------------------------------------------------------------
# Add data to participants_7t2bids.tsv
df_participants_bic2bids = pd.read_csv(tsv_file, sep='\t')
new_row = {
    "sub": subject,
    "ses": session,
    "date": today,
    "N.anat": anat,
    "N.dwi": pet,
    "user": os.getenv("USER", "unknown_user"),
    "user": os.getenv("USER"),
    "processing.time": time_difference
}

# Check if the row already exists based on "sub" and "ses"
def find_existing_row_index(df, sub, ses):
    """
    Find the index of an existing row in the DataFrame based on subject and session.

    Args:
        df (pd.DataFrame): The DataFrame to search.
        sub (str): Subject identifier.
        ses (str): Session identifier.

    Returns:
        pd.Index: Index of the matching row(s).
    """
    return df[(df["sub"] == sub) & (df["ses"] == ses)].index
existing_row_index = find_existing_row_index(df_participants_bic2bids, new_row["sub"], new_row["ses"])

# If the row exists, overwrite it, otherwise append the new row
if not existing_row_index.empty:
    # Overwrite the existing row
    # Ensure column alignment before assignment
    aligned_new_row = pd.DataFrame([new_row], columns=df_participants_bic2bids.columns)
    df_participants_bic2bids.loc[existing_row_index] = aligned_new_row.iloc[0]
else:
    # Append the new row
    new_row_df = pd.DataFrame([new_row])
    df_participants_bic2bids = pd.concat([df_participants_bic2bids, new_row_df], ignore_index=True)

df_participants_bic2bids.to_csv(tsv_file, sep='\t', index=False)