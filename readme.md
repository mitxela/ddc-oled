# DDC-OLED

Use an SSD1306 OLED display as a secondary monitor by piping video to it over the DDC bus. This is a total hack and by far the worst way to get a second monitor.

This demo will only work on Linux using X11, and requires the `i2c-dev` kernel module loaded. Assuming your primary display is called eDP-1, has a resolution of 1920x1080, and you want to place this tiny monitor to the right of it:
```
xrandr --fb 2048x1080 --output eDP-1 --panning 1920x1080/2048x1080
xrandr --setmonitor virtual 128/22x64/11+1920+0 none
```
Then run the python script. __Make sure the right i2c device is selected on the second line of the python script before running it.__ 

To undo:
```
xrandr --delmonitor virtual
xrandr --output eDP-1 --auto
```
More info: https://mitxela.com/projects/ddc-oled

PyXCursor from here: https://github.com/zorvios/PyXCursor (modified to also return xhot and yhot)
