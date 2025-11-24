from django.urls import path
from . import views

urlpatterns = [
    path('petinfo/', views.PetInfoView.as_view(), name='petinfo'),
    path('status/', views.PetStatusView.as_view(), name='petstatus')
]
