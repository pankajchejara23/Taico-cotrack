from django.db import models
from django.contrib import admin
from ckeditor_uploader.fields import RichTextUploadingField

# Using custom user model
from django.contrib.auth import get_user_model
User = get_user_model()

import os

class Session(models.Model):
    """Model to store information regarding the learning session
    """
    creator = models.ForeignKey(User, on_delete=models.CASCADE)   #owner of the session
    name = models.CharField(max_length=100)                     #session title
    groups = models.IntegerField()                              #number of groups
    learning_problem = RichTextUploadingField()                 #learning problem
    language = models.CharField(max_length=2)                   #language (to use for speech to text translation)
    created_at = models.DateTimeField(auto_now_add=True)        #created at date and time
    duration = models.DurationField()                           #duration of the activity
    access_allowed = models.BooleanField(default=True)          #whether the access is open to the students or not
    status = models.BooleanField(default=False)                 #status of session, used for archiving the session
    assessment_score = models.IntegerField()                    #to store the teacher's assessment of group's work
    useEtherpad = models.BooleanField(default=False)            #whether to use etherpad or not
    useAVchat = models.BooleanField(default=False)              #whether to use audio video chat or not @todo: for future version
    record_audio = models.BooleanField(default=False)           #whether to record audio during activity
    record_audio_video = models.BooleanField(default=False)     #whether to record audio and video both during the activity
    data_recording_session = models.BooleanField(default=False) #whether the session is just for data collection purposes
    random_group = models.BooleanField(default=False)           #whether the session uses random grouping for collaborative learning
    consent_content = RichTextUploadingField()                  #content of a consent form

    # Tracking configuration variable
    conf_vad = models.BooleanField(default=False)               #whether to perform voice activity detection
    conf_speech = models.BooleanField(default=False)            #whether to perform speech to text conversion
    conf_consent = models.BooleanField(default=False)           #whether to show consent form
    

# Model for storing requests for getting teacher's role
class RoleRequest(models.Model):
    """This model stores request made by users for gaining teacher's role.
    """
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    school =  models.TextField(blank=True)
    class_size = models.IntegerField()
    subject = models.TextField(blank=True)
    decision =  models.BooleanField(default=False)
    pending =  models.BooleanField(default=True)


# Model for storing Etherpad session id
class SessionGroupMap(models.Model):
    """Model to mapping between Etherpad pads and learning session
    """
    session = models.ForeignKey(Session,on_delete=models.CASCADE) 
    eth_groupid = models.CharField(max_length=20)                 


def user_directory_path(instance, filename):
    """Function to create filename to store audio/video file

    Args:
        instance (Session): Session object
        filename (str): name of the file

    Returns:
        filename: complete filename containing session info
    """
    # file will be uploaded to MEDIA_ROOT/session_<id>/group_<id>/user_<id>/<filename>
    return os.path.join(
      "session_%d" % instance.session.id,
      "group_%d" % instance.group, 
      "user_%s" % instance.user.id, 
      filename)


class Audiofl(models.Model):
    """Model to store audio/video file on the server

    """
    session = models.ForeignKey(Session,on_delete=models.CASCADE)   
    group = models.IntegerField(blank=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    sequence = models.IntegerField(blank=True)
    description = models.TextField(blank=True)
    fl = models.FileField(upload_to=user_directory_path, blank=True)


class VAD(models.Model):
    """Model to store voice activity detection data

    """
    session = models.ForeignKey(Session,on_delete=models.CASCADE)
    group = models.IntegerField(blank=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    timestamp = models.DateTimeField(blank=True)
    activity = models.BigIntegerField(blank=True)


class Speech(models.Model):
    """Model to store Google Speech-to-Text.  Only available for chrome browser

    """
    session = models.ForeignKey(Session,on_delete=models.CASCADE)
    group = models.IntegerField(blank=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    timestamp = models.DateTimeField(blank=True)
    TextField = models.TextField(blank=True)


class activityLog(models.Model):
    """Model to store activity logs 

    """
    session = models.ForeignKey(Session,on_delete=models.CASCADE)
    actor = models.ForeignKey(User,on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)
    verb = models.TextField(blank=True)
    object = models.TextField(blank=True)


class Consent(models.Model):
    """Model to store users' consent responses

    """
    session = models.ForeignKey(Session,on_delete=models.CASCADE)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    permission = models.BooleanField(default=False)
    given_at = models.DateTimeField(auto_now_add=True)


class observationData(models.Model):
    """Model to store observational data

    """
    session = models.ForeignKey(Session,on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)
    observation = models.TextField(blank=True)


class GroupPin(models.Model):
    """Model to store a secure pin for accessing a group's pad

    """
    session = models.ForeignKey(Session,on_delete=models.CASCADE)
    pin = models.CharField(max_length=6)
    group = models.IntegerField(blank=True)


class DummyAccounts(models.Model):
    """Model to store information about user accounts created by a teachers
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    prefix = models.TextField()
    password_str = models.TextField()
    num_accounts = models.IntegerField()
    status = models.BooleanField(default=False)



admin.site.register(Audiofl)
admin.site.register(Session)
admin.site.register(VAD)
admin.site.register(Speech)
admin.site.register(GroupPin)
admin.site.register(Consent)
admin.site.register(RoleRequest)
admin.site.register(SessionGroupMap)
admin.site.register(DummyAccounts)