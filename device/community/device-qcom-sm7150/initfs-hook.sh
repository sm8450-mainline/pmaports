#!/bin/sh

# Some devices (xiaomi-surya) ship with a touchscreen that has no persistent
# firmware storage. That is unfortunate and means we need to provide firmware
# from the initramfs for FDE to work.
# This is only the case for the novatek touchscreens. Their firmware resides
# in /vendor/firmware. Let's copy it over.
# The file names are novatek_ts_huaxing_fw.bin and novatek_ts_tianma_fw.bin,
# for both panels respectively.

for input in /sys/class/input/input*/uevent
do
	if grep -q "NT36XXX" "$input"
	then
		echo "nt36xxx is loaded, mounting firmware for it!"

		mkdir /firmware-mnt

		for part in /sys/block/sd*/sd*
		do
			DEVNAME="$(grep DEVNAME "$part"/uevent | sed 's/DEVNAME=//g')"
			PARTNAME="$(grep PARTNAME "$part"/uevent | sed 's/PARTNAME=//g')"

			# Could be vendor_a or vendor_b
			if [[ "$PARTNAME" == "vendor"* ]]
			then
				mount -o ro,nodev,noexec,nosuid \
					"/dev/$DEVNAME" /firmware-mnt
				break
			# Super partition with vendor on a subpartition, system if retrofit
			elif [[ "$PARTNAME" == "super" ]] || [[ "$PARTNAME" == "system" ]]
			then
				if ! make-dynpart-mappings "/dev/$DEVNAME"; then continue; fi;

				for dynpart in /dev/mapper/*
				do
					if [[ "$dynpart" == *"vendor"* ]]
					then
						mount -o ro,nodev,noexec,nosuid \
							"$dynpart" /firmware-mnt
						break 2
					fi
				done
			fi
		done

		if [ -d /firmware-mnt/firmware ]
		then
			for firmware_file in /firmware-mnt/firmware/novatek_ts_*_fw.bin
			do
				echo "Found novatek firmware file at $firmware_file"

				cp $firmware_file /lib/firmware/
			done

			umount /firmware-mnt
		fi

		break
	fi
done
