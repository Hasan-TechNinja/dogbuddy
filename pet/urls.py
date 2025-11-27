from django.urls import path
from . import views

urlpatterns = [
    path('petinfo/', views.PetInfoView.as_view(), name='petinfo'),
    path('status/', views.PetStatusView.as_view(), name='petstatus'),
    path('events/create/', views.EventCreateView.as_view(), name='create_event'),
    path('events/', views.EventListView.as_view(), name='event_detail'),
    path('events/enroll/<int:event_id>/', views.EventEnrollView.as_view(), name='enroll_event'),
    path('events/unenroll/<int:event_id>/', views.EventUnenrollView.as_view(), name='unenroll_event'),
]
