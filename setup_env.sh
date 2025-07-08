#!/bin/bash

# Recreate conda env
conda env create -f environment.yaml

# Activate it
conda activate your-env-name

# Install pip requirements
pip install -r requirements.txt
