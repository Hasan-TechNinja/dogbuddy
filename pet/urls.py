from django.urls import path
from . import views

urlpatterns = [
    path('petinfo/', views.PetInfoView.as_view(), name='petinfo'),
]
