from django.db import models
from django.conf import settings
from django.utils.translation import gettext as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib import admin
import requests

from django.contrib.auth import get_user_model
User = get_user_model()

def call(function, arguments=None, request=None):
    """Functoin to call etherpad api function

    Args:
        function (str): name of etherpad api function to call.https://etherpad.org/doc/v1.8.4/#index_http_api 
        arguments (dict): arguments for the called function
        request (): request params
    """
    try:
        url =  settings.ETHERPAD_PROTOCOL + "://" + settings.ETHERPAD_URL + '/api/1.2.12/' +function+'?apikey='+settings.ETHERPAD_KEY   
        response = requests.post(url,arguments)
        # response object
        x = response.json()
        return x
    except:
        return None


class AuthorMap(models.Model):
    """
    model to store etherpad author id for each user
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # field to store etherpad user id
    authorid = models.CharField(max_length=20)


# Function to execute whenever a new user is created
@receiver(post_save, sender=User)
def createAuthor(sender,instance,created,**kwargs):
    """Function to create a author id for every new user

    Args:
        sender: from which to receive signals (read more here: https://docs.djangoproject.com/en/5.0/topics/signals/)
        instance: instance of sender
        created: bool type flag representing the status of the new object
    """
    if created:
        objs = AuthorMap.objects.all().filter(user=instance)
        if objs.count()>0:
            authorid = objs[0].authorid
        else:
            print('making etherpad api request')
            res = call('createAuthorIfNotExistsFor',{'authorMapper':instance.id,'name':instance.username})
            authorid = res['data']['authorID']
            AuthorMap.objects.create(user=instance,authorid=authorid)


class PadGroup(models.Model):
    """
    This model stores etherpad group information. 
    Each pad in etherpad belongs to a group. 
    """

    # group name
    group = models.CharField(max_length=50)

    # etherpad group id
    groupID = models.CharField(max_length=256, blank=True)

    class Meta:
        verbose_name = _('Group')


class Pad(models.Model):
    """This model stores pad id and its text 
    """
    eth_padid = models.CharField(max_length=50)
    eth_group = models.ForeignKey(PadGroup, on_delete=models.CASCADE)
    group_number = models.IntegerField(blank=True)


admin.site.register(Pad)
admin.site.register(PadGroup)
admin.site.register(AuthorMap)