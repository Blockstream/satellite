#!/bin/bash

# Check if the build directory exists
if [ ! -d ./gr-mods/build ]; then
  mkdir ./gr-mods/build
fi

cd ./gr-mods/build
cmake ..
make
sudo make install

