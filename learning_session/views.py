from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.http import HttpResponseForbidden
from .models import Session, GroupPin, SessionGroupMap, VAD, Speech, Audiofl, RoleRequest, Consent
from django.views import View
from django.contrib import messages
from django.core.files.base import File
from django.views.generic import ListView, DetailView, UpdateView, CreateView
from .forms import SessionCreateForm, SessionEnterForm, AudioflForm, VADForm, SpeechForm, SessionUpdateForm 
from .forms import ConsentForm, RoleRequestForm, GrantTeacherRoleForm, UserCreateForm, UserBulkCreateForm
from etherpad_app import views as ep_views
from datetime import date, timedelta
import uuid
import numpy as np
from django.db import transaction
from django.urls import reverse
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.mixins import LoginRequiredMixin
import jwt
import io
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import urllib, base64
from io import StringIO
import csv
import datetime
from django.conf import settings
from django.utils.translation import gettext as _
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from .apps import ApiConfig
import pandas as pd

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
User = get_user_model()

from etherpad_app.models import call, Pad, PadGroup
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from django.db.models import Sum
from etherpad_app.models import Pad

VAD_OBJECTS = []
SPEECH_OBJECTS = []

COLORS = ["rgba(31, 119, 180, 0.8)",
         "rgba(255, 127, 14, 0.8)",
         "rgba(44, 160, 44, 0.8)",
         "rgba(214, 39, 40, 0.8)",
         "rgba(148, 103, 189, 0.8)",
         "rgba(140, 86, 75, 0.8)",
         "rgba(227, 119, 194, 0.8)",
         "rgba(127, 127, 127, 0.8)",
         "rgba(188, 189, 34, 0.8)",
         "rgba(23, 190, 207, 0.8)",
         "rgba(31, 119, 180, 0.8)",
         "rgba(255, 127, 14, 0.8)",
         "rgba(44, 160, 44, 0.8)",
         "rgba(214, 39, 40, 0.8)",
         "rgba(148, 103, 189, 0.8)",
         "rgba(140, 86, 75, 0.8)",
         "rgba(227, 119, 194, 0.8)",
         "rgba(127, 127, 127, 0.8)",
         "rgba(188, 189, 34, 0.8)",
         "rgba(23, 190, 207, 0.8)",
         "rgba(31, 119, 180, 0.8)",
         "rgba(255, 127, 14, 0.8)",
         "rgba(44, 160, 44, 0.8)",
         "rgba(214, 39, 40, 0.8)",
         "rgba(148, 103, 189, 0.8)",
         "rgba(140, 86, 75, 0.8)",
         "rgba(227, 119, 194, 0.8)",
         "rgba(127, 127, 127, 0.8)",
         "rgba(188, 189, 34, 0.8)",
         "rgba(23, 190, 207, 0.8)",
         "rgba(31, 119, 180, 0.8)",
         "rgba(255, 127, 14, 0.8)",
         "rgba(44, 160, 44, 0.8)",
         "rgba(214, 39, 40, 0.8)",
         "rgba(148, 103, 189, 0.8)"]

def generate_pin(s, g):
    """This function generates a unique pin code

    Args:
        s (Session): Session object
        g (int): Group number

    """

    # iterate until a unique group pin (which is not already used) is generated.
    while True:
        # generate a unique identifier and use 6 chars
        u_pin = uuid.uuid4().hex[:6].upper()

        # check if the generated pin already used or not
        objs = GroupPin.objects.filter(pin = u_pin)

        # if not used then break
        if objs.count() == 0:
            break
    sg = GroupPin.objects.create(session=s,pin=u_pin,group=g)
    return

def after_login_page(request):
    if request.user.is_staff:
        redirect('session_list')
    else:
        redirect('session_enter')


class StaffRequiredMixin(UserPassesTestMixin):
    """This mixin put an access restriction on some views

    Args:
        UserPassesTestMixin (_type_): _description_
    """
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        return HttpResponseForbidden("You do not have permission to access this page.")


