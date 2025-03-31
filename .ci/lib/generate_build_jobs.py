#!/usr/bin/env python3
# Copyright 2025 Pablo Correa Gomez
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path
import shutil
import sys

from jinja2 import Template
import add_pmbootstrap_to_import_path
import pmb.parse
import pmb.helpers.logging
from pmb.core.arch import Arch

# Same dir
import common

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
    archs = set()
    # Get and print modified packages
    common.add_upstream_git_remote()
    for file in common.get_changed_files():
        path = Path(file)
        if path.name != "APKBUILD":
            continue
        elif not path.exists():
            continue  # APKBUILD was deleted
        apkbuild = pmb.parse.apkbuild(path)
        archs.update(apkbuild["arch"])

    if common.commit_message_has_string("[ci:skip-build]"):
        print("User requested skipping build, not creating child pipeline file")
        archs = set()

    # This ignores things like !armv7, that could be a follow-up optimization
    if 'noarch' in archs or 'all' in archs:
        archs = set([str(arch) for arch in Arch.supported()])

    print(archs)
    with open(template) as f:
        rendered = Template(f.read()).render(archs=archs)
        with open(child_pipeline, "w") as fw:
            fw.write(rendered)
