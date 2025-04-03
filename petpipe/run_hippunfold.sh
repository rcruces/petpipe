#!/bin/bash
# ----------------------------------------------------------------
# This script is part of the PETPIPE pipeline
# This script runs the HIPUNFOLD pipeline for a given subject
# Usage: bash run_hippunfold.sh <sub> <threads> <out>
# ----------------------------------------------------------------
#
# Usage: bash run_hippunfold.sh <sub> <bids_dir> <out> <threads>
# 
# This is a functional draft, current paths are local or hardcoded!
sub=$1
bids_dir=$2
out=$3
threads=$4
HIPPUNFOLD_IMG=/data/mica1/01_programs/singularity/hippunfold_v1.4.1.sif
export HIPPUNFOLD_CACHE_DIR=/host/yeatman/local_raid/rcruces/cache/hippunfold
export SNAKEMAKE_OUTPUT_CACHE=/host/yeatman/local_raid/rcruces/cache/snakemake

# Hippunfold image path
sif_hipunfold=${HIPPUNFOLD_IMG}

here=$(pwd)
# Create output directory
mkdir -p ${out}/hippunfold_v1.4.1

cd $SNAKEMAKE_OUTPUT_CACHE
singularity run \
        -B ${bids_dir}:/bids_dir \
        -B ${out}/hippunfold_v1.4.1:/output_dir \
        ${sif_hipunfold} /bids_dir /output_dir \
        participant \
        --participant_label ${sub/sub-} \
        --modality T1w \
        --output-density 0p5mm 2mm \
        --cores ${threads} 
        # --filter-T1w space=nativepro \

cd $here