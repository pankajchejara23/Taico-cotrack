from django.urls import path
from .views import PadCreateFormView, PadListView, PadDetailView
urlpatterns = [
    path('etherpad-ui/create', PadCreateFormView.as_view(), name='create_ehterpad'),
    path('etherpad-ui/list', PadListView.as_view(), name='pad_list'),
    path('etherpad-ui/show/<int:pk>/', PadDetailView.as_view(), name='pad_show')
]