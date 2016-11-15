#!/bin/sh
cd /home/pi/Documents/speed_project/speed
sudo python manage.py runserver 0.0.0.0:80 > /home/pi/Documents/speed_project/logs/django.log 2>&1 &
