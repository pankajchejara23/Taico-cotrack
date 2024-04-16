from django.urls import path
from .views import SessionListView
urlpatterns = [
    path('session/create', SessionListView.as_view(), name='create_ehterpad'),
    path('session/list', SessionListView.as_view(), name='pad_list'),
    path('session/show/<int:pk>/', SessionListView.as_view(), name='pad_show')
]