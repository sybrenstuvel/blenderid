from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.views.generic import View


class AbstractAPIView(View):
    """Excempted from CSRF requests and never cached."""

    @method_decorator(csrf_exempt)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
