from django.urls import path
from .views import SessionListView, SessionCreateView, SessionDetailView, SessionEnterView
from .views import UploadVADView, UploadSpeechView, UploadAudioView
urlpatterns = [
    path('session/create', SessionCreateView.as_view(), name='session_create'),
    path('session/list', SessionListView.as_view(), name='session_list'),
    path('session/show/<int:pk>/', SessionDetailView.as_view(), name='session_detail'),
    path('session/enter', SessionEnterView.as_view(), name='session_enter'),
    path('vad_upload/', UploadVADView.as_view(), name='upload_vad'),
    path('speech_upload/', UploadSpeechView.as_view(), name='upload_speech'),
    path('audio_upload/', UploadAudioView.as_view(), name='upload_audio'),
]