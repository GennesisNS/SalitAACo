from django.urls import path

from . import views

urlpatterns = [
    # Named "index" because that is what the rest of the project calls the site's root.
    path('', views.view_home, name='index'),
]
