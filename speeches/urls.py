from django.urls import path

from . import views

app_name = "speeches"

urlpatterns = [
    path("choose/", views.pick, name="choose"),
    path("obama/", views.obama, name="obama"),
    path("lincoln/", views.lincoln, name="lincoln"),
    # path("trump/", views.trump, name="trump"),
]
