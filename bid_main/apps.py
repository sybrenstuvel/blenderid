from django.apps import AppConfig


class BidMainConfig(AppConfig):
    name = 'bid_main'
    verbose_name = 'Blender-ID'

    def ready(self):
        # Just import for the side-effects.
        from . import signals
        assert signals
