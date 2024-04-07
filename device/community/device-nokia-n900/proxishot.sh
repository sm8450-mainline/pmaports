#!/bin/sh
# Take a screenshot if the proximity sensor is covered.
# NB: pass the user's username in USER_USER environment variable when calling
# this script.
/usr/bin/evtest --query /dev/input/by-path/platform-gpio_keys-event \
	EV_SW SW_FRONT_PROXIMITY
# return value of `10` means the sensor is in the set state, i.e.
# proximity = near. see `man 1 evtest`
if [ "$?" = "10" ]; then
	su "$USER_USER" -c "/bin/mkdir -p ~/Screenshots"
	su "$USER_USER" -c 'cd ~/Screenshots && DISPLAY=:0 /usr/bin/scrot "%Y-%m-%d_%H-%M-%S.png"'
fi
