#!/bin/sh

# This is a stub to work around cyclical dependencies in CI while we migrate away from this script.

is_systemd_running() {
	return 1
}

systemd_service_post_install() {
	echo "NOP systemd_service_post_install"
}

systemd_service_pre_deinstall() {
	echo "NOP systemd_service_pre_deinstall"
}
