from django.shortcuts import render, redirect
from .models import Session, GroupPin, SessionGroupMap
from django.views import View
from django.contrib import messages
from django.views.generic import ListView, DetailView
from .forms import SessionCreateForm, SessionEnterForm, AudioflForm
from etherpad_app import views as ep_views
from datetime import date, timedelta
import uuid
from django.db import transaction
import jwt
import datetime
from django.conf import settings
# Create your views here.

class SessionListView(ListView):
    """View for listing out learning sessions

    """
    model = Session
    template_name = 'list_session.html'


class SessionDetailView(DetailView):
    """View for displaying dashboard for the session

    """
    model = Session
    template_name = 'detail_session.html'

    def get_context_data(self, **kwargs):
        """Function to expand the context data

        """
        context = super().get_context_data(**kwargs)
        context["no_groups"] = list(range(self.object.groups))
        return context


class SessionCreateView(View):
    """View to create learning session

    """
    form_class = SessionCreateForm
    template_name = 'create_session.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form':form})

    @transaction.atomic
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

            # generate a secure access pin for each pad in the group
            for group in range(groups):
                group += 1
                # generate a random pin and check its existence in the database
                while True:
                    group_pin = uuid.uuid4().hex[:6].upper()
                    group_pin_objects = GroupPin.objects.filter(pin=group_pin)

                    # if the newly generate pin is not in db then break
                    if group_pin_objects.count() == 0:
                        break
                # create an entry in GroupPin table
                gp = GroupPin.objects.create(session=s,
                                            pin=group_pin,
                                            group=group)

            
            # create equal number of pads in Etherpad (one for each group)
            group_name = f'session_{s.id}'
            result = ep_views.create_pads(groups, group_name)

            if result['status'] == 'success':
                group_id = result['group_id']
                sgm = SessionGroupMap.objects.create(session=s,
                                                     eth_groupid=group_id,
                                                     )
                messages.success(self.request, 'Session is created successfully !')
            else:
                messages.error(self.request, 'Error occurred while creating the session !')
            return redirect('session_list')
        else:
            print(form)
            print('Form is not valid')


class SessionEnterView(View):
    """View for displaying entry page for students

    """
    form_class = SessionEnterForm
    template_name = 'enter_session.html'
    pad_template_name = 'student_pad.html'

    def get(self, request, *args, **kwargs):
        """This function displays form to take access pin

        Args:
            request (HttpRequest): request parameter

        """
        form = self.form_class()
        return render(request, self.template_name, {'form':form})
    
    def post(self, request, *args, **kwargs):
        """This function process submitted form's input.

        Args:
            request (HttpRequest): request parameter
        """
        form = self.form_class(request.POST)
        if form.is_valid():
            input_pin = form.cleaned_data.get('pin')

            # check if the pin exists
            valid_pin_objects = GroupPin.objects.all().filter(pin=input_pin)
            if valid_pin_objects.count() == 0:
                messages.error(request, 'Entered pin is invalid.')
                form = self.form_class()
                # redisplaying the enter form with error message
                return render(request, self.template_name, {'form':form})
            else:
                # getting associated session object
                session_object = valid_pin_objects[0].session

                group_number = valid_pin_objects[0].group

                # create a corresponding etherpad user if it does not exists already
                authorid = ep_views.create_etherpad_user({'authorMapper':self.request.user.id,
                                                          'name':self.request.user.first_name}) 

                # access sessiongroupmap 
                session_group_object = SessionGroupMap.objects.get(session=session_object)     

                # access Etherpad groupID associated with the session
                groupid = session_group_object.eth_groupid

                # creating timestamp until when the etherpad will be accessible
                end_timestamp = datetime.datetime.today() + session_object.duration

                # calling etherpad api to generate link to access the writing pad in Etherpad
                sessionID = ep_views.create_session({'authorID':authorid,
                                                     'groupID':groupid,
                                                     'validUntil':end_timestamp.timestamp()})
                # storing sessionID in session object, so that user did not need to enter the pin again
                self.request.session['ethsid'] = sessionID

                # preparing context params 
                audio_form = AudioflForm()

                # pad name
                pad_name = f'session_{session_object.id}_group_{group_number-1}'

                context_data = {'group':groupid,
                                'session':session_object,
                                'form':audio_form,
                                'pad_name':pad_name,
                                'sessionid':sessionID,
                                'etherpad_url':settings.ETHERPAD_URL,
                                'protocol':'http'}

                return render(request, self.pad_template_name, context_data)
        else:
            messages.error(request, 'Form is invalid.')
            form = self.form_class()
            # redisplaying the enter form with error message
            return render(request, self.template_name, {'form':form})