from django.urls import path
from .views import SessionListView, SessionCreateView
urlpatterns = [
    path('session/create', SessionCreateView.as_view(), name='session_create'),
    path('session/list', SessionListView.as_view(), name='session_list'),
    path('session/show/<int:pk>/', SessionListView.as_view(), name='session_show')
]