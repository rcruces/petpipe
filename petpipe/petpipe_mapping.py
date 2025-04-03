#!/usr/bin/env python
# coding: utf-8
"""
This script is part of the PET pipeline for processing PET imaging data.
It maps PET volumes to hippocampal surfaces, smooths the data, and calculates hippocampal volumes.
The script requires the following arguments:
    -sub        : Subject identification.
    -ses        : Session.
    -out        : Path to derivatives directory ( . or FULL PATH).
    -hippunfold : Path to Hippunfold directory ( . or FULL PATH).
    -threads    : Number of threads to use for processing (default: 6).
    -smooth     : Smoothing kernel size in mm (default: 2).
    -tmpDir     : Specify location of temporary directory <path> (Default is /tmp).
    -force      : Will overwrite files.

The script is intended for use by researchers and developers working with PET imaging data, particularly in the context of hippocampal analysis.
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
parser.add_argument("-out", dest="out_dir", type=str, required=True, help="Path to derivatives directory ( . or FULL PATH)")
parser.add_argument("-hippunfold", dest="hip_dir", type=str, required=True, help="Path to Hippunfols directory ( . or FULL PATH)")
parser.add_argument("-threads", type=int, dest="threads", default=6, help="Number of threads to use for processing (default: 6)")
parser.add_argument("-smooth", type=int, dest="smooth", default=2, help="Smoothing kernel size in mm (default: 2)")
parser.add_argument("-tmpDir", type=str, default="/tmp", help="Specify location of temporary directory (default: /tmp)")
parser.add_argument("-force", action="store_true", help="Overwrite files")
args = parser.parse_args()

# Validate mandatory arguments
if not all([args.sub, args.ses, args.hippunfold, args.out]):
    print("Error: One or more mandatory arguments are missing.")
    parser.print_help()
    sys.exit(1)

# Normalize paths and variables
session = f"{args.ses.replace('ses-', '')}"
subject = f"{args.sub.replace('sub-', '')}"
hip_dir = os.path.realpath(args.hip_dir)
out_dir = os.path.realpath(f"{args.out_dir}/petpipe_beta")
threads = args.threads
smooth = args.smooth

# -------------------------------------------------------------------------
# Check if surf_dir
if not os.path.isdir(hip_dir):
    error(f"Hippunfold directory {hip_dir} does not exist")
    sys.exit(1)
# Check if the output directory exists
if not os.path.isdir(out_dir):
    error(f"Hippunfold directory {hip_dir} does not exist")
    sys.exit(1)

print(f"\n{bcolors.TEAL}-------------------------------------------------------------")
print("         PET pipeline - Processing")
print("-------------------------------------------------------------{bcolors.ENDC}")
print(f"   {bcolors.TEAL}Subject:{bcolors.ENDC} {subject}")
print(f"   {bcolors.TEAL}Session:{bcolors.ENDC} {session}")
print(f"   {bcolors.TEAL}Output directory:{bcolors.ENDC} {out_dir}")
print(f"   {bcolors.TEAL}Hippunfold directory:{bcolors.ENDC} {hip_dir}")
print(f"   {bcolors.TEAL}Smoothing kernel size:{bcolors.ENDC} {smooth} mm")
print(f"   {bcolors.TEAL}Threads:{bcolors.ENDC} {threads}")

# Set default values
tmpDir = tempfile.mkdtemp() if not args.tmpDir else os.path.realpath(args.tmpDir)
print(f"Temporary Directory: {tmpDir}")

# Timer & beginning
import time
start_time = time.time()

# Print today's date in mm.dd.yyyy format
today=datetime.today().strftime('%m.%d.%Y')

# -----------------------------------------------------------------------------------
# Map the PET volume to the hippocampal surface

# -----------------------------------------------------------------------------------
# Smooth PET on hippocampal surface

# -----------------------------------------------------------------------------------
# Calculate hippocampal volumes

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
