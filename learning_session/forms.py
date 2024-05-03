from django import forms
from django_toggle_switch_widget.widgets import DjangoToggleSwitchWidget
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django.utils.translation import gettext as _
from .models import Session, VAD, Speech, Audiofl, RoleRequest



default_consent_form_content = """<h3>Dear Participant </h3>
      With your permission, we would like to record audio and video during collaborative activity session so that we can analyze it in detail later on.
      The recording will be saved in  files- in WEBM format on server.
      <br/><br/>
      It should be noticed that:<br/>
      All kinds of data will be stored securely on Google drive (under a password-protected TLU account), and backed up in a password-protected server at TLU, accessible only to the research team.
      This data will be stored not longer than 5 years. <br/>
      The data may be re-used by members of the <a href='http://ceiter.tlu.ee/' target='_blank'>CEITER research team</a>, or in later projects by students of the School of Educational Technologies and School of Educational Sciences.
      <br/><br/>No personal information about you will be shared or made public, and any information you provide will be anonymized before publication. <br/>
      At any point, you can request to withdraw your data from the study, or from this storage. <br/>
      <br/><br/>
      <b>GDPR art. 13</b> requirements: <br/>
      Data Protection Officer (at Tallinn University): andmekaitsespetsialist@tlu.ee<br/>
      <br/>
      <b>Please read carefully the following points and ask for clarifications in case of doubts:</b><br/><br/>

      <ul>
        <li>  The collaboration activity is designed to gather information for research purposes and further development of data collection and visualization technologies to understand collaborative learning activities across spaces.</li>
        <li>  I may withdraw and discontinue my participation at any time.</li>
        <li> My audio and video will be recorded.</li>
        <li> The researcher will not identify me by name in any report using information obtained from this dataset, and my confidentiality as a participant in this study will remain secure. </li>
        <li> Anonymized extracts from the dataset may be used in research publications.  </li>
        <li> I have the right to ask access, rectification, or erasure of my data (as long as it is possible to pinpoint my identity from that data)</li>
      </ul>"""


class AudioflForm(forms.ModelForm):
    """Form to save audio/video file on server

    Args:
        forms (_type_): _description_
    """
    strDate = forms.CharField(max_length=50,required=False,
                              widget=forms.HiddenInput())
    class Meta:
        model = Audiofl
        fields = ('description', 'fl', 
                  'session','user',
                  'group','sequence')
        widgets = {'description':forms.HiddenInput(),
                   'fl': forms.HiddenInput(),
                   'session':forms.HiddenInput(),
                   'user':forms.HiddenInput(),
                   'group':forms.HiddenInput(),
                   'sequence':forms.HiddenInput()
                   }


class VADForm(forms.ModelForm):
    """Form to store voice activity detection data on server

    """
    strDate = forms.CharField(max_length=20,
                              required=False,
                              widget=forms.HiddenInput())
    milli = forms.IntegerField(max_value=1000,
                               required=False,
                               widget=forms.HiddenInput())
    class Meta:
        model = VAD
        fields = ( 'session','user','group','activity')
        widgets = {'strDate':forms.HiddenInput(),
                   'milli':forms.HiddenInput(),
                   'session':forms.HiddenInput(),
                   'user':forms.HiddenInput(),
                   'group':forms.HiddenInput(),
                   'activity':forms.HiddenInput()}


class SpeechForm(forms.ModelForm):
    """Form to save speech-to-text data on server

    """
    strDate = forms.CharField(max_length=20,
                              required=False,
                              widget=forms.HiddenInput())
    class Meta:
        model = Speech
        fields = ( 'session','user','group','TextField')
        widgets = {'strDate':forms.HiddenInput(),
                   'milli':forms.HiddenInput(),
                   'session':forms.HiddenInput(),
                   'user':forms.HiddenInput(),
                   'group':forms.HiddenInput(),
                   'TextField':forms.HiddenInput()}

