# DDC-OLED

Use an SSD1306 OLED display as a secondary monitor by piping video to it over the DDC bus. This is a total hack and by far the worst way to get a second monitor.

This demo will only work on Linux using X11, and requires the `i2c-dev` kernel module loaded.

__Update:__ Command line options for dither and brightness have been added, and the script now only updates the parts of the display which have changed.

I've added a wrapper script which handles the xrandr framebuffer setup and teardown, and attempts to determine the i2c device number based on its name as output by `i2cdetect -l` (or `cat /sys/class/i2c-dev/*/device/name`). In my case, that's `i915 gmbus dpb`. The script assumes the primary display is named eDP-1 and has a resolution of 1920x1080. You should definitely read through/modify the script before running it.

More info: https://mitxela.com/projects/ddc-oled

PyXCursor from here: https://github.com/zorvios/PyXCursor (modified to also return xhot and yhot)
