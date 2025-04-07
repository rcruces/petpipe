from pathlib import Path

# Configuration
FASTSURFER_IMG = config.get("singularity_containers", {}).get(
    "fastsurfer", "/data/mica1/01_programs/fastsurfer/fastsurfer-cpu-v2.4.2.sif"
)
FS_LICENSE = config.get("freesurfer_license", "/data_/mica1/01_programs/freesurfer-7.3.2/license.txt")
TMPDIR = config.get("tmp_dir", "/host/yeatman/local_raid/rcruces/tmp/tmpfiles")

# Set up FastSurfer output directory
fastsurfer_outdir = Path(
    config["output_dir"], 
    config.get("fastsurfer_output_subdir", "fastsurfer")
)

# Rule to ensure output directory exists
rule fastsurfer_create_output_dir:
    output:
        directory(fastsurfer_outdir)
    shell:
        "mkdir -p {output}"

# Main rule to run FastSurfer for each subject
rule run_fastsurfer:
    input:
        t1w=bids(
            root=config["bids_dir"],
            datatype="anat",
            suffix="T1w",
            extension=".nii.gz",
            **config["input_wildcards"]["t1w"]
        ),
        outdir=fastsurfer_outdir
    params:
        sub=lambda wildcards: wildcards.subject.replace("sub-", ""),
        ses=lambda wildcards: wildcards.session.replace("ses-", "") if hasattr(wildcards, 'session') else None,
        subject_id=lambda wildcards: f"sub-{wildcards.subject.replace('sub-', '')}_ses-{wildcards.session.replace('ses-', '')}" if hasattr(wildcards, 'session') else f"sub-{wildcards.subject.replace('sub-', '')}",
        bids_dir=config["bids_dir"],
        outdir=fastsurfer_outdir,
        fastsurfer_img=FASTSURFER_IMG,
        fs_license=FS_LICENSE,
        tmpdir=TMPDIR
    output:
        # Define expected FastSurfer output files
        surf=directory(fastsurfer_outdir / "{subject_id}/surf"),
        mri=directory(fastsurfer_outdir / "{subject_id}/mri"),
        label=directory(fastsurfer_outdir / "{subject_id}/label")
    threads: config.get("threads", 15)
    resources:
        mem_mb=16000
    container:
        FASTSURFER_IMG
    shell:
        """
        # Ensure temp directory exists
        mkdir -p {params.tmpdir}
        
        # Get full path to T1w image
        T1_IMAGE={input.t1w}
        
        # Run singularity
        singularity exec --writable-tmpfs --containall \
            -B "{params.outdir}":/output \
            -B "{params.tmpdir}":/tmpdir \
            -B "$T1_IMAGE":/tmpdir/{params.subject_id}_T1w.nii.gz \
            -B "{params.fs_license}":/output/license.txt \
            "{params.fastsurfer_img}" \
            /fastsurfer/run_fastsurfer.sh \
            --fs_license /output/license.txt \
            --vox_size min \
            --t1 /tmpdir/{params.subject_id}_T1w.nii.gz \
            --sid "{params.subject_id}" --sd /output \
            --parallel --threads {threads} --device cpu --3T \
            --no_hypothal
        """

# Rule to create a combined target for all subjects
rule all_fastsurfer:
    input:
        expand(
            [
                fastsurfer_outdir / "{subject_id}/surf",
                fastsurfer_outdir / "{subject_id}/mri",
                fastsurfer_outdir / "{subject_id}/label"
            ],
            subject_id=expand(
                "sub-{subject}" if not config.get("use_session", False) else "sub-{subject}_ses-{session}",
                subject=config["subjects"],
                session=config.get("sessions", ["01"]) if config.get("use_session", False) else []
            )
        )