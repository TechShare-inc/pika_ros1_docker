#!/bin/bash
# This script is an example generated at TechShare Corporation.
# It starts double pika multi-sensor, including two depth cameras and two fisheye cameras in ROS environment.

camera_fps=10
camera_width=640
camera_height=480
l_depth_camera_no=315122272259
r_depth_camera_no=315122272142

l_serial_port=/dev/ttyUSB50
r_serial_port=/dev/ttyUSB51
sudo chmod a+rw /dev/ttyUSB*
l_fisheye_port=50
r_fisheye_port=51
sudo chmod a+rw /dev/video*

source /opt/ros/noetic/setup.bash && cd $HOME/pika_ros/install/share/sensor_tools/scripts && chmod 777 usb_camera.py
if [ -n "$1" ]; then
    source $HOME/pika_ros/install/setup.bash && roslaunch sensor_tools open_multi_sensor.launch l_depth_camera_no:=$l_depth_camera_no r_depth_camera_no:=$r_depth_camera_no l_serial_port:=$l_serial_port r_serial_port:=$r_serial_port l_fisheye_port:=$l_fisheye_port r_fisheye_port:=$r_fisheye_port camera_fps:=$camera_fps camera_width:=$camera_width camera_height:=$camera_height name:=$1 name_index:=$1_
else
    source $HOME/pika_ros/install/setup.bash && roslaunch sensor_tools open_multi_sensor.launch l_depth_camera_no:=$l_depth_camera_no r_depth_camera_no:=$r_depth_camera_no l_serial_port:=$l_serial_port r_serial_port:=$r_serial_port l_fisheye_port:=$l_fisheye_port r_fisheye_port:=$r_fisheye_port camera_fps:=$camera_fps camera_width:=$camera_width camera_height:=$camera_height
fi
                