#! /bin/bash
sudo apt-get install libatlas-base-dev -y
pip install matplotlib
pip install numpy -y 
sudo apt install ./digilent.adept.runtime_2.27.9-armhf.deb -y
sudo apt install ./digilent.waveforms_3.19.5_armhf/deb -y
sudo apt-get update -y
sudo apt-get install libopenblas-base -y
