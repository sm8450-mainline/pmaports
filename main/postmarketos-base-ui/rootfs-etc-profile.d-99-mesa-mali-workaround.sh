#!/bin/sh
if grep -q mediatek, /sys/firmware/devicetree/base/compatible 2>/dev/null; then
	export PAN_MESA_DEBUG=noafbc
fi
