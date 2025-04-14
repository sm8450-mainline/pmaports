#!/bin/sh
if grep -q qcom, /sys/firmware/devicetree/base/compatible 2>/dev/null; then
	export GSK_RENDERER=ngl
fi