class SessionUpdateForm(forms.ModelForm):
    LANG_CHOICES = [('En',_('English')),('Et',_('Estonian'))]
    STATUS_CHOICES=[(True,_('Enable')),(False,_('Disable'))]

    # form field to get title info
    name = forms.CharField(label=_('Learning session title'),
                           widget=forms.TextInput(
                               attrs={
                                   'class':'form-control'
                                   }))
    # get number of groups
    groups = forms.IntegerField(label=_('Number of groups'),
                                widget=forms.NumberInput(
                                    attrs={
                                        'class':'form-control'
                                        }))
    # instruction language: this is used for deciding the language when using Google Speech-to-Text
    language=forms.CharField(label=_('Language'),
                             widget=forms.Select(
                                 choices=LANG_CHOICES,
                                 attrs={
                                     'class':'form-control'
                                     }))
    # duration of the learning session (in days)
    duration_days = forms.IntegerField(label=_('Days'),
                                       widget=forms.NumberInput(
                                           attrs={
                                               'class':'form-control',
                                               'placeholder':_('Days')
                                               }))
    # duration of the learning session (in hours)
    duration_hours = forms.IntegerField(label=_('Hours'),
                                        widget=forms.NumberInput(
                                            attrs={
                                                'class':'form-control',
                                                'placeholder':_('Hours')
                                                }))
    # duration of the learning session (in minutes)
    duration_minutes = forms.IntegerField(label=_('Minutes'),
                                          widget=forms.NumberInput(
                                              attrs={
                                                  'class':'form-control',
                                                  'placeholder':_('Minutes')
                                                  }))
    

    # field to differentiate between create and edit operations
    new = forms.IntegerField(widget=forms.HiddenInput(),
                             required=False,initial=-1) # store -1 if session is new otherwise contains session id

    ### LEARNING SPACE CONFIGURATION

    # learning task for students
    learning_problem = forms.CharField(required=False,
                                       label=_('Learning activity'),
                                       widget=CKEditorUploadingWidget(
                                           attrs={
                                               'class':'form-control'
                                               })
                                        )
    # whether to use Etherpad for the learning task
    useEtherpad = forms.BooleanField(required=False,
                                     widget=DjangoToggleSwitchWidget(
                                         klass="django-toggle-switch-dark-primary"
                                         )
                                     )
    # whether to use audio/video chat for learning task
    useAVchat = forms.BooleanField(required=False,
                                   widget=DjangoToggleSwitchWidget(
                                       klass="django-toggle-switch-dark-primary"
                                       )
                                  )
    # whether to automatically group students
    random_group = forms.BooleanField(required=False,
                                      widget=DjangoToggleSwitchWidget(
                                          klass="django-toggle-switch-dark-primary"
                                          )
                                      )
    
    #### RECORDING CONFIGURATION 

    # whether to record audio data
    record_audio = forms.BooleanField(required=False, label=_('Audio recording'),
                                      widget=DjangoToggleSwitchWidget(
                                          klass="django-toggle-switch-dark-primary"
                                          )
                                      )
    # whether to record video data
    record_audio_video = forms.BooleanField(required=False, label=_('Audio/Video recording'),
                                            widget=DjangoToggleSwitchWidget(
                                                klass="django-toggle-switch-dark-primary"
                                                )
                                            )
    # whether to perform voice activity detection
    conf_vad = forms.BooleanField(required=False,label=_('Capture speaking activity'),
                                  widget=DjangoToggleSwitchWidget(
                                      klass="django-toggle-switch-dark-primary"
                                      )
                                  )
    # whether to perform speech-to-text
    conf_speech = forms.BooleanField(required=False, label=_('Capture speech-to-text'),
                                     widget=DjangoToggleSwitchWidget(
                                         klass="django-toggle-switch-dark-primary"
                                         )
                                     )
    # whether to add consent form
    conf_consent = forms.BooleanField(required=False, label=_('Add consent form'),
                                      widget=DjangoToggleSwitchWidget(
                                          klass="django-toggle-switch-dark-primary"
                                          )
                                     )
    # content of consent
    consent_content = forms.CharField(label=_('Consent form'),
                                      widget=CKEditorUploadingWidget(
                                          attrs={'class':'form-control'}
                                      ),
                                      required=False,
                                      initial=default_consent_form_content)
    # whether to activate the learning session now
    allow_access = forms.ChoiceField(required=False,
                                    choices=STATUS_CHOICES, 
                                    widget=forms.RadioSelect(
                                         attrs={'class': "custom-radio-list"}
                                    ),
                                    initial=True)
    class Meta:
        model = Session
        exclude = ['creator','created_at','status','access_allowed','duration','assessment_score']


