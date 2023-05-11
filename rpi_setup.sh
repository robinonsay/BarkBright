#!/bin/bash

sudo apt update && sudo apt upgrade
sudo apt install python-all-dev python3-venv python3-pip pulseaudio portaudio19-dev git espeak make gcc g++ vim
git clone https://github.com/robinonsay/BarkBright.git && cd BarkBright
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r rpi_requirements.txt
touch config.json
echo "{}" >> config.json
touch dataset/dataset.json
echo "[]" >> dataset/dataset.json
cd barkbright/models/assets
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
cd ../../../


