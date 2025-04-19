from django.urls import path, include

app_name = "api"

urlpatterns = [
    path("microservicios/", include('microservicios.urls'), name="microservicios"),
]