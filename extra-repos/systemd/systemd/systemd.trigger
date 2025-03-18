#!/bin/sh

# All the things we can do even if systemd isn't running

# Update journald catalog
# FIXME: trigger only on /usr/lib/systemd/catalog
journalctl --update-catalog || :

# Update the hwdb if it was modified
# FIXME: trigger only on /usr/lib/udev/hwdb.d
systemd-hwdb update || :

# Process new sysusers
# FIXME: trigger only on /usr/lib/sysusers.d
systemd-sysusers || :

# OK, if systemd isn't running then we're done, else we have more
# to do!

if ! [ -d "/run/systemd/system" ]; then
	exit 0
fi

# Can fail if binfmt_misc is not loaded
# FIXME: trigger only on /usr/lib/binfmt.d
/usr/lib/systemd/systemd-binfmt || :

# Create new tmpfiles
# FIXME: trigger only on /usr/lib/tmpfiles.d
systemd-tmpfiles --create

# FIXME: trigger only on /usr/lib/udev/rules.d
# We can't do this as a trigger for the udevd subpackage because it might
# end up running AFTER the systemd trigger. Urgh!
systemctl set-property systemd-udevd.service Markers=+needs-reload &

# FIXME: trigger only on /usr/lib/sysctl.d
/usr/lib/systemd/systemd-sysctl || :

# FIXME: the rest of this should trigger on. The system and user parts
# could trigger separately but the ordering is still important (systemd
# itself should be reloaded at the system and user level before services
# are reloaded or restarted).
# /usr/lib/systemd/system:/usr/lib/systemd/user:/etc/systemd/system:/etc/systemd/user

# First do a system-wide daemon-reload
systemctl daemon-reload

# And reload the user services. This doesn't do anything yet but will trigger
# a daemon-reexec once we upgrade to systemd 257. See
# https://github.com/systemd/systemd/commit/a375e145190482e8a2f0971bffb332e31211622f
systemctl reload "user@*.service"

# Then reload or restart marked system units. Units get marked in their respective
# package post-upgrade scripts
systemctl reload-or-restart --marked

users=$(systemctl list-units 'user@*' --legend=no | sed -n -r 's/.*user@([0-9]+).service.*/\1/p')
for user in $users; do
	systemctl --user -M "$user@" reload-or-restart --marked &
done
wait
