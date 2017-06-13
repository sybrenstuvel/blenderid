#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    if sys.version_info < (3, 6, 0):
        raise ValueError('Python 3.6 or newer is required')

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blenderid.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
