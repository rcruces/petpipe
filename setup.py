from setuptools import setup, find_packages

setup(
    name="petpipe",
    version="0.1.0",
    author="Raúl RC & Enning Yang",
    author_email="raul.rodriguezcruces@mcgill.ca",
    description="BIDS-compliant processing pipeline for PET imaging using python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),  # Adjust depending on your structure
    package_dir={"": "petpipe"},  
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8,<4.0",
    install_requires=[
        "snakebids >=0.14.0",
        "snakemake>=7.20,<8; python_version < '3.11'",
        "snakemake>=8.1.2; python_version >= '3.11'",
        "pulp < 2.8.0; python_version < '3.11'",
    ],
    entry_points={
        "console_scripts": [
            "petpipe=petpipe.run:app.run"
        ]
    }
)
