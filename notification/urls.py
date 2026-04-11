from django.urls import path
from . import views

urlpatterns = [
    path('register-fcm-token/', views.RegisterFCMTokenView.as_view(), name='register_fcm_token'),
    path('', views.NotificationListView.as_view(), name='notification_list'),
    path('<int:notification_id>/', views.NotificationDetailView.as_view(), name='notification_detail'),
]
