#!/bin/sh
# systemd.preset reference:
# 	https://www.freedesktop.org/software/systemd/man/latest/systemd.preset.html
# Systemd macro file for RPM:
# 	https://github.com/systemd/systemd/blob/main/src/rpm/macros.systemd.in
# 	https://github.com/systemd/systemd/blob/main/src/rpm/systemd-update-helper.in

SYSTEMD_BUS_TIMEOUT=5s

is_systemd_running() {
	[ -d "/run/systemd/running" ]
}

# runs `systemctl preset` on the list of services of the given type
# $1: type of service, supported values: "user" or "system"
# $@: list of service unit names, as you'd pass to `systemctl preset`
# FIXME: this may not work with wildcards in unit names, and other input you
# can give to the preset command
systemd_service_post_install() {
	local type="$1"
	shift

	if [ -z "$type" ]; then
		echo "service type (user or service) not given"
		exit 1
	fi

	if ! command -v systemctl > /dev/null; then
		echo "systemctl is not available"
		exit 1
	fi

	case "$type" in
		"user")
			systemctl --no-reload preset --global "$@"
			;;
		"system")
			systemctl --no-reload preset "$@" || true
			;;
		*)
			echo "unsupported service type: $type"
		exit 1
	esac
}

# disables the list of services of the given type
# $1: type of service, supported values: "user" or "system"
# $@: list of service unit names, as you'd pass to `systemctl disable`
# FIXME: this may not work with wildcards in unit names, and other input you
# can give to the disable command
systemd_service_pre_deinstall() {
	local type="$1"
	shift

	if [ -z "$type" ]; then
		echo "service type (user/service) not given"
		exit 1
	fi

	if ! command -v systemctl > /dev/null; then
		echo "systemctl is not available"
		exit 1
	fi

	case "$type" in
		"user")
			systemctl --global disable --no-warn "$@"
			if is_systemd_running; then
				local users
				users=$(systemctl list-units 'user@*' --legend=no | sed -n -r 's/.*user@([0-9]+).service.*/\1/p')
				for user in $users; do
					systemctl --user -M "$user@" disable --now --no-warn "$@" &
				done
				wait
			fi
			;;
		"system")
			if is_systemd_running; then
				systemctl --no-reload disable --now --no-warn "$@"
			else
				systemctl --no-reload disable --no-warn "$@"
			fi
			;;
		*)
			echo "unsupported service type: $type"
			exit 1
	esac
}
