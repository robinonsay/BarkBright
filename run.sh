#!/bin/bash

source venv/bin/activate
python -m barkbright > log-$(date +"%Y-%m-%d-%H-%M-%S").txt 2>&1
