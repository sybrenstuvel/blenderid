"""
Some HttpResponse subclasses not defined in Django.
"""

from django.http import HttpResponse


class HttpResponseNoContent(HttpResponse):
    status_code = 204

    def __init__(self, *args, **kwargs):
        super().__init__('', *args, **kwargs)
        del self['content-type']

    @HttpResponse.content.setter
    def content(self, value):
        if value:
            raise AttributeError("You cannot set content to a 204 (No Content) response")


class HttpResponseUnprocessableEntity(HttpResponse):
    status_code = 422
