#!/bin/bash
#
# MICA PET processing script
#
Col="38;5;83m" # Color code
#---------------- FUNCTION: HELP ----------------#
help() {
echo -e "\033[38;5;141m

\033[38;5;141mCOMMAND:\033[0m
   $(basename $0)

\033[38;5;141mARGUMENTS:\033[0m
\t\033[38;5;120m-sub\033[0m 	      : Subject identification.
\t\033[38;5;120m-ses\033[0m 	      : Session.
\t\033[38;5;120m-out\033[0m 	      : Output directory.
\t\033[38;5;120m-micapipe\033[0m     : Path to micapipe directory
\t\033[38;5;120m-surf_dir\033[0m     : Path to surface directory


\033[38;5;141mOPTIONS:\033[0m
\t\033[38;5;197m-nocleanup\033[0m : Do not delete temporal directory at script completion
\t\033[38;5;197m-threads\033[0m   : Number of threads (Default is 6)
\t\033[38;5;197m-tmpDir\033[0m    : Specify location of temporary directory <path> (Default is /tmp)
\t\033[38;5;197m-quiet\033[0m 	   : Does NOT print comments.

\033[38;5;141mUSAGE:\033[0m
   $(basename "$0")\033[0m \033[38;5;197m-sub\033[0m HC062 \033[38;5;197m-ses\033[0m 01 \\
                  \033[38;5;197m-out\033[0m /data_/mica3/MICA-PET/derivatives_trc-mk6240_desc-REP \\
                  \033[38;5;197m-micapipe\033[0m /data_/mica3/BIDS_MICs/derivatives/micapipe_v0.2.0 \\
                  \033[38;5;197m-surf_dir\033[0m /data_/mica3/BIDS_MICs/derivatives/freesurfer

RRC - McGill University, MNI, MICA-lab, April 2025
https://github.com/MICA-MNI
http://mica-mni.github.io/"
}

# SET the MICAPE working directory
MICAPET=$(dirname $(realpath "$0"))

# Source print functions
source "${MICAPET}/utilities.sh"

#------------------------------------------------------------------------------#
#			ARGUMENTS
# Number of inputs
for arg in "$@"
do
  case "$arg" in
  -h|-help)
    help
    exit 1
  ;;
  -sub)
    id=$2
    shift;shift
  ;;
  -out)
    outDir=$2
    shift;shift
  ;;
  -ses)
    ses=$2
    shift;shift
  ;;
  -nocleanup)
    nocleanup=TRUE
    shift
  ;;
  -threads)
    threads=$2
    shift;shift
  ;;
  -tmpDir)
    tmpDir=$2
    shift;shift;
  ;;
  -surf_dir)
    surf_dir=$2
    shift;shift
  ;;
  -micapipe)
    micapipe_dir=$2
    shift;shift
  ;;
  -quiet)
    quiet=TRUE
    shift;shift
  ;;
  -*)
    Error "Unknown option ${2}"
    help
    exit 1
  ;;
   esac
done

# argument check out & WARNINGS
arg=($id $ses $outDir $surf_dir, $micapipe_dir)
if [ "${#arg[*]}" -lt 4 ]; then help
Error "One or more mandatory arguments are missing.
               -sub      : $id
               -ses      : $ses
               -out      : $outDir
               -micapipe : $micapipe_dir
               -surf_dir : $surf_dir"
exit 0; fi

# Realpath to directories
sub=sub-${id/sub-}
ses=ses-${ses/ses-}
subject_id=${sub}_${ses}

outDir=$(realpath "$outDir")
subjDIR=$(realpath "$micapipe_dir")/${sub}/ses-01
surf_dir=$(realpath "$surf_dir")/${sub}_ses-01
out="${outDir}/micapet/${sub}/${ses}"
trc="mk6240"

# Erase temporal files by default
if [ -z "$nocleanup" ]; then nocleanup=FALSE; fi

# Number of THREADS used by ANTs. Default is 10 if not defined by -threads
if [[ -z "$threads" ]]; then export threads=10; fi

# Temporal directory
if [ -z "$tmpDir" ]; then export tmpDir=/tmp; else tmpDir=$(realpath "$tmpDir"); fi

# No print cmd
if [ "$quiet" = "TRUE" ]; then export quiet=TRUE; fi

# Suppress warnings
export AFNI_NIFTI_TYPE_WARN=No
export OMP_NUM_THREADS=$threads

#----------------    Variables      ----------------#
pet=${out}/pet/${subject_id}_pet-mkAVG-t1w_ANTs-a-direct.nii.gz
t1w=${out}/anat/${subject_id}_space-nativepro_T1w.nii.gz

# White matter probabilistic mask
#prob_wm="${surf_dir}/mri/wm.seg.mgz"
prob_wm="$subjDIR"/anat/${sub}_ses-01_space-nativepro_T1w_brain_pve_2.nii.gz

# Gray matter probabilistic mask
prob_gm="$subjDIR"/anat/${sub}_ses-01_space-nativepro_T1w_brain_pve_1.nii.gz

# Subcortical segmentation
atlas_subcortical="$subjDIR"/parc/*_space-nativepro_T1w_atlas-subcortical.nii.gz

# Atlas segmentation
atlas_fs="${surf_dir}/mri/aparc.DKTatlas+aseg.mgz"

#----------------  if !Variables    ----------------#
if [ ! -f "$t1w" ]; then Error "Subject $id does NOT have a T1 \n\t    ls ${t1w}"; exit 0; fi
if [ ! -f "$pet" ]; then Error "Subject $id does NOT have a mk-PET on T1 space \n\t  ls ${pet}"; exit 0; fi
if [ ! -f $prob_gm ]; then Error "Subject $id does NOT have a GM probabilistic segmentation \n\t  ls ${prob_gm}"; exit 0; fi
if [ ! -f $prob_wm ]; then Error "Subject $id does NOT have a GM probabilistic segmentation \n\t  ls ${prob_wm}"; exit 0; fi
if [ ! -f $atlas_fs ]; then Error "Subject $id does NOT have a surface segmentations DTK \n\t  ls ${atlas_fs}"; exit 0; fi

# temporal directory
tmp="${tmpDir}/${sub}_micapet2_${RANDOM}"
cmd mkdir -p "$tmp"
function finish {
  rm -rf "$tmp"
}
trap finish EXIT

#---------------- Timer & Beginning ----------------#
aloita=$(date +%s.%N)
Title "MICA-PET - SUVR, PVC and Surface Registration
Subject: ${sub}
Session: ${ses}
Tracer:  ${trc}
Tmp dir: ${tmp}
"

# -------------------------------------------------------------------
# SUVR | Calculate SUV =Cimg(90)/(Injected_dose/Body Weight)
# Register T1w atlas to T1w native space
atlas_t1w=${out}/anat/${subject_id}_atlas-DKT_T1w_mask.nii.gz
transformation_mat="${subjDIR}"/xfm/*_from-fsnative_to_nativepro_T1w_0GenericAffine.mat
if [ ! -f "$atlas_t1w" ]; then
antsApplyTransforms -i ${atlas_fs} -r ${t1w} \
        -t ${transformation_mat} \
        -o ${atlas_t1w} -d 3 -v -u int -n GenericLabel
fi
# Register T1w atlas to T1w native space
# prob_wm_t1w=${out}/anat/${subject_id}_atlas-WMprob_T1w_mask.nii.gz
# transformation_mat="${subjDIR}"/xfm/*_from-fsnative_to_nativepro_T1w_0GenericAffine.mat
# antsApplyTransforms -i ${prob_wm} -r ${t1w}
#         -t ${transformation_mat}
#         -o ${prob_wm_t1w} -d 3 -v -u int -n NearestNeighbor
prob_wm_t1w=${prob_wm}

# ------------------------------
# SUVR | brainsteam
reference="brainsteam"
atlas_mask=${out}/anat/${subject_id}_atlas-${reference}_T1w_mask.nii.gz

# Calculate mask
fslmaths ${atlas_t1w} -thr 16 -uthr 16 -bin ${atlas_mask}

# Generate normalized image
normalize_pet "${subject_id}" "${reference}" "${trc}" "${atlas_mask}" "${pet}" "${tmp}"

# ------------------------------
# SUVR | Cerebellar gray matter
reference="cerebellarGM"
atlas_mask=${out}/anat/${subject_id}_atlas-${reference}_T1w_mask.nii.gz

# Calculate mask
fslmaths ${atlas_t1w} -thr 47 -uthr 47 -bin ${tmp}/R_cerebellarGM_tmp.nii.gz
fslmaths ${atlas_t1w} -thr 8 -uthr 8 -bin ${tmp}/L_cerebellarGM_tmp.nii.gz
fslmaths ${tmp}/R_cerebellarGM_tmp.nii.gz -add ${tmp}/L_cerebellarGM_tmp.nii.gz -bin ${atlas_mask}

# Generate normalized image
normalize_pet "${subject_id}" "${reference}" "${trc}" "${atlas_mask}" "${pet}" "${tmp}"

# ------------------------------
# SUVR | Composite
reference="composite"
atlas_mask=${out}/anat/${subject_id}_atlas-${reference}_T1w_mask.nii.gz

# Calculate mask
fslmaths ${atlas_subcortical} -thr 16 -uthr 16 -binv -mul ${atlas_subcortical} -bin ${tmp}/subcortical.nii.gz
fslmaths ${prob_wm_t1w} \
  -add ${out}/anat/${subject_id}_atlas-cerebellarGM_T1w_mask.nii.gz \
  -add ${out}/anat/${subject_id}_atlas-brainsteam_T1w_mask.nii.gz -bin \
  -sub ${tmp}/subcortical.nii.gz -thr 0 ${atlas_mask}

# Generate normalized image
normalize_pet "${subject_id}" "${reference}" "${trc}" "${atlas_mask}" "${pet}" "${tmp}"

# Save reference values in a csv
reference_maks=("brainsteam" "cerebellarGM" "composite")
suvr_csv="${out}/anat/${subject_id}_desc-ReferenceMeanSUVR_trc-${trc}_pet.csv"
# Write header row
echo "subject_id,${reference_maks[*]}" | tr ' ' ',' > "$suvr_csv"

# Collect values for each reference
values=("$subject_id")  # Start with subject ID
for reference in "${reference_maks[@]}"; do
  pet_avg_csv="${tmp}/${subject_id}_ref-${reference}_trc-${trc}_pet.csv"
  pet_ref=$(awk -F "\t" 'NR==2 {print $4}' "$pet_avg_csv")
  values+=("$pet_ref")
done

# Append values as a new row
echo "${values[*]}" | tr ' ' ',' >> "$suvr_csv"

# -------------------------------------------------------------------
# PVC | Partial volume correction
# ------------------------------
# PVC | Probabilistic GM
method="GMprob"
prob_gm_NOsub="${out}/anat/${subject_id}_atlas-${method}_T1w.nii.gz"
fslmaths ${atlas_subcortical} -binv -mul ${prob_gm} ${prob_gm_NOsub}

# Generate PVC image
for reference in ${reference_maks[*]}; do 
  Info "PVC with ${method}"
  Note "Pet SUVR:" "${reference}"
  pet_suvr="${tmp}/${subject_id}_ref-${reference}_trc-${trc}_pet.nii.gz"
  pet_pvc="${out}/pet/${subject_id}_pvc-${method}_ref-${reference}_trc-${trc}_pet.nii.gz"
  fslmaths "$prob_gm" -mul "$pet_suvr" "$pet_pvc"
done

# ------------------------------
# SUVR | Muller-G  (MG)
method="MG"
# Create a probability tissue mask
tissue_mask="${tmp}/${subject_id}_tissue_mask.nii.gz"
mrcat -force ${prob_gm} ${prob_wm} "${tissue_mask}" -quiet

for reference in ${reference_maks[*]}; do
  Info "PVC with ${method}"
  Note "Pet SUVR:" "${reference}"
  pet_suvr="${tmp}/${subject_id}_ref-${reference}_trc-${trc}_pet.nii.gz"
  pet_pvc="${out}/pet/${subject_id}_pvc-${method}_ref-${reference}_trc-${trc}_pet.nii.gz"
	petpvc -i "$pet_suvr" \
	-m "${tissue_mask}" \
	-o "$pet_pvc" \
	--pvc MG -x 2.4 -y 2.4 -z 2.4
done

# -------------------------------------------------------------------
# Smooth thickness to smooth 10mm 
util_surface="${MICAPET}/surfaces"
smooth=10
Info "Smoothing ${smooth}mm cortical thickness in fsLR-32k"
for H in R L; do
  wb_command -metric-smoothing \
    "${subjDIR}/surf/${sub}_ses-01_hemi-${H}_space-nativepro_surf-fsLR-32k_label-midthickness.surf.gii" \
    "${subjDIR}/maps/${sub}_ses-01_hemi-${H}_surf-fsLR-32k_label-thickness.func.gii" \
    10 \
    "${out}/surf/${subject_id}_hemi-${H}_surf-fsLR-32k_label-thickness-${smooth}mm.shape.gii"
done

# -------------------------------------------------------------------
# Temporary fsa5 directory
if [ ! -d "${out}/surf" ]; then cmd mkdir "${out}/surf"; fi

Info "Mapping PET-${trc} to fsLR-32k and smoothing"
for HEMI in L R; do
    for label in midthickness; do
        surf_fsnative="${subjDIR}/surf/${sub}_ses-01_hemi-${HEMI}_space-nativepro_surf-fsnative_label-${label}.surf.gii"
        surf_fsLR_32k="${subjDIR}/surf/${sub}_ses-01_hemi-${HEMI}_space-nativepro_surf-fsLR-32k_label-${label}.surf.gii"
        cp "${surf_fsnative}" "${out}/surf"
        # MAPPING metric to surfaces
        for method in GMprob MG; do
        for reference in ${reference_maks[*]}; do
            pet_str=pvc-${method}_ref-${reference}_trc-${trc}_pet
            pet_pvc="${out}/pet/${subject_id}_${pet_str}.nii.gz"
            map_nat="${tmp}/${subject_id}_${HEMI}_surf-fsnative_label-${label}_${pet_str}.shape.gii"

            Info "SUVR hemisphere-${HEMI}: $pet_str"
            map_to-surfaces "${pet_pvc}" "${surf_fsnative}" "${map_nat}" "${HEMI}" "${label}_${pet_str}" "${out}/surf" ${sub} ${ses}

            # Output SUVR on surface
            pet_pvc_surf="${out}/surf/${subject_id}_hemi-${HEMI}_surf-fsLR-32k_label-${label}_${pet_str}.shape.gii"
            if [ ! -f "$pet_pvc_surf" ]; then exit; fi
            
            for k in 10 20; do
                Note "Smoothing" "$k mm"
                wb_command -metric-smoothing \
                    "${surf_fsLR_32k}" \
                    "${pet_pvc_surf}" \
                    "$k" \
                    "${out}/surf/${subject_id}_hemi-${HEMI}_surf-fsLR-32k_label-${label}_${pet_str}-${k}mm.shape.gii"
            done
        done
        done
    done
done

# ---------------------------------------------------------------------------- #
# Ending time
lopuu=$(date +%s.%N)
eri=$(echo "$lopuu - $aloita" | bc)
eri=$(echo print "$eri"/60 | perl)
echo -e "\n\033[38;5;141m-------------------------------------------------------------
MICA-PET_02 TOTAL running time:\033[38;5;220m $(printf "%0.2f\n" "$eri") minutes \033[38;5;141m
-------------------------------------------------------------\033[0m"
finish
