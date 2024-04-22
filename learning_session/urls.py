from django.urls import path
from .views import SessionListView, SessionCreateView, SessionDetailView, SessionEnterView
urlpatterns = [
    path('session/create', SessionCreateView.as_view(), name='session_create'),
    path('session/list', SessionListView.as_view(), name='session_list'),
    path('session/show/<int:pk>/', SessionDetailView.as_view(), name='session_detail'),
    path('session/enter', SessionEnterView.as_view(), name='session_enter')
]