from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import SessionListView, SessionCreateView, SessionDetailView, SessionEnterView
from .views import SessionArchiveView, SessionUpdateView, SessionDuplicateView, SessionArchiveListView
from .views import UploadVADView, UploadSpeechView, UploadAudioView
urlpatterns = [
    path('session/create', login_required(SessionCreateView.as_view()), name='session_create'),
    path('session/edit/<int:pk>/', login_required(SessionUpdateView.as_view()), name='session_edit'),
    path('session/duplicate/<int:pk>/',login_required( SessionDuplicateView.as_view()), name='session_duplicate'),
    path('session/archive/<int:pk>/', login_required(SessionArchiveView.as_view()), name='session_archive'),
    path('session/list', login_required(SessionListView.as_view()), name='session_list'),
    path('session/list/archive', login_required(SessionArchiveListView.as_view()), name='session_list_archive'),
    path('session/show/<int:pk>/', login_required(SessionDetailView.as_view()), name='session_detail'),
    path('session/enter', SessionEnterView.as_view(), name='session_enter'),
    path('vad_upload/', UploadVADView.as_view(), name='upload_vad'),
    path('speech_upload/', UploadSpeechView.as_view(), name='upload_speech'),
    path('audio_upload/', UploadAudioView.as_view(), name='upload_audio'),
]