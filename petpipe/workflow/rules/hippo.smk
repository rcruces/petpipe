from pathlib import Path

# Configuration
HIPPUNFOLD_IMG = config.get("singularity_containers", {}).get(
    "hippunfold", "/data/mica1/01_programs/singularity/hippunfold_v1.4.1.sif"
)
HIPPUNFOLD_CACHE_DIR = config.get("hippunfold_cache_dir", "/host/yeatman/local_raid/rcruces/cache/hippunfold")
SNAKEMAKE_OUTPUT_CACHE = config.get("snakemake_output_cache", "/host/yeatman/local_raid/rcruces/cache/snakemake")

# Set up hippunfold output directory
hippunfold_outdir = Path(
    config["output_dir"], 
    config.get("hippunfold_output_subdir", "hippunfold_v1.4.1")
)

# Rule to ensure output directory exists
rule hippunfold_create_output_dir:
    output:
        directory(hippunfold_outdir)
    shell:
        "mkdir -p {output}"

# Main rule to run HippUnfold for each subject
rule run_hippunfold:
    input:
        t1w=bids(
            root=config["bids_dir"],
            datatype="anat",
            suffix="T1w",
            extension=".nii.gz",
            **config["input_wildcards"]["t1w"]
        ),
        outdir=hippunfold_outdir
    params:
        sub=lambda wildcards: wildcards.subject.replace("sub-", ""),
        bids_dir=config["bids_dir"],
        outdir=hippunfold_outdir,
        hippunfold_img=HIPPUNFOLD_IMG,
        modality="T1w",
        output_density="0p5mm 2mm",
        hippunfold_cache_dir=HIPPUNFOLD_CACHE_DIR,
        snakemake_output_cache=SNAKEMAKE_OUTPUT_CACHE
    output:
        hippocampus=expand(
            hippunfold_outdir / "sub-{subject}" / "surf" / "sub-{subject}_hemi-{hemi}_space-T1w_den-0p5mm_label-hipp_midthickness.surf.gii",
            hemi=["L", "R"],
            allow_missing=True
        )
    threads: config.get("threads", 8)
    resources:
        mem_mb=8000
    container:
        HIPPUNFOLD_IMG
    shell:
        """
        export HIPPUNFOLD_CACHE_DIR={params.hippunfold_cache_dir}
        export SNAKEMAKE_OUTPUT_CACHE={params.snakemake_output_cache}
        
        cd {params.snakemake_output_cache}
        
        singularity run \
            -B {params.bids_dir}:/bids_dir \
            -B {params.outdir}:/output_dir \
            {params.hippunfold_img} /bids_dir /output_dir \
            participant \
            --participant_label {params.sub} \
            --modality {params.modality} \
            --output-density {params.output_density} \
            --cores {threads}
        """

# Rule to create a combined target for all subjects
rule all_hippunfold:
    input:
        expand(
            hippunfold_outdir / "sub-{subject}" / "surf" / "sub-{subject}_hemi-{hemi}_space-T1w_den-0p5mm_label-hipp_midthickness.surf.gii",
            subject=config["subjects"],
            hemi=["L", "R"],
        )