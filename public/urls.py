from django.urls import path
from public.views import get_nationality

urlpatterns = [
    path("get_nationality/", get_nationality, name="nationality"),
]
