from django.conf.urls import url
from . import views

urlpatterns = [
    url('^$', views.BaseView.as_view(), name="base")
]
