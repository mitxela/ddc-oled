#!/bin/bash

xrandr --fb 2048x1080 --output eDP-1 --panning 1920x1080/2048x1080
xrandr --setmonitor pointless 128/22x64/11+1920+0 none

function cleanup {
  xrandr --delmonitor pointless
  xrandr --output eDP-1 --auto
}
trap cleanup EXIT

python ssd1306.py
