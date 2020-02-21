#!/bin/bash
set -e

if [ "$1" == "-u" ]; then
	# Upgrade sources and re-install
	cd ~/src/tbsdriver/
	cd media
	git remote update
	git pull
	cd ../media_build
	git remote update
	git pull
	make
	sudo make install
else
	sudo apt-get update
	sudo apt-get install make gcc git patch patchutils libproc-processtable-perl
	sudo apt-get install linux-headers-$(uname -r)

	mkdir -p ~/src
	cd ~/src
	mkdir -p tbsdriver
	cd tbsdriver
	git clone https://github.com/tbsdtv/media_build.git
	git clone --depth=1 https://github.com/tbsdtv/linux_media.git -b latest ./media

	# Build media drivers
	cd media_build
	make dir DIR=../media
	make allyesconfig
	#make distclean
	make -j4
	# Delete the previous Media Tree installation
	sudo rm -rf /lib/modules/`uname -r`/kernel/drivers/media/*
	# Install the new one
	sudo make install

	# Install firmware
	cd ../
	wget http://www.tbsdtv.com/download/document/linux/tbs-tuner-firmwares_v1.0.tar.bz2
	sudo tar jxvf tbs-tuner-firmwares_v1.0.tar.bz2 -C /lib/firmware/
fi
