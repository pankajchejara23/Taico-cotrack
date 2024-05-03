from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from .models import Session, GroupPin, SessionGroupMap, VAD, Speech, Audiofl, RoleRequest
from django.views import View
from django.contrib import messages
from django.core.files.base import File
from django.views.generic import ListView, DetailView, UpdateView, CreateView
from .forms import SessionCreateForm, SessionEnterForm, AudioflForm, VADForm, SpeechForm, SessionUpdateForm, RoleRequestForm
from etherpad_app import views as ep_views
from datetime import date, timedelta
import uuid
from django.db import transaction
import jwt
import datetime
from django.conf import settings
from django.utils.translation import gettext as _
# Create your views here.

def generate_pin(s, g):
    """This function generates a unique pin code

    Args:
        s (Session): Session object
        g (int): Group number

    """
    while True:
        u_pin = uuid.uuid4().hex[:6].upper()
        objs = GroupPin.objects.filter(pin = u_pin)
        if objs.count() == 0:
            break
    sg = GroupPin.objects.create(session=s,pin=u_pin,group=g)
    return


class SessionUpdateView(UpdateView):
    """This view allows editing of Session objects.

    """
    model = Session
    template_name = 'update_session.html'
    success_url = '/session/list'
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
            
        return HttpResponseRedirect(self.get_success_url())


class SessionListView(ListView):
    """View for listing out learning sessions

    """
    model = Session
    template_name = 'list_session.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(status=True)
        return queryset


class SessionArchiveListView(ListView):
    """View for listing out archived learning sessions

    """
    model=Session
    template_name = 'list_session.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(status=False)
        return queryset


class SessionArchiveView(View):
    """This view handles archiving of sessions.

    """
    def get(self, request, *args, **kwargs):
        id = self.kwargs['pk']
        session_object = Session.objects.get(id=id)
        # changing  status to False
        session_object.status=False
        session_object.save()
        messages.success(self.request, _('Session is archived.'))
        return redirect('session_list')


class SessionDuplicateView(View):
    """This view handles duplicate and archive actions.

    """
    def get(self, request, *args, **kwargs):
        id = self.kwargs['pk']

        session_object = Session.objects.get(id=id)

        # setting primary key to None cause creation of a new object at save
        session_object.id = None
        session_object.save()

        groups = session_object.groups

        # generate a secure access pin for each pad in the group
        for group in range(groups):
            group += 1
            generate_pin(self.object, g)

            
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
                messages.success(self.request, _('Session is created successfully !'))
            else:
                messages.error(self.request, _('Error occurred while creating the session !'))
            return redirect('session_list')
        else:
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
                
                print('Session Etherpad:',sessionID)
                # storing sessionID in session object, so that user did not need to enter the pin again
                self.request.session['ethsid'] = sessionID

                # preparing context params 
                audio_form = AudioflForm()  # this form used to store audio data on server

                # pad name
                pad_name = f'session_{session_object.id}_group_{group_number-1}'

                context_data = {'group':group_number,
                                'session':session_object,
                                'sessionj':session_object,
                                'form':audio_form,
                                'pad_name':pad_name,
                                'sessionid':sessionID,
                                'etherpad_url':settings.ETHERPAD_URL,
                                'protocol':settings.PROTOCOL}

                return render(request, self.pad_template_name, context_data)
        else:
            messages.error(request, 'Form is invalid.')
            form = self.form_class()
            # redisplaying the enter form with error message
            return render(request, self.template_name, {'form':form})
        

class UploadVADView(View):
    """View for handling audio data processing and storing on server

    """
    form_class = VADForm
    def post(self, request, *args, **kwargs):
        """This function stores voice activity detection data on server.

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


class UploadSpeechView(View):
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
        

class UploadAudioView(View):
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
        

class RoleRequestView(View):
    model = RoleRequest
    form_class = RoleRequestForm
    template_name = 'role_request.html'
    success_url = '/session/list'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        
        # save only if the request does not exists alredy
        roles = RoleRequest.objects.filter(user=self.request.user)
        if roles.count() !=0:
            messages.error(request, 'You already made a request.')
            return HttpResponseRedirect(self.success_url)
        else:
            return render(request, self.template_name, {'form':form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            role = form.save(commit=False)
            role.user = self.request.user
            role.decision = False
            role.pending = True
            role.save()
            messages.success(request, 'Your request have been registered.')
            return HttpResponseRedirect(self.success_url)
        else:
            return render(request, self.template_name, {'form':form})


class RoleRequestListView(ListView):
    model = RoleRequest
    template_name = 'role_list.html'
