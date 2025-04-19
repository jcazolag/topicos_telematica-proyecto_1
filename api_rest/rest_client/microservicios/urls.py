from django.urls import path
from .views import micro_1

app_name = "microservicios"

urlpatterns = [
    path("micro-one/", micro_1, name="micro-one")
]