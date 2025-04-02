# utils.py - Python Utilities

import os
import json
import subprocess

def info(message):
    print("-------------------------------------------------------------")
    print(f"[ INFO ] ... {message}")

def warning(message):
    print(f"[ WARNING ] ... {message}")

def error(message):
    print(f"[ ERROR ] ... {message}")

class BIDSPetName:
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
    
class BIDSName:
    ALLOWED_SUFFIXES = ["FLAIR", "PDT2", "PDw", "T1w", "T2starw", "T2w", "UNIT1", "angio", "inplaneT1", "inplaneT2"] 
    def __init__(self, **kwargs):
        self.keys = ["sub", "ses", "task", "acq", "ce", "rec", "run", "echo", "part", "chunk", "suffix"]
        self.values = kwargs    
        # Validate suffix
        if 'suffix' in self.values and self.values['suffix'] not in self.ALLOWED_SUFFIXES:
            invalid_suffix = self.values['suffix']
            raise ValueError(f"Invalid suffix '{invalid_suffix}'. Must be one of {self.ALLOWED_SUFFIXES}")
    
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
    overwriting the existing file with the merged content. If the 
    `json_subject` file does not exist, an empty dictionary is used.

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

def run_command(command):
    try:
        print(f"Running command: {command}")
        subprocess.run(command.split(), check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running command: Exception: {e}")

def convert_ecat_to_bids(in_file, out_file, output_dir, json=None):
    """
    Convert ECAT files to BIDS format using dcm2niix.
    
    Args:
        in_file (str): Input ECAT file path.
        out_file (str): Output BIDS file path.
        output_dir (str): Output directory for converted files.
        json (str, optional): Path to an existing JSON file to merge with the generated JSON sidecar.
    """
    
    command = f'dcm2niix -b y -v n -z y -o {output_dir} -f {out_file} {in_file}'
    print(command)
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        
        # Check if the output file was generated
        nifti_file = os.path.join(output_dir, f"{out_file}.nii.gz")
        if not os.path.isfile(nifti_file):
            raise RuntimeError(f"Conversion failed, NIfTI file not generated: {nifti_file}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error running dcm2niix: {e.stderr}")
    if json is not None:
        # Update JSON sidecar
        merge_json_files(os.path.join(output_dir, f"{out_file}.json"), json)