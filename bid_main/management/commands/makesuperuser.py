"""
Makes a user a superuser. The user must already exist.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Turns a user into a superuser'

    def add_arguments(self, parser):
        parser.add_argument('email')

    def handle(self, *args, **options):
        self.stdout.write('Making %s an admin' % options['email'])

        model = get_user_model()
        try:
            user = model.objects.get(email=options['email'])
        except model.DoesNotExist:
            self.stdout.write(self.style.ERROR('User does not exist; use manage.py createsuperuser instead.'))
            raise SystemExit(1)

        user.is_staff = True
        user.is_superuser = True
        user.save()
        self.stdout.write(self.style.SUCCESS('Done.'))
