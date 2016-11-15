#!/bin/sh
cd /home/pi/Documents/speed_project/speed/
python manage.py celeryd -l info > /home/pi/Documents/speed_project/logs/celery.log 2>&1 &
