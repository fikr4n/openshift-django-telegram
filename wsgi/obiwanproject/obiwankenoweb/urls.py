from django.conf.urls import url

from . import views

app_name = 'obiwan'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^update/$', views.update, name='update'),
]
