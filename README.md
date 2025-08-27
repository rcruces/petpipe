# PET imaging Pipeline
BIDS-compliant processing pipeline for PET imaging using python and Snakemake.

## Overview
This pipeline provides automated preprocessing and analysis of PET imaging datasets organized in the BIDS format.
It is designed for reproducibility, scalability, and portability across environments (local, HPC clusters, and cloud).

## Workflow (Draft)
- Input: BIDS-compliant PET datasets (sub-*/ses-*/pet/*.nii[.gz], dataset_description.json, etc.)
- Preprocessing: Coregistration to structural image T1w/MP2RAGE
- Quantification: SUV / SUVr calculation, kinetic modeling (optional)
- PVC: partial volume correction
- Surface mapping: From cortical and hippocampal surfaces and apply smoothing over the surface (optional)
- Outputs: BIDS-Derivatives folder with processed images (NIFTIS and GIFTIS), QC reports, and logs

## Requirements
In order to use the surfaces this pipeline requires that `micapipe`, `Freesurfer`, or `Fastsurfer` has been run on the dataset.
- hippunfold (optional)

## Installation
- Snakemake (>= 7.x recommended)
- Conda (for environment management)
- Python (>= 3.9)

Create the environment using the provided `environment.yml`:
    conda env create -f environment.yml
    conda activate pet_pipeline

## Usage
Run the pipeline with:
```
    petpipe <BIDS directory> <derivatives directory> --options
```
### Main Parameters
```
--config bids : Path to BIDS dataset
--directory : Output derivatives folder
--cores : Number of cores to use
--use-singularity or --use-conda : Container or environment management (optional)
```

## Datasets Tested
| Dataset              | Description                                                         | Availability                                                                  | BIDS |
|----------------------|---------------------------------------------------------------------|-------------------------------------------------------------------------------|------|
| MICA Tau-PET         | [18F]-MK-6240 Temporal lobe epilepsy and healthy subjects Tau-PET   | Not open                                                                      |  ✔️  |
| Healthy Tau-PET      | [18F]-MK-6240 Healthy subjects Tau-PET                              | [OSF: znt9d](https://osf.io/znt9d/)                                           |  ✔️  |
| CERMEP-IDB-MRXFDG    | 18F-FDG and anatomical MRI for 37 normal adult human subjects       | [DOI: 10.1186/s13550-021-00830-6](https://doi.org/10.1186/s13550-021-00830-6) |  ✔️  |
| PET glucose in AD    | 18F-FDG Alzheimer's Disease Neuroimaging Initiative (ADNI)          | [Website](https://adni.loni.usc.edu/)                                         |  ❌  |
| PET Protein synthesis| L-[1-11C]Leucine 4D Positron Emission Tomography (PET) images       | [OpenNeuro: ds004730](https://openneuro.org/datasets/ds004730/versions/1.0.0) |  ✔️  |
| PET neuroinflammation| [11C]MC1 COX-2                                                      | [OpenNeuro: ds004869](https://openneuro.org/datasets/ds004869/versions/1.1.1) |  ✔️  |

## Outputs (draft)
- derivatives/
  - sub-*/ses-*/pet/ processed images
  - QC reports (qc/)
  - logs (snakemake.log)

## Acknowledgments
This pipeline builds on the MICA lab/snakemake ecosystem and BIDS standards.
- BIDS PET extension: doi: [10.1038/s41597-022-01164-1](https://doi.org/10.1038/s41597-022-01164-1)

