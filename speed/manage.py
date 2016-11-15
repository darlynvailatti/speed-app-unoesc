#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault('C_FORCE_ROOT', 'true')
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "speed.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
