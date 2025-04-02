# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Install dependencies and dcm2niix
RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           bc \
           cmake \
           curl \
           g++ \
           gcc \
           git \
           make \
           pigz \
           unzip \
           wget \
           zlib1g-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* 

# Download and install Miniconda <<<<<<< You can use Mamba instead of Conda
# Install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /miniconda.sh && \
    bash /miniconda.sh -b -p /opt/conda && \
    rm /miniconda.sh && \
    /opt/conda/bin/conda init && \
    /opt/conda/bin/conda clean -afy

# Update PATH to include Conda
ENV PATH="/opt/conda/bin:$PATH"

# Copy and create Conda environment from environment.yml
COPY environment.yml /tmp/environment.yml
RUN /opt/conda/bin/conda env create -f /tmp/environment.yml && \
    conda clean -afy

# Set Conda shell to use the new environment
SHELL ["/opt/conda/bin/conda", "run", "-n", "petpipe", "/bin/bash", "-c"]

# Install PETPVC
# https://github.com/UCL/PETPVC

# Install deno v2.2.3
ENV DENO_DIR=/opt/deno_cache
ENV DENO_INSTALL="/opt/.deno"
RUN curl -fsSL https://deno.land/install.sh | sh
ENV PATH="$DENO_INSTALL/bin:$PATH"

# Compile bids-validator v2.0.3
RUN deno compile -ERN -o bids-validator jsr:@bids/validator

# Install workbench command
# The version below is an old version maybe check if there is a new one
# RUN bash -c 'apt-get update && apt-get install -y gnupg2 && wget -O- http://neuro.debian.net/lists/xenial.de-fzj.full | tee /etc/apt/sources.list.d/neurodebian.sources.list && apt-key adv --recv-keys --keyserver hkps://keyserver.ubuntu.com 0xA5D32F012649A5A9 && apt-get update && apt-get install -y connectome-workbench=1.3.2-2~nd16.04+1'

# Install fastsurfer v2.4.2
#  <<<<<<< Code below is from an old version
# ENV PATH="/opt/FastSurfer:$PATH"
# ENV FASTSURFER_HOME=/opt/FastSurfer
# RUN git clone https://github.com/Deep-MI/FastSurfer.git /opt/FastSurfer && cd /opt/FastSurfer && git checkout stable && ls /opt/FastSurfer
# RUN cd /opt/FastSurfer \
#   && bash -c 'wget --no-check-certificate -qO /tmp/miniconda.sh https://repo.continuum.io/miniconda/Miniconda3-py38_4.11.0-Linux-x86_64.sh \
#   && chmod +x /tmp/miniconda.sh \
#   && /tmp/miniconda.sh -b -p /opt/conda \
#   && rm /tmp/miniconda.sh \
#   && conda env create -f ./fastsurfer_env_cpu.yml'

# # Install FastSurferCNN module
# ENV PYTHONPATH="${PYTHONPATH}:/opt/FastSurfer"
# RUN bash -c "source activate fastsurfer_cpu && cd /opt/FastSurfer && python FastSurferCNN/download_checkpoints.py --all && source deactivate"


# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

ENV PATH="/app/functions:$PATH"

# Run the applicationv  <<<<<<<<< This will be the master script in Snake bids
ENTRYPOINT ["/app/functions/petpipe/petpipe.py"]
