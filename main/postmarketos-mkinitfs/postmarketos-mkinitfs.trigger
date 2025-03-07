#!/bin/sh -e
# This script fails on error (-e). We don't want an error while generating the
# initramfs to go unnoticed, it may lead to the device not booting anymore.

# Conditionally run mkinitfs:
# * Only invoke mkinitfs if the deviceinfo exists in the rootfs.
# * Don't run mkinitfs inside "pmbootstrap install" with this trigger script,
#   as it would trigger multiple times as the rootfs gets constructed, slowing
#   down the process. Instead, pmbootstrap runs "mkinitfs" explicitly once at
#   the end of "pmbootstrap install".
if [ -f /usr/share/deviceinfo/deviceinfo ] && ! [ -f /in-pmbootstrap ]; then
	/usr/sbin/mkinitfs
fi
