#!/usr/bin/env python3
# Copyright 2025 Pablo Correa Gomez
# SPDX-License-Identifier: GPL-3.0-or-later

from functools import cached_property
from pathlib import Path
from typing import Self
import sys
import traceback

from jinja2 import Template
import pmb.parse
from pmb.parse.deviceinfo import Deviceinfo
from pmb.types import Apkbuild
import pmb.helpers.devices
import pmb.helpers.logging
import pmb.helpers.package
from pmb.core.arch import Arch

# Same dir
import common


class Device:
    def __init__(self, codename: str):
        self.codename = codename
        self.full_path = pmb.helpers.devices.find_path(codename)

    def __repr__(self):
        return f"Device({self.codename})"

    @property
    def name(self):
        return self.full_path.name.removeprefix("device-")

    @cached_property
    def gitlab_ci_fragment(self) -> str | None:
        fragment_path = self.full_path / "gitlab-ci.yml.j2"
        try:
            fragment_tmpl = fragment_path.read_text()
        except Exception:
            return None

        return Template(fragment_tmpl).render(device=self)

    @property
    def is_present_in_ci(self):
        return bool(self.gitlab_ci_fragment)

    @cached_property
    def pmaports_path(self) -> Path:
        # Find the root of pmaports
        pmaports_root = self.full_path.parent
        while (not (pmaports_root / "pmaports.cfg").exists() and
               pmaports_root != pmaports_root.root):
            pmaports_root = pmaports_root.parent
        assert pmaports_root != pmaports_root.root

        return self.full_path.relative_to(pmaports_root)

    @cached_property
    def apkbuild(self) -> Apkbuild:
        return pmb.parse.apkbuild(self.full_path)

    @property
    def pkgname(self) -> str:
        return self.apkbuild['pkgname']

    @property
    def arch(self) -> Arch:
        return Arch(self.apkbuild['arch'][0])

    @property
    def testing_dependencies(self) -> set[str]:
        # TODO: Source this from the APKGBUILD
        return {"postmarketos-mkinitfs-hook-ci"}

    @cached_property
    def package_dependencies(self) -> list[str]:
        # HACK: Work around a bug in depends_recurse which prevents listing all the dependencies
        # Bug: https://gitlab.postmarketos.org/postmarketOS/pmbootstrap/-/issues/2623
        return {"postmarketos-initramfs"}
        # return pmb.helpers.package.depends_recurse(pkgname=self.pkgname,
        #                                            arch=self.arch)

    @cached_property
    def dependencies(self) -> set[str]:
        return self.package_dependencies | self.testing_dependencies

    @cached_property
    def kernels(self) -> list[str] | None:
        kernels = []

        subpackage_prefix = f"device-{self.codename}-kernel-"
        for subpkgname in self.apkbuild.get('subpackages', []):
            if not subpkgname.startswith(subpackage_prefix):
                continue
            kernel_name = subpkgname.removeprefix(subpackage_prefix)

            # Ignore `none` kernels as they are not bootable
            if kernel_name != "none":
                kernels.append(kernel_name)

        if kernels:
            return kernels
        else:
            return None

    @cached_property
    def deviceinfo(self) -> dict[str, Deviceinfo] | Deviceinfo:
        # NOTE: deviceinfo files that have different values per kernel are
        # currently unsupported due to a gitlab-ci issue which prevents us
        # from having a per-kernel list of variables that would be selected
        # using `.extends`:
        # https://gitlab.com/gitlab-org/gitlab/-/issues/299423
        return Deviceinfo(self.full_path / "deviceinfo", None)

    @property
    def has_kernel_variants(self):
        return len(self.kernels) > 0

    @classmethod
    def supported_devices(cls) -> dict[Path, Self]:
        # NOTE: Not sure I like relying on pmboostrap just to avoid listing
        # devices ourselves, but since we need it to parse the APKBUILD, then
        # let's avoid duplicating the logic?
        supported_devices = {}
        for vendor in pmb.helpers.devices.list_vendors():
            for device in pmb.helpers.devices.list_codenames(vendor):
                try:
                    dev = cls(device.codename)

                    # Ignore devices that do not have a gitlab ci fragment,
                    # since we won't be able to make use of them
                    if not dev.gitlab_ci_fragment:
                        continue

                    supported_devices[dev.pmaports_path] = dev
                except Exception:
                    traceback.print_exc()
        return supported_devices


class ArchTagSet(set):
    supported_arches = [
        Arch.x86_64,
        Arch.x86,
        Arch.aarch64,
        Arch.armv7,
        Arch.armhf,
        Arch.riscv64,
    ]

    def update(self, iterable):
        # This ignores things like !armv7, that could be a follow-up optimization
        if 'noarch' in iterable or 'all' in iterable:
            iterable = [arch for arch in self.supported_arches]
        super().update([Arch(arch) for arch in iterable if Arch(arch) in self.supported_arches])


if __name__ == "__main__":
    # Needs input to output if we should create the jobs
    if len(sys.argv) != 3:
        print("usage: generate_build_jobs.py TEMPLATE CHILD_PIPELINE")
        print(sys.argv)
        sys.exit(1)
    template = sys.argv[1]
    child_pipeline = sys.argv[2]

    # pmb logging has to be initialized for later pmb commands to work, setting
    # to /dev/null since we don't care about the output. Later this could
    # be changed to a file and added as a CI artifact if we need to debug
    # something.
    pmb.logging.init(Path("/dev/null"), False)

    # Load context
    sys.argv = ["pmbootstrap.py", "chroot"]
    args = pmb.parse.arguments()

    # Get the list of supported devices
    supported_devices = Device.supported_devices()

    archs = ArchTagSet()
    devices_under_test = set()
    packages_modified = set()
    # Get and print modified packages
    common.add_upstream_git_remote()
    for file in common.get_changed_files():
        path = Path(file)

        # Check if the modified's file parent folder is one of a supported dev
        if device := supported_devices.get(path.parent):
            devices_under_test.add(device)

        if path.name != "APKBUILD":
            continue
        elif not path.exists():
            continue  # APKBUILD was deleted
        apkbuild = pmb.parse.apkbuild(path)
        packages_modified.add(apkbuild['pkgname'])
        archs.update(apkbuild["arch"])

        # Add all the devices found in CI that depend on the package that got
        # modified
        for device in supported_devices.values():
            if apkbuild['pkgname'] in device.dependencies:
                devices_under_test.add(device)

    if common.commit_message_has_string("[ci:skip-build]"):
        print("User requested skipping build, not creating child pipeline file")
        archs = ArchTagSet()
        devices_under_test = set()

    print(f"Architectures to build: {archs}")
    print(f"Devices under test: {devices_under_test}")

    with open(template) as f:
        rendered = Template(f.read()).render(
            archs=archs,
            devices_under_test=devices_under_test,
            packages_modified=packages_modified,
            archtag={
                Arch.x86_64: "shared",
                Arch.x86: "shared",
                Arch.aarch64: "arm64",
                Arch.armv7: "qemu",
                Arch.armhf: "qemu",
                Arch.riscv64: "qemu",
            },
        )
        with open(child_pipeline, "w") as fw:
            fw.write(rendered)
