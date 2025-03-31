#!/usr/bin/env python3
# Copyright 2025 Pablo Correa Gomez
# SPDX-License-Identifier: GPL-3.0-or-later

# Same dir
import common

def verify_checksums(packages):
    if len(packages) == 0:
        print("no packages changed, not doing any checksums verification")
        return

    print("verifying checksums: " + ", ".join(packages))
    common.run_pmbootstrap(["build_init"])
    common.run_pmbootstrap(["--details-to-stdout", "checksum", "--verify"] +
                           list(packages))

if __name__ == "__main__":
    # Get and print modified packages
    common.add_upstream_git_remote()
    packages = common.get_changed_packages()
    verify_checksums(packages)
