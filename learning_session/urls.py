from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import SessionListView, SessionCreateView, SessionDetailView, SessionEnterView
from .views import SessionArchiveView, SessionUpdateView, SessionDuplicateView, SessionArchiveListView, SessionListAdminView
from .views import UploadVADView, UploadSpeechView, UploadAudioView, RoleRequestView, RoleRequestListView, GrantRoleView, UserCreateView
from .views import DownloadVadView, DownloadSpeechView, DownloadLogsView
urlpatterns = [
    path('session/create', login_required(SessionCreateView.as_view()), name='session_create'),
    path('session/edit/<int:pk>/', login_required(SessionUpdateView.as_view()), name='session_edit'),
    path('session/duplicate/<int:pk>/',login_required( SessionDuplicateView.as_view()), name='session_duplicate'),
    path('session/archive/<int:pk>/', login_required(SessionArchiveView.as_view()), name='session_archive'),
    path('session/list', login_required(SessionListView.as_view()), name='session_list'),
    path('session/list/admin', login_required(SessionListAdminView.as_view()), name='session_list_admin'),
    path('session/list/archive', login_required(SessionArchiveListView.as_view()), name='session_list_archive'),
    path('session/show/<int:pk>/', login_required(SessionDetailView.as_view()), name='session_detail'),
    path('session/enter', SessionEnterView.as_view(), name='session_enter'),
    path('vad_upload/', UploadVADView.as_view(), name='upload_vad'),
    path('speech_upload/', UploadSpeechView.as_view(), name='upload_speech'),
    path('audio_upload/', UploadAudioView.as_view(), name='upload_audio'),
    path('request/send', RoleRequestView.as_view(), name='request_send'),
    path('request/list', RoleRequestListView.as_view(), name='request_list'),
    path('role/assing', GrantRoleView.as_view(), name='grant_role'),
    path('user/create', UserCreateView.as_view(), name='create_user'),
    path('download/vad/<int:pk>', DownloadVadView.as_view(), name='download_logs'),
    path('download/speech/<int:pk>', DownloadSpeechView.as_view(), name='download_logs'),
    path('download/logs/<int:pk>', DownloadLogsView.as_view(), name='download_logs'),

]