#!/bin/sh -e
# Description: run apkbuild-lint on modified APKBUILDs
# Options: native
# Use 'native' because it requires git commit history.
# https://postmarketos.org/pmb-ci

if [ "$(id -u)" = 0 ]; then
	set -x
	wget "https://gitlab.postmarketos.org/postmarketOS/ci-common/-/raw/master/install_pmbootstrap.sh"
	sh ./install_pmbootstrap.sh
	exec su "${TESTUSER:-pmos}" -c "sh -e $0"
fi

.ci/lib/apkbuild_linting.py
