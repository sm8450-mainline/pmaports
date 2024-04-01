#!/bin/sh

display=off
if xset q | grep -iq "monitor is on"; then
	display=on
fi

case "$display" in
	off)
		xinput enable "TSC2005 touchscreen"
		xset dpms force on
		;;
	on)
		xinput disable "TSC2005 touchscreen"
		xset dpms force off
		;;
esac
