from django.urls import path
from .views import PadCreateFormView
urlpatterns = [
    path('etherpad-ui/create', PadCreateFormView.as_view(), name='create_ehterpad')
]