class SessionCreateForm(forms.Form):
    """Form to create Session. 

    """
    LANG_CHOICES = [('En',_('English')),('Et',_('Estonian'))]
    STATUS_CHOICES=[(True,_('Enable')),(False,_('Disable'))]

    # form field to get title info
    name = forms.CharField(label=_('Learning session title'),
                           widget=forms.TextInput(
                               attrs={
                                   'class':'form-control'
                                   }))
    # get number of groups
    groups = forms.IntegerField(label=_('Number of groups'),
                                widget=forms.NumberInput(
                                    attrs={
                                        'class':'form-control'
                                        }))
    # instruction language: this is used for deciding the language when using Google Speech-to-Text
    language=forms.CharField(label=_('Language'),
                             widget=forms.Select(
                                 choices=LANG_CHOICES,
                                 attrs={
                                     'class':'form-control'
                                     }))
    # duration of the learning session (in days)
    duration_days = forms.IntegerField(label=_('Days'),
                                       widget=forms.NumberInput(
                                           attrs={
                                               'class':'form-control',
                                               'placeholder':_('Days')
                                               }))
    # duration of the learning session (in hours)
    duration_hours = forms.IntegerField(label=_('Hours'),
                                        widget=forms.NumberInput(
                                            attrs={
                                                'class':'form-control',
                                                'placeholder':_('Hours')
                                                }))
    # duration of the learning session (in minutes)
    duration_minutes = forms.IntegerField(label=_('Minutes'),
                                          widget=forms.NumberInput(
                                              attrs={
                                                  'class':'form-control',
                                                  'placeholder':_('Minutes')
                                                  }))
    # field to differentiate between create and edit operations
    new = forms.IntegerField(widget=forms.HiddenInput(),
                             required=False,initial=-1) # store -1 if session is new otherwise contains session id

    ### LEARNING SPACE CONFIGURATION

    # learning task for students
    learning_problem = forms.CharField(required=False,
                                       label=_('Learning activity'),
                                       widget=CKEditorUploadingWidget(
                                           attrs={
                                               'class':'form-control'
                                               })
                                        )
    # whether to use Etherpad for the learning task
    useEtherpad = forms.BooleanField(required=False,
                                     widget=DjangoToggleSwitchWidget(
                                         klass="django-toggle-switch-dark-primary"
                                         )
                                     )
    # whether to use audio/video chat for learning task
    useAVchat = forms.BooleanField(required=False,
                                   widget=DjangoToggleSwitchWidget(
                                       klass="django-toggle-switch-dark-primary"
                                       )
                                  )
    # whether to automatically group students
    random_group = forms.BooleanField(required=False,
                                      widget=DjangoToggleSwitchWidget(
                                          klass="django-toggle-switch-dark-primary"
                                          )
                                      )
    
    #### RECORDING CONFIGURATION 

    # whether to record audio data
    record_audio = forms.BooleanField(required=False, label=_('Audio recording'),
                                      widget=DjangoToggleSwitchWidget(
                                          klass="django-toggle-switch-dark-primary"
                                          )
                                      )
    # whether to record video data
    record_audio_video = forms.BooleanField(required=False, label=_('Audio/Video recording'),
                                            widget=DjangoToggleSwitchWidget(
                                                klass="django-toggle-switch-dark-primary"
                                                )
                                            )
    # whether to perform voice activity detection
    conf_vad = forms.BooleanField(required=False,label=_('Capture speaking activity'),
                                  widget=DjangoToggleSwitchWidget(
                                      klass="django-toggle-switch-dark-primary"
                                      )
                                  )
    # whether to perform speech-to-text
    conf_speech = forms.BooleanField(required=False, label=_('Capture speech-to-text'),
                                     widget=DjangoToggleSwitchWidget(
                                         klass="django-toggle-switch-dark-primary"
                                         )
                                     )
    # whether to add consent form
    conf_consent = forms.BooleanField(required=False, label=_('Add consent form'),
                                      widget=DjangoToggleSwitchWidget(
                                          klass="django-toggle-switch-dark-primary"
                                          )
                                     )
    # content of consent
    consent_content = forms.CharField(label=_('Consent form'),
                                      widget=CKEditorUploadingWidget(
                                          attrs={'class':'form-control'}
                                      ),
                                      required=False,
                                      initial=default_consent_form_content)
    # whether to activate the learning session now
    allow_access = forms.ChoiceField(required=False,
                                    choices=STATUS_CHOICES, 
                                    widget=forms.RadioSelect(
                                         attrs={'class': "custom-radio-list"}
                                    ),
                                    initial=True)


class ConsentForm(forms.Form):
    """This form stores user's input on the consent form. 
    @todo: extends the form for opt-out case.
    """
    permission = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={'class': "form-check-input"}
        ),
        initial=False,required=True)
    

class SessionEnterForm(forms.Form):
    """This form takes a pin as input and allows access to learning space.

    """

    # form field to get session pin
    pin = forms.CharField(label=_('Enter access pin'),
                           widget=forms.TextInput(
                               attrs={
                                   'class':'form-control'
                                   }))


class RoleRequestForm(forms.ModelForm):

    class Meta:
        model = RoleRequest
        fields = ['school', 'class_size', 'subject']
        widgets= {
            'school':forms.TextInput(attrs = {'class':'form-control'}),
            'class_size':forms.NumberInput(attrs = {'class':'form-control'}),
            'subject':forms.TextInput(attrs = {'class':'form-control'}),

        }