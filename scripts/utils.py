# utils.py - Python Utilities

import os
import json
import subprocess
from nilearn.image import load_img, mean_img
from nilearn.surface import load_surf_data
import nibabel as nib

class bcolors:
    PURPLE = '\033[95m'
    TEAL = '\033[38;5;37m'
    WARNING = '\033[38;5;220m'
    ERROR = '\033[38;5;1m'
    ENDC = '\033[0m'
    CIAN = '\033[38;5;45m'
    BOLD = '\033[1m'

    def disable(self):
        self.INFO = ''
        self.TEAL = ''
        self.WARNING = ''
        self.ERROR = ''
        self.CIAN = ''
        self.BOLD = ''
        self.ENDC = ''

def info(message):
    print(f"{bcolors.CIAN}  Info ... {message}{bcolors.ENDC}\n")

def warning(message):
    print(f"\n{bcolors.WARNING}  Warning ... {message}{bcolors.ENDC}\n")

def error(message):
    print(f"{bcolors.ERROR}  Error ... {message}{bcolors.ENDC}\n")

def note(message):
    print(f"{bcolors.PURPLE}{message}{bcolors.ENDC}\n")

class BIDSpetName:
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

class BIDSderivativeName:
    ALLOWED_SUFFIXES = ["pet", "T1w", "T1w_mask", "surf", "xfm"]
    def __init__(self, **kwargs):
        self.keys = ["sub", "ses", "hemi", "surf", "from", "to", "space", "label", "smooth", "pvc", "ref", "desc", "trc"]
        self.values = kwargs
    
    def build(self):
        parts = []
        for key in self.keys:
            if key in self.values:
                if key == "suffix":
                    # Directly append the suffix without a prefix "suffix-"
                    suffix = self.values[key]
                    if self.values[key] is not "surf":
                        parts.append(suffix)
                elif isinstance(self.values[key], str):
                    parts.append(f"{key}-{self.values[key]}")
                elif isinstance(self.values[key], int):
                    parts.append(f"{key}-{self.values[key]}")
        
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

def compute_average_4D_image(pet_trc, threads=1):
    """
    Compute the average across the 4th dimension of a 4D NIfTI image or a list of such images.
    
    Parameters:
    - pet_trc: str or list of str, path(s) to the NIfTI image(s)
    - threads: int, number of threads for parallel processing (default: 1)

    Returns:
    - List of averaged 3D images if input is a list, otherwise a single 3D image.
    """
    
    # Ensure input is a list
    if isinstance(pet_trc, str):
        pet_trc = [pet_trc]

    pet_mean_images = []

    for pet_path in pet_trc:
        # Load the PET image
        pet_img = nib.load(pet_path)

        # Check if the image is 4D
        if len(pet_img.shape) == 4:
            # Compute the average across the 4th dimension
            pet_mean = mean_img(pet_img, target_affine=None, target_shape=None, verbose=0, n_jobs=threads, copy_header=True)
            info(f"Average of the 4D image computed for {pet_path}.")
            pet_mean_images.append(pet_mean)
        else:
            info(f"The image at {pet_path} is not 4D, no average computed.")

    # Return a list if multiple images, otherwise return a single image
    return pet_mean_images if len(pet_mean_images) > 1 else pet_mean_images[0]

def convert_freesurfer_to_gifti(input_path, output_path):
    """
    Load a FreeSurfer lh.thickness file, convert it to GIfTI format, and save it.

    Parameters:
    - input_path: str, path to the lh.thickness file.
    - output_path: str, path to save the converted GIfTI file.
    """
    # Load cortical thickness data using nilearn
    thickness_data = load_surf_data(input_path)  # Returns a NumPy array

    # Convert to GIfTI format
    gifti_image = nib.GiftiImage(darrays=[nib.GiftiDataArray(thickness_data)])

    # Save as GIfTI
    nib.save(gifti_image, output_path)
    print(f"Saved GIfTI file to {output_path}")