class SessionUpdateView(StaffRequiredMixin,UpdateView):
    """This view allows editing of Session objects.

    """
    model = Session
    template_name = 'update_session.html'
    success_url = 'session_list'
    form_class = SessionUpdateForm

    def update_group_pin(self, org_groups, new_groups):
        """This function updates the group pins according to new value.

        Args:
            org_groups (int): number of groups before update
            new_groups (int): number of groups after update
        """

        # don't do anything if the number of groups are not changed
        if org_groups == new_groups:
            return
        
        # computing difference between new and original number of groups
        group_diff = new_groups - org_groups

        # if the updated number of groups is higher than old value
        if (group_diff > 0):
            for g in range(group_diff):
                g =  g +  org_groups + 1
                generate_pin(self.object, g)
        else:
            group_diff = abs(group_diff)
            for g in range(group_diff):
                del_group = g + new_groups + 1
                GroupPin.objects.filter(session=self.object,group=del_group).delete()
        return 

    
    def get_initial(self):
        """This function adds initial values for duration days, hours, minutes.

        Returns:
            dict: dictionary of initial values for the form
        """
        initial_values = super().get_initial()
        initial_values['new'] = self.object.groups
        initial_values['duration_days'] = self.object.duration.days
        initial_values['duration_hours'] = self.object.duration.seconds // 3600
        initial_values['duration_minutes'] =  ( self.object.duration.seconds // 60) % 60
        return initial_values
    
    def form_valid(self, form):
        """This form executes when the submitted form is valid.

        Args:
            form (SessionUpdateForm): form object with submitted values
        Returns:
            HttpResponseRedirect: redirect user to success url
        """
        self.object = form.save(False)
        org_groups = form.cleaned_data.get('new')
        new_groups = form.cleaned_data.get('groups')
        self.object.duration = timedelta(days=form.cleaned_data.get('duration_days'),
                                         hours=form.cleaned_data.get('duration_hours'),
                                         minutes=form.cleaned_data.get('duration_minutes'))
        
        session_groupmap = SessionGroupMap.objects.filter(session = self.object)
        group_name = f'session_{self.object.id}'
        etherpad_groupid = session_groupmap[0].eth_groupid
        self.update_group_pin(org_groups, new_groups)
        status = ep_views.update_pads(etherpad_groupid, group_name, org_groups, new_groups)
        if status:
            self.object.save()
            messages.success(self.request, _('Session is updated.'))
        else:
            messages.error(self.request, _('There are some errors while updating pads in Etherpad.'))
            
        return HttpResponseRedirect(reverse_lazy(self.get_success_url()))


class SessionListView(StaffRequiredMixin,UserPassesTestMixin,ListView):
    """View for listing out learning sessions

    """
    model = Session
    template_name = 'list_session.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        """This function update the queryset which returns the objects for listview.

        Returns:
            queryset: queryset containing objects
        """
        queryset = super().get_queryset()
        queryset = queryset.filter(status=True).filter(creator = self.request.user)
        return queryset


class GrantTeacherRoleView(StaffRequiredMixin,ListView):
    """View for displaying role requests

    """
    template_name = 'user_list.html'
    model = User


class SessionListAdminView(ListView):
    """View for listing out all learning sessions (which are not archived)

    """
    model = Session
    template_name = 'list_session.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(status=True)
        return queryset


class SessionArchiveListView(StaffRequiredMixin,ListView):
    """View for listing out archived learning sessions

    """
    model=Session
    template_name = 'list_session.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(status=False).filter(creator=self.request.user)
        return queryset


class SessionArchiveView(StaffRequiredMixin,View):
    """This view handles archiving of sessions.

    """
    def get(self, request, *args, **kwargs):
        """This function archives the learning session.

        """
        # id of session to archive
        id = self.kwargs['pk']

        # fetch the session
        session_object = Session.objects.get(id=id)

        # changing  status to False 
        session_object.status=False

        # save the session
        session_object.save()
        messages.success(self.request, _('Session is archived.'))
        return redirect('session_list')


class SessionDuplicateView(StaffRequiredMixin,View):
    """This view handles duplicate and archive actions.

    """
    def get(self, request, *args, **kwargs):
        """This function create a duplicate session.

        Args:
            request (HttpRequest): request parameter

        """
        # id of the session to be duplicated
        id = self.kwargs['pk']

        # fetcht the session
        session_object = Session.objects.get(id=id)

        # setting the primary key to None causes creation of a new object at save
        session_object.id = None
        session_object.save()

        groups = session_object.groups
        # generate a secure access pin for each pad in the group
        for group in range(groups):
            group += 1
            generate_pin(session_object, group) ### @todo: Here new session object needs to be passed

        # create equal number of pads in Etherpad (one for each group)
        group_name = f'session_{session_object.id}'
        result = ep_views.create_pads(groups, group_name)

        if result['status'] == 'success':
            group_id = result['group_id']
            sgm = SessionGroupMap.objects.create(session=session_object,
                                                     eth_groupid=group_id,
                                                     )
            messages.success(self.request, _('Session is duplicated successfully !'))
        else:
                messages.error(self.request, _('Error occurred while duplicating the session !'))
        return redirect('session_list')


class SessionDetailView(StaffRequiredMixin,DetailView):
    """View for displaying dashboard for the session

    """
    model = Session
    template_name = 'detail_session.html'

    def get_context_data(self, **kwargs):
        """Function to expand the context data

        Args:
            request (HttpRequest): request parameter
        """
        context = super().get_context_data(**kwargs)

        # adding number of groups
        context["no_groups"] = list(range(self.object.groups))
        return context


class SessionCreateView(StaffRequiredMixin,View):
    """View to create learning session

    """
    form_class = SessionCreateForm
    template_name = 'create_session.html'

    def get(self, request, *args, **kwargs):
        """Function to render session create form
            
        Args:
            request (HttpRequest): request parameter
        """
        form = self.form_class()
        return render(request, self.template_name, {'form':form})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # populate the form with submittted response
        form = self.form_class(request.POST)

        # form validity check
        if form.is_valid():
            # fetching data
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

            # create a session object
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
                messages.success(self.request, _('Session is created successfully !'))
            else:
                messages.error(self.request, _('Error occurred while creating the session !'))
            return redirect('session_list')
        else:
            print('Form is not valid')


class SessionEnterView(LoginRequiredMixin,View):
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

                # adding information about session and group
                payload = {'session': session_object.id,
                           'group':group_number}
                encoded_payload = jwt.encode(payload, settings.JW_SEC, algorithm='HS256')
                request.session['payload'] = encoded_payload

                return redirect('session_consent')
        else:
            messages.error(request, 'Form is invalid.')
            form = self.form_class()
            # redisplaying the enter form with error message
            return render(request, self.template_name, {'form':form})


class SessionLeaveView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        if 'payload' in self.request.session.keys():
            del self.request.session['payload']
        return redirect('session_enter')
    

class SessionGroupAnalyticsView(StaffRequiredMixin,View):
    """View for displaying dashboard for a particular group

    """
    template_name = 'group_analytics.html'

    def get(self, request, *args, **kwargs):
        """This function return group dashboard page.

        Args:
            request (HttpRequest): HttpRequest object
            session (Session): Session object
            group (int): Group number

        """
        session_id = self.kwargs['pk']
        group_number = self.kwargs['gk']

        # fetch the corresponding session object
        session_object = Session.objects.filter(id=session_id).first()

        # fetch sesssion group map
        session_group_map = SessionGroupMap.objects.filter(session=session_object).first()

        # This is the id of Pad object (e.g., 1,2,3 etc.)
        padid = ep_views.get_padid(session_group_map.eth_groupid,group_number)

        ethid = Pad.objects.get(id=padid).eth_padid

        print(f'Requested pad info:  ID:{padid}  Eth:{ethid}')

        # fetch etherpad group
        context_data = {
                        'group':group_number,
                        'session':session_object,
                        'padid':padid,
                        'protocol':settings.PROTOCOL,
                        'server':settings.SERVER_URL,
                        'group_sequence':group_number-1,
                        'ethid':ethid
                        }
        return render(request, self.template_name, context_data)


class StudentPadView(LoginRequiredMixin,View):
    """This view shows etherpad to student.

    """
    template_name = 'student_pad.html'
    def get(self, request, *args, **kwargs):
        """This function forwards the user to the etherpad view

        Args:
            request (HttpRequest): HttpRequest object
            session (Session): Session object
            group (int): Group number
            audio_form (AudioForm): Audio form to collect audio data during group activity
            pad_name (str): Name of the pad
            eth_sessionid (str): Etherpad session id
        """

        # check if request has a session data stored in the key 'payload'
        if 'payload' not in request.session.keys():
            return redirect('session_enter')

        # access the payload and decode it to get session id and group number.
        decoded_payload = jwt.decode(self.request.session['payload'], settings.JW_SEC, algorithms=["HS256"])
        session_id = decoded_payload['session']
        group_number = decoded_payload['group']

        # fetch the corresponding session object
        session_object = Session.objects.filter(id=session_id).first()

        # call to fetch the etherpad user's id for the corresponding user (create if doesn't exists)
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
        audio_form = AudioflForm()  # this form used to store audio data on server

        # pad name
        pad_name = f'{groupid}$session_{session_object.id}_group_{group_number}'

        context_data = {'group':group_number,
                        'session':session_object,
                        'sessionj':session_object,
                        'form':audio_form,
                        'pad_name':pad_name,
                        'sessionid':sessionID,
                        'etherpad_url':settings.ETHERPAD_URL,
                        'protocol':settings.ETHERPAD_PROTOCOL,
                        'server':settings.SERVER_URL}

        return render(request, self.template_name, context_data)


class ConsentView(LoginRequiredMixin,View):
    """This view shows the consent form and handles student's response.

    """
    form_class = ConsentForm
    template_name = 'consent.html'

    def post(self, request, *args, **kwargs):
        """This function handles user's response to consent.

        Args:
            request (HttpRequest): request parameter
        """
        form = self.form_class(request.POST)

        # check if payload is in session dict
        if 'payload' in request.session.keys():

            # decode payload and access session id and group number
            decoded_payload = jwt.decode(request.session['payload'], settings.JW_SEC, algorithms=["HS256"])
            session_id = decoded_payload['session']
            group_number = decoded_payload['group']

            # fetch corresponding session object
            session_objects = Session.objects.filter(id=session_id)

            # check if session object exists
            if session_objects.count() == 0:
                del request.sesssion['payload']
                return redirect('session_enter')
            else:
                session_object = Session.objects.get(id=session_id)
                if form.is_valid():
                    consent = form.cleaned_data.get('permission')

                    # save user's response to consent form
                    Consent.objects.create(session = session_object, user = request.user, permission=consent)
                    return redirect('session_student')
                else:
                    # if form is not valid then returnt the user to consent again.
                    form = self.form_class()
                    consent_content = session_object.consent_content
                    return render(request, self.template_name, {'form':form, 'consent_content':consent_content})
        else:
            return redirect('session_enter')
                
    def get(self, request, *args, **kwargs):
        """This function displays form to take user's input on the consent form.

        Args:
            request (HttpRequest): request parameter
        """
        if 'payload' in request.session.keys():
            # decode payload and access session id and group number
            decoded_payload = jwt.decode(request.session['payload'], settings.JW_SEC, algorithms=["HS256"])
            session_id = decoded_payload['session']
            group_number = decoded_payload['group']

            session_object = Session.objects.filter(id=session_id).first()

            # return consent if it is configured in the session otherwise redirect to the pad.
            if session_object.conf_consent:
                form = self.form_class()
                consent_content = session_object.consent_content
                return render(request, self.template_name, {'form':form, 'consent_content':consent_content})
            else:
                return redirect('session_student')
        else:
            return redirect('session_enter')


class UploadVADView(LoginRequiredMixin,View):
    """View for handling audio data processing and storing on server

    """
    form_class = VADForm
    def post(self, request, *args, **kwargs):
        """This function stores voice activity detection data on server.

        Args:
            request (HttpRequest): request parameter
        """
        form = self.form_class(request.POST)
        print('-----VAD-----',form)
        if form.is_valid():
            # fetch data from submitted form
            session = form.cleaned_data.get("session")
            user = form.cleaned_data.get("user")
            group = form.cleaned_data.get("group")

            # start time of voice activity in milliseconds
            strDate = form.cleaned_data.get("strDate")

            # duration of the voice activity
            activity = form.cleaned_data.get("activity")

            # start time converstion to seconds
            strDate = (int)(float(strDate)/1000)

            # converting timestamp from seconds to date and time
            dt = datetime.datetime.fromtimestamp(strDate)

            print(form)
            
            # saving voice activity detection data in database
            VAD.objects.create(session=session,user=user,group=group,timestamp=dt,activity=activity)
            print('Vad object saved')
            return HttpResponse('Done')
        else:
            return HttpResponse('Error')


class UploadSpeechView(LoginRequiredMixin,View):
    """View for handling speech-to-text conversion and storing on server

    """
    form_class = SpeechForm
    def post(self, request, *args, **kwargs):
        """This function stores speech-to-text data on server.

        Args:
            request (HttpRequest): request parameter
        """
        form = self.form_class(request.POST)
        if form.is_valid():
            # fetch data from submitted form
            session = form.cleaned_data.get("session")
            user = form.cleaned_data.get("user")
            group = form.cleaned_data.get("group")

            # start time of voice activity in milliseconds
            strDate = form.cleaned_data.get("strDate")

            # speech-to-text data
            speech = form.cleaned_data.get("TextField")

            # start time converstion to seconds
            strDate = (int)(float(strDate)/1000)

            # converting timestamp from seconds to date and time
            dt = datetime.datetime.fromtimestamp(strDate)
            
            # saving voice activity detection data in database
            Speech.objects.create(session=session,user=user,group=group,timestamp=dt,TextField=speech)
            print('Speech object saved')
            return HttpResponse('Done')
        

class UploadAudioView(LoginRequiredMixin,View):
    """View for handling audio files storing on server

    """
    form_class = AudioflForm
    def post(self, request, *args, **kwargs):
        """This function stores audio data files on server.

        Args:
            request (HttpRequest): request parameter
        """
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            # timestamp in milliseconds
            strDate = form.cleaned_data.get("strDate")

            # timestamp in seconds
            strDate = (int)(float(strDate)/1000)

            # timestamp in datetime format
            dt = datetime.datetime.fromtimestamp(strDate)

            # changing default saving of the form
            newform = form.save(commit=False)

            # assigning start time
            newform.started_at = dt

            # fetching audio (or audio/video) file content
            djfile = File(request.FILES['data_blob'])

            # saving the file on the server
            newform.fl.save(request.FILES['data_blob'].name,djfile)

            # saving the form's data
            newform.save()
            return HttpResponse('Done')
        

class RoleRequestView(LoginRequiredMixin,View):
    """View for displaying and hanlding role request form

    """
    model = RoleRequest
    form_class = RoleRequestForm
    template_name = 'role_request.html'
    success_url = '/session/list'

    def get(self, request, *args, **kwargs):
        """This function shows the form to make a request for teacher's role.

        Args:
            request (HttpRequest): request parameter
        """
        form = self.form_class()

        # save only if the request does not exists alredy
        roles = RoleRequest.objects.filter(user=self.request.user)
        if roles.count() !=0:
            messages.error(request, 'You already made a request.')
            return HttpResponseRedirect(self.success_url)
        else:
            return render(request, self.template_name, {'form':form})

    def post(self, request, *args, **kwargs):
        """This function handles the role request form submission.

        Args:
            request (HttpRequest): request parameter
        """
        form = self.form_class(request.POST)
        if form.is_valid():
            role = form.save(commit=False)
            role.user = self.request.user
            role.decision = False
            role.pending = True
            role.save()
            messages.success(request, _('Your request have been registered.'))
            return HttpResponseRedirect(self.success_url)
        else:
            return render(request, self.template_name, {'form':form})


class RoleRequestListView(StaffRequiredMixin,ListView):
    """View for displaying all role requests.

    """
    model = RoleRequest
    template_name = 'role_list.html'


class GrantRoleView(View):
    """View for granting teacher's role to the users.

    """
    form_class = GrantTeacherRoleForm    
    template_name = 'grant_request.html'
    success_url = '/session/list/admin'

    def get(self, request, *args, **kwargs):
        """This function displays form to take admin's action.

        Args:
            request (HttpRequest): request parameter
        """
        form = self.form_class()
        return render(request, self.template_name, {'form':form})
    
    def post(self, request, *args, **kwargs):
        """This function performs role granting action.

        Args:
            request (HttpRequest): request parameter
        """
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.cleaned_data.get('user')
            staff = form.cleaned_data.get('staff')

            # get corresponding user object
            user_object = User.objects.get(id=user.id)

            user_object.is_active = True
            # using is_active as a flag to determine teacher's role
            user_object.is_staff = staff
            user_object.save()
            messages.success(request, f'User <strong>{user.email}</strong> has been assigned teacher role.')
        else:
            return render(request, self.template_name, {'form':form})
        return HttpResponseRedirect(self.success_url)
    

class UserCreateView(View):
    """View for creating new user accounts.

    """
    form_class = UserCreateForm  
    template_name = 'create_user.html'
    success_url = '/session/list'

    def get(self, request, *args, **kwargs):
        """This function shows user creation form.

        Args:
            request (HttpRequest): request parameter
        """
        form = self.form_class()
        return render(request, self.template_name, {'form':form})
    
    def post(self, request, *args, **kwargs):
        """This function handles submission of user creation form.

        Args:
            request (HttpRequest): request parameter
        """
        form = self.form_class(request.POST)
        print(form)
        if form.is_valid():
            # fetching submitted data
            user = form.cleaned_data.get('name')
            email = form.cleaned_data.get('email')
            pwd = form.cleaned_data.get('password')
            staff = form.cleaned_data.get('staff')

            # create a new user
            user_object = User.objects.create_user(username = user,email = email,password = pwd)
            print('Setting is_staff to',staff)
            # set is_staff status
            user_object.is_staff = staff
            user_object.is_active = True
            user_object.save()
            messages.success(request, f'User acocunt for <strong>{user_object.email}</strong> has been created.')
        else:
            return render(request, self.template_name, {'form':form})
        return HttpResponseRedirect(self.success_url)


class UserBulkCreateView(View):
    """View for creating new user accounts.

    """
    form_class = UserBulkCreateForm  
    template_name = 'create_bulk_users.html'
    success_url = '/session/list'

    def get(self, request, *args, **kwargs):
        """This function shows user creation form.

        Args:
            request (HttpRequest): request parameter
        """
        form = self.form_class()
        return render(request, self.template_name, {'form':form})
    
    def post(self, request, *args, **kwargs):
        """This function handles submission of user creation form.

        Args:
            request (HttpRequest): request parameter
        """
        form = self.form_class(request.POST)
        if form.is_valid():
            # fetching submitted data
            prefix = form.cleaned_data.get('prefix')
            pwd = form.cleaned_data.get('password')
            how_many = form.cleaned_data.get('how_many')

            # create a new user
            for user_number in range(1,how_many+1):
                user = f'{prefix}_{user}'
                email = f'{prefix}_{user}@demo.ee'

                user_object = User.objects.create_user(username = user,email = email,password = pwd)
                user_object.is_active = True
                user_object.save()
            messages.success(request, f'{how_many} Users accounts are created.<br/> user-name : {prefix}_N  (here N is a number from 1 to {how_many}<br/>  password:{pwd}')
        else:
            return render(request, self.template_name, {'form':form})
        return HttpResponseRedirect(self.success_url)

class RoleRequestAction(StaffRequiredMixin,View):
    """View to handle role request actions
    
    """
    def get(self, request, *args, **kwargs):
        """This function handles role request action.

        Args:
            request (HttpRequest): request parameter
        """
        # type of action (grant or reject)
        action = kwargs['action']

        # id of role request
        role_request_id = kwargs['pk']

        # only if the current user is admin
        if request.user.is_superuser:
            # fetch corresponding role request object
            role_request_object = RoleRequest.objects.get(id=role_request_id)

            # grant action
            if action == 'grant':
                user = role_request_object.user
                user.is_staff = True
                user.save()

                # setting the request status as processed
                role_request_object.pending = False
                messages.success(request, _('Request has been approved.'))
                role_request_object.save()
            
            # reject action
            if action == 'reject':
                # setting the request status as processed
                role_request_object.pending = False
                role_request_object.save()
                messages.success(request, _('Request has been declined.'))
        return HttpResponseRedirect(reverse('request_list'))



# Download data views
class DownloadVadView(StaffRequiredMixin,View): 
    """View to download VAD data
    
    """
    def get(self, request, *args, **kwargs):
        """This function fetches vad data and prepares a CSV file.

        Args:
            request (HttpRequest): request parameter
        """
        # get session id
        session_id = kwargs['pk']

        # filter session on id
        sessions = Session.objects.all().filter(id=session_id)

        # if session exists
        if sessions.count() == 0:
            messages.error(request, _('Invalid session id'))
            return HttpResponseRedirect('/session/list')
        else:
            session = Session.objects.get(id=session_id)

            # Preparing csv data File
            fname = session.name + '_vad.csv'
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment;filename="' + fname +'"'

            # csv writer object
            writer = csv.writer(response)
            writer.writerow(['timestamp','user','group','speaking_time(sec.)'])

            # fetching vad objects for specified session
            vads = VAD.objects.filter(session=session).distinct().order_by('timestamp')

            # writing data from vad objects into csv file
            for v in vads:
                writer.writerow([v.timestamp,
                                 v.user.authormap.authorid,
                                 v.group,(v.activity/1000)])

            return response
        

class DownloadSpeechView(StaffRequiredMixin,View): 
    """View to download Speech data
    
    """
    def get(self, request, *args, **kwargs):
        """This function fetches speech data and prepares a CSV file.

        Args:
            request (HttpRequest): request parameter
        """
        # get session id
        session_id = kwargs['pk']

        # filter session on id
        sessions = Session.objects.all().filter(id=session_id)

        # if session exists
        if sessions.count() == 0:
            messages.error(request, _('Invalid session id'))
            return HttpResponseRedirect('/session/list')
        else:
            session = Session.objects.get(id=session_id)

            # Preparing csv data File
            fname = session.name + '_speech.csv'
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment;filename="' + fname +'"'

            # csv writer object
            writer = csv.writer(response)
            writer.writerow(['timestamp','user','group','speech'])

            # fetching speech objects for specified session
            objs = Speech.objects.all().filter(session=session).distinct()
            for obj in objs:
                writer.writerow([obj.timestamp,
                                 obj.user.authormap.authorid,
                                 obj.group,obj.TextField])

            return response

class DownloadLogsView(StaffRequiredMixin,View): 
    """View to download Logs data
    
    """
    def get(self, request, *args, **kwargs):
        """This function fetches logs data and prepares a CSV file.

        Args:
            request (HttpRequest): request parameter
        """
        # get session id
        session_id = kwargs['pk']

        # filter session on id
        sessions = Session.objects.all().filter(id=session_id)

        # if session exists
        if sessions.count() == 0:
            messages.error(request, _('Invalid session id'))
            return HttpResponseRedirect('/session/list')
        else:
            session = Session.objects.get(id=session_id)
            session_map = SessionGroupMap.objects.get(session=session)

            # Preparing csv data File
            fname = session.name + '_logs.csv'
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment;filename="' + fname +'"'

            # csv writer object
            writer = csv.writer(response)
            writer.writerow(['timestamp',
                             'author',
                             'group',
                             'char_bank',
                             'changeset',
                             'source_length',
                             'operation',
                             'difference',
                             'text'])

            # access all associated pads' logs
            logs = ep_views.download_logs(session_map.eth_groupid)
            for log in logs:
                writer.writerow(log)
            return response


#### REST API START ###############

@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def getRevCount(request,ethid):
    """This function returns number of revisions made in the pad of given padid.
    @url: /getRevCount/<padid>
    Args:
        request (HttpRequest): request object
        padid (str): Etherpad pad id

    Returns:
        Response: number of revision counts
    """

    params = {'padID':ethid}
    rev_count = call('getRevisionsCount',params)
    return Response({'revisions':rev_count['data']['revisions']})


@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def getWordCloud(request,session_id,group_id):
    """
    This function returns word-cloud for a given group of a session.

    Args:
        request (HttpRequest): request object
        session_id (int): Session id
        group_id (int): Group id

    Returns:
        Response: image of word-cloud
    
    """
    stopwords = set(STOPWORDS)
    session = Session.objects.get(id=session_id)
    speeches = Speech.objects.all().filter(session = session, group = group_id).values_list('TextField',flat=True)
    speeches = " ".join(speech for speech in speeches)
    print(speeches)
    if len(speeches) == 0:
        data = {'data':'empty'}
    else:
        wc = WordCloud(background_color = 'white', max_words=2000, stopwords = stopwords)
        """
        new code
        """
        fig2, ax = plt.subplots(1,1,figsize=(6,8))
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])
        cloud = wc.generate(speeches)
        print('Word cloud generated')
        ax.imshow(wc,interpolation ='bilinear')

        """
        fig = plt.figure(figsize=(6,8))
        cloud = wc.generate(speeches)
        print('Word cloud generated')
        plt.imshow(wc,interpolation ='bilinear')
        plt.axis('off')
        """
        image = io.BytesIO()
        fig2.savefig(image,format="png")
        image.seek(0)
        string = base64.b64encode(image.read())
        #image_64 =  urllib.parse.quote(string)
    data = {'data':str(string.decode())}
    print('Returning:',data)
    return Response(data)

# for building edge list with weight
def edgeExist(edge_list,edge):
    for e in edge_list:
        if e[0] == edge[0] and e[1] == edge[1]:
            return True
        #if e[0] == edge[1] and e[1] == edge[0]:
        #    return True
    return False

def updateWeight(edge_list, edge):
    updated = list()
    for i,e in enumerate(edge_list):
        if edgeExist([edge],e):
            w = edge_list[i][2] + 1
            updated.append((e[0],e[1],w))
        else:
            updated.append(e)
    return updated

def getEdgeWidth(edge_weight, total_weight):
    percentage = int(edge_weight * 100/total_weight)
    if percentage >= 90:
        return 24
    elif percentage >= 80:
        return 22
    elif percentage >= 70:
        return 19
    elif percentage >= 60:
        return 15
    elif percentage >= 50:
        return 13
    elif percentage >= 40:
        return 11
    elif percentage >= 30:
        return 10
    elif percentage >= 20:
        return 8
    elif percentage >= 10:
        return 5
    elif percentage >= 6:
        return 4
    elif percentage >= 4:
        return 3
    else:
        return 1

# function to get elements for cytoscape.js to draw network
def generateElements(user_sequence,speaking_data,session,group):

    try:
        color_mapping,t = getUsers(session,group)
    except:
        color_mapping = {}

    total_speaking = sum(speaking_data.values())
    avg_speaking = 0
    if len(speaking_data.values()) != 0:
        avg_speaking = total_speaking/len(speaking_data.values())
    if sum(speaking_data.values()) == 0:
        total_speaking = 1

    per_speaking = [float(i)/total_speaking for i in speaking_data]
    #### create edge list_files
    edge_list = list()

    total_weight = 0
    # Create two variable node1 and node2 and set them to zero.
    node1=node2=0
    # Iterate over resultant users sequences
    for i in range(len(user_sequence)):
        # For the first element
        if node1==0:
            # set node1 to the first element
            node1=user_sequence[i]
        # For rest of the elements
        else:
            # Set the current element to node2
            node2=user_sequence[i]
            if node1 != node2:
                total_weight = total_weight +  1
                # Append the edge node1, node2 to the edge list
                if edgeExist(edge_list,(node1,node2)):
                    edge_list = updateWeight(edge_list,(node1,node2))

                else:

                    edge_list.append((node1,node2,5))
            node1=node2
    ele_nodes=[]
    total_edges = len(edge_list)

    for n in set(user_sequence):
        user_obj = User.objects.get(pk = n)
        #speak_ratio = 200*sp_time[n]/total_sp
        ratio = float(speaking_data[n]/total_speaking)
        node_width = 10 + 100 * ratio

        if len(color_mapping) !=0:
            t = {'id':n,'name':user_obj.first_name,'color':color_mapping[n],'size':node_width,'ratio':ratio}
        else:
            t = {'id':n,'name':user_obj.first_name,'size':node_width,'ratio':ratio}
        ele_nodes.append(t)
    ele_edges = []
    for e in edge_list:
        edge_width = getEdgeWidth(e[2],total_weight)
        t = {'source':e[0],'to':e[1],'weight':edge_width}
        ele_edges.append(t)
    elements = {'nodes':ele_nodes,'edges':ele_edges}
    return elements


def gini(array):
    """Calculate the Gini coefficient of a numpy array."""
    # based on bottom eq: http://www.statsdirect.com/help/content/image/stat0206_wmf.gif
    # from: http://www.statsdirect.com/help/default.htm#nonparametric_methods/gini.htm
    if array.size == 0:
        return '--'

    array = array.flatten() #all values are treated equally, arrays must be 1d
    if np.amin(array) < 0:
        array -= np.amin(array) #values cannot be negative
    array += 0.0000001 #values cannot be 0
    array = np.sort(array) #values must be sorted
    index = np.arange(1,array.shape[0]+1) #index per array element
    n = array.shape[0]#number of array elements
    gini_coef =  ((np.sum((2 * index - n  - 1) * array)) / (n * np.sum(array))) #Gini coefficient
    # Alarming level from this paper: https://arxiv.org/pdf/1409.3979.pdf
    if gini_coef > .3:
        return 'Low'
    else:
        return 'High'


def dummyGroupDashboard(request,session_id,group_id):
    session = Session.objects.get(id=session_id)
    session_group = SessionGroupMap.objects.get(session=session)
    eth_group = session_group.eth_groupid
    context_data = {'group':group_id,'session':session,'eth_group':eth_group}

    return render(request,'teacher_group_analytics_dummy.html',context_data)


def dummySessionDashboard(request,session_id):
    session = Session.objects.get(id=session_id)
    context_data = {'session':session,'no_group':list(range(session.groups)),'protocol':settings.PROTOCOL}
    return render(request,'session_main_redesign_dummy.html',context_data)


def getUsers(session_id,group_id):
    """This function returns color mapping for users

    Args:
        session_id (int): Session id
        group_id (int): Group id (or group number e.g., 1, 2, 3)

    Returns:
        dict, dict: two dictionaries, one with user id to color mapping, and another for author id to color mapping
    """
    s = Session.objects.get(id=session_id)
    tmp_users = VAD.objects.filter(session=s,group = group_id).values('user').distinct()
    sp_users = [user['user'] for user in tmp_users]
    et_users = []

    session_group_object = SessionGroupMap.objects.filter(session=s).first()
    
    padid =  ep_views.get_padid(session_group_object.eth_groupid,group_id)
    pad_object = Pad.objects.filter(id=padid).first()
    params = {'padID':pad_object.eth_padid}
    print('======> params:',params)
    author_list = call('listAuthorsOfPad',params)['data']['authorIDs']
    # 
    print('Authors:',author_list)
    print('Sp users:',sp_users)
    id_to_author = {}

    for author in author_list:
        author_mapping = ep_views.get_author_user_objects(authorid=author)
        id_to_author[author_mapping[0].user.id] = author
        et_users.append(author_mapping[0].user.id)

    final_list = list(set(sp_users + et_users))

    user_to_color = {}
    author_to_color = {}

    for index,user in enumerate(final_list):
        user_to_color[user] = COLORS[index]
        try:
            author_to_color[id_to_author[user]] = COLORS[index]
        except:
            print('')
    return user_to_color,author_to_color


@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def getText(request,session_id,group_id):
    """This function returns the text produced by a group in a session.

    Args:
        request (HttpRequest): request object
        session_id (int): Session id
        group_id (int): Group id

    Returns:
        Response: text from the pad of the specified group
    
    #### Just for testing purposes ##########
    #response = requests.post('http://www.cotrack.website/en/getText/1/1')
    #return Response({'data':response.json()['data']})
    #########################################
    """
    session = Session.objects.filter(id=session_id).first()
    session_group = SessionGroupMap.objects.filter(session=session).first()
    
    # Get pad id for specified group and session
    pad_id = ep_views.get_padid(session_group.eth_groupid, group_id)
    pad = Pad.objects.get(id=pad_id)
    padid =  pad.eth_padid
    params = {'padID':padid}
    print('getHTML params:',params)
    t = call('getHTML',params)
    print("getHTML response:",t)
    content = t['data']['html']
    return Response({'data':content})


@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def getSpeakingStats(request,session_id):
    """This function returns speaking statistics and group-dynamics data for each group for a specified session.

    Args:
        request (HttpRequest): request object
        session_id (int): Session id

    Returns:
        Response: return speaking time, network data, and other details

    Url:
        http://www.cotrack.website/en/getSpeakingStats/1
    """

    global VAD_OBJECTS
    global SPEECH_OBJECTS
    if len(VAD_OBJECTS) > 0:
        objs = VAD.objects.bulk_create(VAD_OBJECTS)
        VAD_OBJECTS = []

    if len(SPEECH_OBJECTS) > 0:
        objs = Speech.objects.bulk_create(SPEECH_OBJECTS)
        SPEECH_OBJECTS = []

    s = Session.objects.get(id=session_id)
    groups = s.groups
    groups_speaking = []
    for group in range(groups):
        group = group + 1
        vads = VAD.objects.all().filter(session=session_id)

        try:
            color_mapping,t = getUsers(session_id,group)
        except:
            color_mapping = {}

        group_speaking = {}
        group_speaking['group'] = group

        tmp_users = vads.filter(group = group).values('user').distinct()
        users = [user['user'] for user in tmp_users]
        user_sequence = vads.filter(group = group).values_list('user',flat=True)
        data = []
        speaking_data = {}
        gini_data = []
        for user in users:
            user_vads = vads.filter(group = group).filter(user = user).aggregate(Sum('activity'))
            time_condition = datetime.datetime.now() - datetime.timedelta(seconds=120)
            user_vads_last_minute = vads.filter(group = group).filter(user = user,timestamp__gte = time_condition).aggregate(Sum('activity'))
            speak_data = {}
            user_obj = User.objects.get(pk = user)
            speak_data['id'] = user
            speak_data['name'] = user_obj.first_name if user_obj.first_name else user_obj.username
            speak_data['speaking'] = user_vads['activity__sum'] * .001
            if len(color_mapping) != 0:
                speak_data['color'] = color_mapping[user]
            speaking_data[user] = user_vads['activity__sum'] * .001
            data.append(speak_data)
            if not user_vads_last_minute['activity__sum'] is None:
                last_minute_activity = user_vads_last_minute['activity__sum'] * .001
                gini_data.append(last_minute_activity)

        group_speaking['data'] = data
        group_speaking['graph'] = generateElements(user_sequence,speaking_data,session_id,group)
        group_speaking['quality'] = gini(np.array(gini_data))
        groups_speaking.append(group_speaking)

    return Response({'speaking_data':groups_speaking})


def speechDF(session_id, group_id):
    """This function returns speech data for a particular group in the form of Pandas DataFrame.

    Args:
        session_id (int): Session id
        group_id (int): Group id

    Returns:
        DataFrame: A dataframe of speech data
    """
    speech_df = pd.DataFrame(columns=['timestamp','user','speech'])
    speeches = Speech.objects.all().filter(session=session_id, group=group_id)
    for speech in speeches:
        speech_df =speech_df.append({'timestamp':speech.timestamp,'user':speech.user.authormap.authorid,'speech':speech.TextField},ignore_index=True)
    speech_df.timestamp = pd.to_datetime(speech_df.timestamp)
    speech_df.timestamp = pd.to_datetime(speech_df.timestamp)
    try:
        speech_df['timestamp'] = speech_df['timestamp'].dt.tz_convert('Europe/Helsinki')
    except:
        speech_df['timestamp'] = speech_df['timestamp'].dt.tz_localize('Europe/Helsinki')
    speech_df['timestamp'] = speech_df['timestamp'].dt.tz_localize(None)
    return speech_df


def getVadDf(session_id,group_id):
    """This function returns vad data for a particular group in the form of Pandas DataFrame.

    Args:
        session_id (int): Session id
        group_id (int): Group id

    Returns:
        DataFrame: A dataframe of vad data
    """
    vad_df = pd.DataFrame(columns=['timestamp','user','speaking'])
    vads = VAD.objects.filter(session=session_id,group=group_id).order_by('timestamp')

    for v in vads:
        vad_df =vad_df.append({'timestamp':v.timestamp,'user':v.user.authormap.authorid,'speaking':(v.activity/1000)},ignore_index=True)
    vad_df.timestamp = pd.to_datetime(vad_df.timestamp)
    try:
        vad_df['timestamp'] = vad_df['timestamp'].dt.tz_convert('Europe/Helsinki')
    except:
        vad_df['timestamp'] = vad_df['timestamp'].dt.tz_localize('Europe/Helsinki')
    vad_df['timestamp'] = vad_df['timestamp'].dt.tz_localize(None)
    vad_df.drop_duplicates(inplace=True)
    return vad_df


def getLogDf(session_id,group_id):
    """This function returns logs data for a particular group in the form of Pandas DataFrame.

    Args:
        session_id (int): Session id
        group_id (int): Group id

    Returns:
        DataFrame: A dataframe of logs data
    """
    

    pad = Pad.objects.all().filter(session=session_id,group=group_id)
    log = pd.DataFrame(columns=['timestamp','author','operation','difference'])
    if len(pad) == 0:
        return log
    padid =  pad[0].eth_padid
    params = {'padID':padid}
    rev_count = call('getRevisionsCount',params)

    for r in range(rev_count['data']['revisions']):
        params = {'padID':padid,'rev':r+1}
        rev = call('getRevisionChangeset',params)
        ath = call('getRevisionAuthor',params)
        d = call('getRevisionDate',params)
        t = call('getText',params)

        try:
            cs = changeset_parse(rev['data'])
            tp = int(d['data'])
            text = t['data']['text']['text']
            char_bank = cs['bank']
            char_bank = "<br/>".join(char_bank.split("\n"))
            text = "<br/>".join(text.split("\n"))
            #print(datetime.datetime.fromtimestamp(tp/1000).strftime('%H:%M:%S %d-%m-%Y'))
            #print('   ',datetime.datetime.fromtimestamp(tp/1000).strftime('%H:%M:%S %d-%m-%Y'));
            log = log.append({'timestamp':datetime.datetime.fromtimestamp(d["data"]/1000).strftime('%H:%M:%S %d-%m-%Y'),'author':ath['data'],'operation':cs['final_op'],'difference':cs['final_diff']},ignore_index=True)
        except:
            continue
    log.timestamp = pd.to_datetime(log.timestamp,format="%H:%M:%S %d-%m-%Y")
    return log


def getProcessedFeatureFromLogVad(request, session_id, group_id):
    """This function returns processed log and vad features for the prediction task.

    Args:
        session_id (int): Session id
        group_id (int): Group id

    Returns:
        DataFrame: A dictionary of eigth features of log and vad featuers
    """
    log_df = getLogDf(session_id, group_id)
    vad_df = getVadDf(session_id, group_id)
    #speech_df = getSpeechDf(session_id, group_id)

    unique_users = set(list(log_df['author'].unique()) + list(vad_df['user'].unique()))

    sequence = vad_df['user'].to_list()

    # For computing turn-taking
    turn_df = pd.DataFrame(columns=['label','conti_frequency'])
    # This function will count the number of continuous occurence
    def count_conti_occurence(index):
        # Set count to 0
        count=0
        # Starts from the given index
        j = index
        # Loop to iterate over the users sequence
        while j<len(sequence):
            # Increase the count if the element at given index (parameter) is same as the iterated element
            if sequence[j] == sequence[index]:
                count +=1
            # If mismatch found, break the loop
            else:
                break
            # Increases j
            j +=1
        # Return number of count for sequence[index] and index of first next occurence of different element.
        return count,(j-index)
    # Set i to 0 for the Loop
    i = 0
    # Iterate for entire sequence of users
    while i < len(sequence):
        # Call count_conti_occurence() function
        count,diff = count_conti_occurence(i)
        # Add continuous frequency of current user (sequence[i]) to the dataframe
        turn_df = turn_df.append({'label':sequence[i],'conti_frequency':count},ignore_index=True)
        # Move to next different element
        i = i + diff

    added = []
    deleted = []
    speak = []
    turns = []
    #speech_text[author] = []

    for author in unique_users:
        author_df = log_df.loc[log_df['author'] == author,['operation','difference']]
        author_vad_df = vad_df.loc[vad_df['user'] == author,:]
        #author_speech_df = df_speech.loc[df_speech['user'] == author,:]
        if author_df.shape[0] != 0:
            author_add = author_df[author_df['operation'] == '>']['difference'].sum()
            author_del = author_df[author_df['operation'] == '<']['difference'].sum()
            added.append(author_add)
            deleted.append(author_del)
        else:
            added.append(0)
            deleted.append(0)

        if author_vad_df.shape[0] != 0:
            #print(author_vad_df['speaking_time(sec.)'].sum())
            speak.append(author_vad_df['speaking_time(sec.)'].sum())
        else:
            speak.append(0)

        """
        if author_speech_df.shape[0] != 0:
            speech_text[author].append(list(set(author_speech_df['speech'].values)))
        else:
            speech_text[author].append('')
        """
        turns.append(turn_df.loc[turn_df['label']==author,:].shape[0])

    processed_feature = {}
    processed_feature['user_speak_mean'] = np.mean(speak)
    processed_feature['user_speak_sd'] = np.std(speak)
    processed_feature['user_turns_mean'] = np.mean(turns)
    processed_feature['user_turns_sd'] = np.std(turns)
    processed_feature['user_add_mean'] = np.mean(added)
    processed_feature['user_add_sd'] = np.std(added)
    processed_feature['user_del_mean'] = np.mean(deleted)
    processed_feature['user_del_sd'] = np.std(deleted)
    return processed_feature


@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def getWordCloud(request,session_id,group_id):
    stopwords = set(STOPWORDS)
    session = Session.objects.get(id=session_id)
    speeches = Speech.objects.all().filter(session = session, group = group_id).values_list('TextField',flat=True)
    speeches = " ".join(speech for speech in speeches)
    print(speeches)
    if len(speeches) == 0:
        data = {'data':'empty'};
    else:
        wc = WordCloud(background_color = 'white', max_words=2000, stopwords = stopwords)
        """
        new code
        """
        fig2, ax = plt.subplots(1,1,figsize=(6,8))
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])
        cloud = wc.generate(speeches)
        print('Word cloud generated')
        ax.imshow(wc,interpolation ='bilinear')

        """
        fig = plt.figure(figsize=(6,8))
        cloud = wc.generate(speeches)
        print('Word cloud generated')
        plt.imshow(wc,interpolation ='bilinear')
        plt.axis('off')
        """
        image = io.BytesIO()
        fig2.savefig(image,format="png")
        image.seek(0)
        string = base64.b64encode(image.read())
        #image_64 =  urllib.parse.quote(string)
    data = {'data':str(string.decode())}
    return Response(data)


def get_pad_session(pad):
    """This function returns session object associated with given pad object.
       Each pad object is linked with a PadGroup object. This pad group object contains a etherpad group id.
       The same id is also used in SessionGroupMap to link PadGroup with Session.
    Args:
        pad (Pad): Pad object

    Returns:
        Session: Session object associated with given Pad
    """
    # Each etherpad pad id consists of group id and group name, seperated by $ sign
    pad_eth_id = pad.eth_padid
    eth_group_id = pad_eth_id.split('$')[0]

    # Session group map object
    session_group_map = SessionGroupMap.objects.filter(eth_groupid = eth_group_id).first()
    # Accessing session object
    session = session_group_map.session

    return session


@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
# change the signature back to  def getGroupPadStats(request,padid)
def getGroupPadStats(request,group_padid):
    """This function returns group-wise statistics for writing.
       @url: /getStats/<pad_id>
    Args:
        request (HttpRequest): request object
        padid (str): Etherpad padid
    Returns:
        Response: writing statistics
    """

    
    # Fetch etherpad group id from padid
    eth_padgroup = group_padid.split('$')[0]

    # Group number
    group_num = int(group_padid.split('_')[-1])

    # Get associated SessionGroupMapping object
    session_group_object = SessionGroupMap.objects.filter(eth_groupid = eth_padgroup)[0]

    # Associated session
    session = session_group_object.session

    # Fetch pad id 
    pad_id = ep_views.get_padid(eth_padgroup, group_num)
    
    print('==============   In getStats')
    # Get Pad object
    pad = Pad.objects.filter(id = pad_id).first()
    group = pad.group_number

    # Return user list and color mapping (each user is linked with a unique color)
    t,color_mapping = getUsers(session.id,group)
    #print(f't:{t} color_mapping:{color_mapping}')
    params = {'padID':group_padid}
    print('   Params:',params)
    
    rev_count = call('getRevisionsCount',params)
    print('  getRevisionCount:',rev_count)
    # get user wise Info
    author_list = call('listAuthorsOfPad',params)['data']['authorIDs']
    print(' Authors:',author_list)
    addition = {}
    deletion = {}
    author_names = {}
    for author in author_list:
        print('------>    Author',author)
        addition[author] = 0
        deletion[author] = 0
        print('------>    Calling:',call('getAuthorName',{'authorID':author}))
        author_names[author] = call('getAuthorName',{'authorID':author})['data']
    for r in range(rev_count['data']['revisions']):
        params = {'padID':pad.eth_padid,'rev':r+1}
        rev = call('getRevisionChangeset',params)
        print(' getReivisionChangeSet:',rev)
        ath = call('getRevisionAuthor',params)
        print(' getRevisionAuthor:',ath)
        cs = ep_views.changeset_parse(rev['data'])
        if (cs['final_op'] == '>'):
            addition[ath['data']] += cs['final_diff']
        if (cs['final_op'] == '<'):
            deletion[ath['data']] += cs['final_diff']

    call_response = {}
    author_count = len(author_names.keys())
    for i,v in enumerate(author_names.keys()):
        call_response[i] = {
            'authorid': v,
            'name':author_names[v],
            'addition':addition[v],
            'deletion':deletion[v],
            'color':color_mapping[v]
        }
    return Response(call_response)

###################### Invetervention strategies are taken from CIM (Kasepalu et al., 2022)
CIM = {'arg':{},'smu':{},'co':{}}

CIM['arg']['high'] = "Praise the students"
CIM['arg']['low'] = "Make sure there is someone in the group with the role of orienting (defining the progress in terms of goals, raising questions about the direction of the discussion)"

CIM['smu']['high'] = "Praise high-functioning group "
CIM['smu']['low'] = "To promote interdependence, specify common rewards for the group, such as a group mark"

CIM['co']['high'] = "Praise the students"
CIM['co']['low'] = "Go and talk to the group about the issue, guide them to solve their own problem"

sample_data = {"user_speak_mean": 4.3533333333333335,
 "user_speak_sd": 2.2290810131579057,
 "user_turns_mean": 2.0,
 "user_turns_sd": 0.7071067811865477,
 "user_add_mean": 15.833333333333332,
 "user_add_sd": 22.391714737574006,
 "user_del_mean": 0.16666666666666666,
 "user_del_sd": 0.23570226039551584}



@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
# predict level of collaboration
def predictCollaboration(request):
    cq_model = ApiConfig.cq_model
    arg_model = ApiConfig.arg_model
    col_names = ['user_speak_mean', 'user_speak_sd', 'user_turns_mean', 'user_turns_sd',
                'user_add_mean', 'user_add_sd', 'user_del_mean', 'user_del_sd']
    #req_data = request.data
    req_data = sample_data
    df = pd.DataFrame(req_data,index=[0])
    y_proba_cq = cq_model.predict_proba(df)
    pred_cq = cq_model.predict(df)
    y_proba_arg = arg_model.predict_proba(df)
    pred_arg = arg_model.predict(df)

    print('Predicted:',pred_arg[0],' Type:',type(pred_arg[0]))

    if int(pred_arg[0]) == 1:
        arg_intervention = CIM['arg']['high']
    else:
        arg_intervention = CIM['arg']['low']

    response_dict = {'cq_probability':y_proba_cq,
                     'cq_prediction':pred_cq,
                     'arg_probability':y_proba_arg,
                     'arg_prediction':pred_arg,
                     'arg_strategy':arg_intervention}
    
    return Response(response_dict, status=200)
#### REST API END   ###############
