#!/usr/bin/env python3
# Copyright 2024 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later

import fnmatch
import glob
import os
import pytest
import sys

import add_pmbootstrap_to_import_path
import pmb.parse
import pmb.parse._apkbuild
from pmb.core.pkgrepo import pkgrepo_default_path, pkgrepo_iglob, pkgrepo_relative_path
from pmb.core.arch import Arch

# Don't complain if these nicknames are the only maintainers of an APKBUILD,
# because they are actually a group of people
gitlab_groups = [
    "@sdm845-mainline",
]


def device_dependency_check(apkbuild, path):
    """ Raise an error if a device package has a dependency that is not allowed
        (e.g. because it should be in a subpackage instead). """

    for depend in apkbuild["depends"]:
        if depend == "mesa-dri-gallium":
            raise RuntimeError(f"{path}: mesa-dri-gallium shouldn't be in"
                               " depends anymore (see pmaports!3478)")


def test_aports_device():
    """
    Various tests performed on the /device/*/device-* aports.
    """
    for path in pkgrepo_iglob("device/*/device-*/APKBUILD"):
        apkbuild = pmb.parse.apkbuild(path)

        # Depends: Require "postmarketos-base"
        depend_flag = False
        for dependency in apkbuild["depends"]:
            if "postmarketos-base" == dependency or "postmarketos-base>" in dependency:
                depend_flag = True
        if not depend_flag:
            raise RuntimeError(f"Missing 'postmarketos-base' in depends of {path}")

        # Depends: Must not have specific packages
        for depend in apkbuild["depends"]:
            device_dependency_check(apkbuild, path)

        # Architecture
        device = apkbuild["pkgname"][len("device-"):]
        deviceinfo = pmb.parse.deviceinfo(device)
        if Arch.from_str("".join(apkbuild["arch"])) != deviceinfo.arch:
            raise RuntimeError("wrong architecture, please change to arch=\""
                               f"{deviceinfo.arch}\": {path}")
        if "!archcheck" not in apkbuild["options"]:
            raise RuntimeError(f"!archcheck missing in options= line: {path}")


def test_aports_device_kernel():
    """
    Verify the kernels specified in the device packages:
    * Kernel must not be in depends when kernels are in subpackages
    * Check if only one kernel is defined in depends
    """
    aports = pkgrepo_default_path()
    # Iterate over device aports
    for path in aports.glob("device/*/device-*/APKBUILD"):
        # Parse apkbuild and kernels from subpackages
        apkbuild = pmb.parse.apkbuild(path)
        device = apkbuild["pkgname"][len("device-"):]
        kernels_subpackages = pmb.parse._apkbuild.kernels(device)

        # Parse kernels from depends
        kernels_depends = []
        for depend in apkbuild["depends"]:
            if not depend.startswith("linux-") or depend.startswith("linux-firmware-"):
                continue
            kernels_depends.append(depend)

            # Kernel in subpackages *and* depends
            if kernels_subpackages:
                raise RuntimeError(f"Kernel package '{depend}' needs to"
                                   " be removed when using kernel" +
                                   f" subpackages: {path}")

        # No kernel
        if not kernels_depends and not kernels_subpackages:
            raise RuntimeError("Device doesn't have a kernel in depends or"
                               f" subpackages: {path}")

        # Multiple kernels in depends
        if len(kernels_depends) > 1:
            raise RuntimeError("Please use kernel subpackages instead of"
                               " multiple kernels in depends (see"
                               f" <https://postmarketos.org/devicepkg>): {path}")


# @pytest.mark.xfail # Not all aports have been updated yet
def test_aports_maintained():
    """
    Ensure that aports in /device/{main,community} have "Maintainer:" and
    "Co-Maintainer:" (only required for main) listed in their APKBUILDs.
    """

    for path in pkgrepo_iglob("device/main/*/APKBUILD"):
        if 'firmware-' in path.parent.name:
            continue
        maintainers = pmb.parse._apkbuild.maintainers(path)
        assert maintainers and len(maintainers) >= 2, \
            f"{path} in main needs at least 1 Maintainer and 1 Co-Maintainer"

    for path in pkgrepo_iglob("device/community/*/APKBUILD"):
        if 'firmware-' in path.parent.name:
            continue
        maintainers = pmb.parse._apkbuild.maintainers(path)
        assert maintainers, f"{path} in community needs at least 1 Maintainer"


def test_aports_unmaintained():
    """
    Ensure that aports in /device/unmaintained have an "Unmaintained:" comment
    that describes why the aport is unmaintained.
    """

    for path in pkgrepo_iglob("device/unmaintained/*/APKBUILD"):
        unmaintained = pmb.parse._apkbuild.unmaintained(path)
        assert unmaintained, f"{path} should have an Unmaintained: " +\
            "comment that describes why the package is unmaintained"
