#!/bin/sh
# shellcheck shell=busybox

# shellcheck source=../postmarketos-initramfs/init_functions.sh
. ./init_functions.sh
# shellcheck source=../devicepkg-utils/source_deviceinfo
. /usr/share/misc/source_deviceinfo

DID_FAIL=0

echo "==> Running postmarketos-mkinitfs-hook-ci"
echo "==> disabling dmesg on console"
dmesg -n 2

for f in /usr/libexec/pmos-tests-initramfs/*; do
	printf '\n==> Running test "%s"\n\n\n' "$f"
	if $f; then
		echo "==> OK: $f"
	else
		echo "==> FAIL: $f"
		DID_FAIL=1
	fi
done

# FIXME: probably should be the initial loglevel.
echo "==> re-enabling dmesg on console at loglevel 8"
dmesg -n 8

if [ $DID_FAIL -ne 0 ]; then
	echo "==> PMOS-CI-FAIL"
else
	echo "==> PMOS-CI-OK"
fi

# We're done, kill it
# CDBA will exit if it sees 20 '~' characters
# in a row, send a whole bunch just to be sure
# In the worst case it will timeout.
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
