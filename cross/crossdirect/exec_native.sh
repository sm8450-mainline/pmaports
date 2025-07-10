#!/bin/sh -e
# Execute the binary from the native chroot if it is installed there. This is
# done for archiver tools such as unxz, so they don't need to go through QEMU.

# Try /native first, then the foreign arch paths. Never try
# /native/usr/lib/crossdirect as this would result in a loop.
UNWRAPPED_PATH="/native/usr/bin:/native/usr/sbin:/native/sbin:/native/bin:/usr/bin:/usr/sbin:/sbin:/bin"

BASENAME="$(basename "$0")"
UNWRAPPED_BIN="$(PATH="$UNWRAPPED_PATH" command -v "$BASENAME")"

case "$UNWRAPPED_BIN" in
	/native/*)
		export LD_LIBRARY_PATH="/native/usr/lib:/native/lib"
		export PATH="$UNWRAPPED_PATH"
		;;
esac

exec "$UNWRAPPED_BIN" "$@"
