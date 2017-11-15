"""blenderid URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
import django.contrib.staticfiles.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'', include('bid_addon_support.urls', namespace='addon_support')),
    url(r'^oauth/', include('blenderid.oauth2_urls', namespace='oauth2_provider')),
    url(r'^api/', include('bid_api.urls', namespace='bid_api')),
    url(r'', include('bid_main.urls', namespace='bid_main')),
]

import bid_main.views
handler400 = bid_main.views.ErrorView.as_view(template_name='errors/400.html', status=400)
handler403 = bid_main.views.ErrorView.as_view(template_name='errors/403.html', status=403)
handler404 = bid_main.views.ErrorView.as_view(template_name='errors/404.html', status=404)
handler500 = bid_main.views.ErrorView.as_view(template_name='errors/500.html', status=500)


if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
        url(r'^static/(?P<path>.*)$', django.contrib.staticfiles.views.serve),
    ]
