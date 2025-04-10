"""
URL configuration for taico_cotrack project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import TemplateView
from .views import change_language
from learning_session.views import UploadVADView, UploadSpeechView, UploadAudioView

urlpatterns = i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("users.urls")),
    path("", include("etherpad_app.urls")),
    path("", include("learning_session.urls")),
    path('about/',TemplateView.as_view(template_name="about.html"), name='about'),
    path('features/',TemplateView.as_view(template_name="features.html"), name='features'),
    path("ckeditor/", include('ckeditor_uploader.urls')),
)

# Adding upload paths without i18
urlpatterns += [path('vad_upload/', UploadVADView.as_view(), name='upload_vad'),
                path('speech_upload/', UploadSpeechView.as_view(), name='upload_speech'),
                path('audio_upload/', UploadAudioView.as_view(), name='upload_audio')
                ]
urlpatterns += [path('i18n/', include("django.conf.urls.i18n"))]
urlpatterns += [ path('change-lang/<lang_code>', change_language, name='change_language')]
urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
urlpatterns += [path('accounts/', include('allauth.urls'))]