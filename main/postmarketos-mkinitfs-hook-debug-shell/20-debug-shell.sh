#!/bin/sh
# shellcheck disable=SC1091
. ./init_functions.sh
. /usr/share/misc/source_deviceinfo
TELNET_PORT=23

setup_usb_network
start_unudhcpd

show_splash "WARNING: debug-shell is active\\nhttps://postmarketos.org/debug-shell"

echo "Create 'pmos_continue_boot' script"
{
	echo "#!/bin/sh"
	#Disable any active usb mass storage
	echo "if [ -d /config/usb_gadget/g1/functions/mass_storage.0 ]; then setup_usb_storage; fi"
	echo "pkill -9 -f pmos_shell"
	echo "pkill -f pmos_fail_halt_boot"
} >/usr/bin/pmos_continue_boot
chmod +x /usr/bin/pmos_continue_boot

echo "Create 'pmos_shell' script"
{
	echo "#!/bin/sh"
	echo "sh"
} >/usr/bin/pmos_shell
chmod +x /usr/bin/pmos_shell

echo "Create 'pmos_fail_halt_boot' script"
{
	echo "#!/bin/sh"
	echo '. /init_functions.sh'
	echo "fail_halt_boot"
} >/usr/bin/pmos_fail_halt_boot
chmod +x /usr/bin/pmos_fail_halt_boot

echo "Create debug-shell cleanup script"
{
	echo "#!/bin/sh"
	# shellcheck disable=SC2016
	echo 'kill `cat /run/debug-shell-telnet.pid`'
} > /hooks-cleanup/debug-shell-cleanup.sh
chmod +x /hooks-cleanup/debug-shell-cleanup.sh

echo "Start the telnet daemon"
{
	echo "#!/bin/sh"
	echo "echo \"Type 'pmos_continue_boot' to continue booting:\""
	echo "sh"
} >/telnet_connect.sh
chmod +x /telnet_connect.sh

host_ip="${unudhcpd_host_ip:-172.16.42.1}"
# Run telnetd with -F (foreground) instead of as a daemon so we can get it's PID
telnetd -F -b "${host_ip}:${TELNET_PORT}" -l /telnet_connect.sh &
echo "$!" > /run/debug-shell-telnet.pid

# mount pstore, if possible
if [ -d /sys/fs/pstore ]; then
	mount -t pstore pstore /sys/fs/pstore || true
fi
# mount debugfs - very helpful for debugging
mount -t debugfs none /sys/kernel/debug || true
# make a symlink like Android recoveries do
ln -s /sys/kernel/debug /d

echo "---"
echo "WARNING: debug-shell is active on ${host_ip}:${TELNET_PORT}."
echo "This is a security hole! Only use it for debugging, and"
echo "uninstall the debug-shell hook afterwards!"
echo "You can expose storage devices using 'setup_usb_storage /dev/DEVICE'"
echo "---"

pmos_shell

# Show "Loading" splash again when continuing
show_splash "Loading..."
