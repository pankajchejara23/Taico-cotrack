from django.shortcuts import render, redirect
from .models import Session
from django.views import View
from django.contrib import messages
from django.views.generic import ListView, DetailView
from .forms import SessionCreateForm
from datetime import date, timedelta

# Create your views here.

class SessionListView(ListView):
    """View for listing out learning sessions

    """
    model = Session
    template_name = 'list_session.html'


class SessionCreateView(View):
    """View to create learning session

    """
    form_class = SessionCreateForm
    template_name = 'create_session.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form':form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get('name')
            groups = form.cleaned_data.get('groups')
            learning_problem = form.cleaned_data.get('learning_problem')
            days = form.cleaned_data.get('duration_days')
            hours = form.cleaned_data.get('duration_hours')
            minutes = form.cleaned_data.get('duration_minutes')
            duration = timedelta(days=days,hours=hours,minutes=minutes)
            language = form.cleaned_data.get('language')
            status = True
            assessment_score = 0
            use_etherpad = True
            record_audio = form.cleaned_data.get('record_audio')
            record_audio_video = form.cleaned_data.get('record_audio_video')
            conf_vad = form.cleaned_data.get('conf_vad')
            conf_speech = form.cleaned_data.get('conf_speech')
            conf_consent = form.cleaned_data.get('conf_consent')

            consent_content = form.cleaned_data.get('consent_content')

            s = Session.objects.create(
                creator = request.user,
                name=name,
                groups=groups,
                language = language,
                duration = duration,
                learning_problem=str(learning_problem),
                status=status,
                assessment_score=assessment_score,
                useEtherpad=use_etherpad,
                record_audio=record_audio,
                record_audio_video=record_audio_video,
                conf_vad=conf_vad,
                conf_speech=conf_speech,
                conf_consent=conf_consent,
                consent_content=consent_content
            )
            messages.success(self.request, 'Session is created successfully !')
            return redirect('session_list')
        else:
            print(form)
            print('Form is not valid')