#!/usr/bin/env python3
# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import sys
import os
import pathlib

# Same dir
import common

# pmbootstrap
import add_pmbootstrap_to_import_path
import pmb.core
import pmb.parse
import pmb.parse._apkbuild
import pmb.helpers.pmaports
from pmb.core.context import get_context


def build_strict(packages, arch):
    common.run_pmbootstrap(["build_init"])
    common.run_pmbootstrap(["--details-to-stdout", "--no-ccache", "build",
                            "--strict", "--force",
                            "--arch", arch, ] + list(packages))


def verify_checksums(packages, arch):
    # Only do this with one build-{arch} job
    arch_verify = "x86_64"
    if arch != arch_verify:
        print(f"NOTE: doing checksum verification in build-{arch_verify} job,"
              " not here.")
        return

    if len(packages) == 0:
        print("no packages changed, not doing any checksums verification")
        return

    common.run_pmbootstrap(["build_init"])
    common.run_pmbootstrap(["--details-to-stdout", "checksum", "--verify"] +
                           list(packages))


if __name__ == "__main__":
    # Architecture to build for (as in build-{arch})
    if len(sys.argv) != 2:
        print("usage: build_changed_aports.py ARCH")
        sys.exit(1)
    arch = sys.argv[1]

    # Get and print modified packages
    common.add_upstream_git_remote()
    packages = common.get_changed_packages()

    # Package count sanity check
    common.get_changed_packages_sanity_check(len(packages))

    # Load context
    sys.argv = ["pmbootstrap.py", "chroot"]
    args = pmb.parse.arguments()
    context = get_context()

    # Get set of all buildable packages for the enabled repos, for skipping unbuildable
    # aports later. We might be given a changed aport from e.g. extra-repos/systemd when
    # that repo is not enabled
    buildable_pkgs = set()
    for path in pmb.core.pkgrepo.pkgrepo_iter_package_dirs():
        buildable_pkgs.add(os.path.basename(path))

    # To store a list of packages from extra-repos/systemd for special handling later:
    systemd_pkgs = list()

    # Filter out packages that either:
    #  1. can't be built for given arch
    #  2. are not found in enabled repos
    # (Iterate over copy of packages, because we modify it in this loop)
    for package in packages.copy():
        if package not in buildable_pkgs:
            print(f"{package}: not in any available repos, skipping")
            packages.remove(package)
            # FIXME: this should probably be more generic, if other repos are added later?
            # This just tosses the package into the list of packages to try building later w/ systemd enabled, and assumes it'll be found there.
            systemd_pkgs.append(package)
            continue

        apkbuild_path = pmb.helpers.pmaports.find(package)
        apkbuild = pmb.parse._apkbuild.apkbuild(pathlib.Path(apkbuild_path, "APKBUILD"))

        if not pmb.helpers.pmaports.check_arches(apkbuild["arch"], arch):
            print(f"{package}: not enabled for {arch}, skipping")
            packages.remove(package)

    # No packages: skip build
    if len(packages) == 0:
        print(f"no packages changed, which can be built for {arch}")

    else:
        verify_only = common.commit_message_has_string("[ci:skip-build]")
        if verify_only:
            # [ci:skip-build]: verify checksums and stop
            print("WARNING: not building changed packages ([ci:skip-build])!")
            print("verifying checksums: " + ", ".join(packages))
            verify_checksums(packages, arch)
        else:
            # Build packages
            print(f"building in strict mode for {arch}: {', '.join(packages)}")
            build_strict(packages, arch)

    # Build packages in extra-repos/systemd
    # FIXME: this should probably be more generic, if other repos are added later?
    if systemd_pkgs:
        common.run_pmbootstrap(["config", "systemd", "always"])

        verify_only = common.commit_message_has_string("[ci:skip-build]")
        if verify_only:
            # [ci:skip-build]: verify checksums
            print("WARNING: not building changed packages for extra-repos/systemd: ([ci:skip-build])!")
            print("verifying checksums: " + ", ".join(packages))
            verify_checksums(systemd_pkgs, arch)
        else:
            # Build packages
            print(f"building in strict mode for {arch}, from extra-repos/systemd: {', '.join(packages)}")
            build_strict(systemd_pkgs, arch)
