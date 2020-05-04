#!/bin/bash

DNF_CMD=$(which dnf)
APT_CMD=$(which apt-get)

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
	if [[ ! -z $DNF_CMD ]]; then
		sudo dnf install -y make gcc git patch patchutils \
			 perl-Proc-ProcessTable \
			 perl-Digest-SHA \
			 "kernel-devel-uname-r == $(uname -r)" \
			 kernel-headers
	elif [[ ! -z $APT_CMD ]]; then
		sudo apt-get update
		sudo apt-get install -y make gcc git patch patchutils \
			 libproc-processtable-perl \
			 linux-headers-$(uname -r)
	else
		echo "Can't find DNF or APT package manager"
		echo "Please follow driver installation instructions at https://github.com/tbsdtv/linux_media/wiki"
		exit 1;
	fi

	mkdir -p ~/src
	cd ~/src
	mkdir -p tbsdriver
	cd tbsdriver
	if [ ! -d "media_build" ] ; then
		git clone https://github.com/tbsdtv/media_build.git
	fi
	if [ ! -d "media" ] ; then
		git clone --depth=1 https://github.com/tbsdtv/linux_media.git -b latest ./media
	fi

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
	wget https://www.tbsdtv.com/download/document/linux/tbs-tuner-firmwares_v1.0.tar.bz2
	sudo tar jxvf tbs-tuner-firmwares_v1.0.tar.bz2 -C /lib/firmware/
fi
