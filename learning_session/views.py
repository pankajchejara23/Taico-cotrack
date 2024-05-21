from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from .models import Session, GroupPin, SessionGroupMap, VAD, Speech, Audiofl, RoleRequest, Consent
from django.views import View
from django.contrib import messages
from django.core.files.base import File
from django.views.generic import ListView, DetailView, UpdateView, CreateView
from .forms import SessionCreateForm, SessionEnterForm, AudioflForm, VADForm, SpeechForm, SessionUpdateForm 
from .forms import ConsentForm, RoleRequestForm, GrantTeacherRoleForm, UserCreateForm
from etherpad_app import views as ep_views
from datetime import date, timedelta
import uuid
from django.db import transaction
from django.urls import reverse
import jwt
import csv
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
            
        return HttpResponseRedirect(reverse(self.get_success_url()))


class SessionListView(ListView):
    """View for listing out learning sessions

    """
    model = Session
    template_name = 'list_session.html'

    def get_queryset(self):
        """This function update the queryset which returns the objects for listview.

        Returns:
            queryset: queryset containing objects
        """
        queryset = super().get_queryset()
        queryset = queryset.filter(status=True).filter(creator = self.request.user)
        return queryset


class GrantTeacherRoleView(ListView):
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


class SessionDuplicateView(View):
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

        Args:
            request (HttpRequest): request parameter
        """
        context = super().get_context_data(**kwargs)

        # adding number of groups
        context["no_groups"] = list(range(self.object.groups))
        return context


class SessionCreateView(View):
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


class SessionLeaveView(View):
    def get(self, request, *args, **kwargs):
        if 'payload' in self.request.session.keys():
            del self.request.session['payload']
        return redirect('session_enter')
    

class StudentPadView(View):
    """This view shows etherpad to student.

    """
    template_name = 'student_pad.html'
    def get(self, request, *args, **kwargs):
        """This function forward the user to the etherpad view

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
        pad_name = f'session_{session_object.id}_group_{group_number-1}'

        context_data = {'group':group_number,
                                        'session':session_object,
                                        'sessionj':session_object,
                                        'form':audio_form,
                                        'pad_name':pad_name,
                                        'sessionid':sessionID,
                                        'etherpad_url':settings.ETHERPAD_URL,
                                        'protocol':settings.PROTOCOL}

        return render(request, self.template_name, context_data)


class ConsentView(View):
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


class RoleRequestListView(ListView):
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

            # using is_active as a flag to determine teacher's role
            user_object.is_active = staff
            messages.success(request, f'User <strong>{user.email}</strong> has been assigned teacher role.')
        else:
            return render(request, self.template_name, {'form':form})
        return HttpResponseRedirect(self.success_url)
    

class UserCreateView(View):
    """View for creating new user accounts.

    """
    form_class = UserCreateForm  
    template_name = 'create_user.html'
    success_url = '/session/list/admin'

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
            user = form.cleaned_data.get('name')
            email = form.cleaned_data.get('email')
            pwd = form.cleaned_data.get('password')
            staff = form.cleaned_data.get('staff')

            # create a new user
            user_object = User.objects.create_user(username = user,email = email,password = pwd)

            # set is_staff status
            user_object.is_active = staff
            user_object.save()
            messages.success(request, f'User acocunt for <strong>{user_object.email}</strong> has been created.')
        else:
            return render(request, self.template_name, {'form':form})
        return HttpResponseRedirect(self.success_url)


class RoleRequestAction(View):
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
class DownloadVadView(View): 
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
        

class DownloadSpeechView(View): 
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

class DownloadLogsView(View): 
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

