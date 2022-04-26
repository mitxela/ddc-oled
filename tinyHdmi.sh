#!/bin/bash

# Usage: tinyHdmi.sh [dither [brightness]]
#   dither: 0 or 1
#   brightness: 0 to 255

dev=$(i2cdetect -l | grep "i915 gmbus dpb" | awk '{print $1}')
test $dev || { echo "i2c device not found (i2c-dev module loaded?)"; exit 1; } 

xrandr --fb 2048x1080 --output eDP-1 --panning 1920x1080/2048x1080
xrandr --setmonitor pointless 128/22x64/11+1920+0 none

function cleanup {
  xrandr --delmonitor pointless
  xrandr --output eDP-1 --auto
}
trap cleanup EXIT

python ssd1306.py "/dev/$dev" "${1:-1}" "${2:-120}" 1920 0
