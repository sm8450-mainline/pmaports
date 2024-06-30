#!/usr/bin/env python3
# Copyright 2024 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later

import glob
import tempfile
import sys
import subprocess

# Same dir
import common


def check_kconfig(pkgnames):
    last_failed = None
    for i in range(len(pkgnames)):
        pkgname = pkgnames[i]
        print(f"  ({i+1}/{len(pkgnames)}) {pkgname}")

        p = subprocess.run(["pmbootstrap", "kconfig", "check", pkgname],
                           check=False)

        if p.returncode:
            last_failed = pkgname

    return last_failed


def show_error(last_failed):
    print("")
    print("---")
    print("")
    print("Please adjust your kernel config. This is required for getting your"
          " patch merged.")
    print("")
    print("Edit your kernel config:")
    print(f"  pmbootstrap kconfig edit {last_failed}")
    print("")
    print("Test this kernel config again:")
    print(f"  pmbootstrap kconfig check {last_failed}")
    print("")
    print("Run this check again (on all kernels you modified):")
    print("  pmbootstrap ci kconfig")
    print("")
    print("---")
    print("")


if __name__ == "__main__":
    common.add_upstream_git_remote()
    pkgnames = common.get_changed_kernels()
    print(f"Changed kernels: {pkgnames}")

    if len(pkgnames) == 0:
        print("No kernels changed in this branch")
        exit(0)

    last_failed = check_kconfig(pkgnames)

    if last_failed:
        show_error(last_failed)
        exit(1)
