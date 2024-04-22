from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView
from django.db import transaction
from .forms import PadCreateForm
from .models import PadGroup, Pad, AuthorMap
from .models import call
import datetime
# Create your views here.
def create_etherpad_user(mapping):
    """This function creates a new user in Etherpad if it doesn't exists.

    Args:
        mapping (dict): this mapping used to create a new user in Etherpad correspoding
                         to a specified user in CoTrack. Each user in CoTrack has a corresponding user
                         in Etherpad.
                         The mapping contains two information: 'authorMapper' which is unique is of the user, and 
                         'name' that is name of the user.
    """
    res = call('createAuthorIfNotExistsFor', mapping)
    if 'authorID' in res['data']:
        return res['data']['authorID']
    else:
        return None


def create_session(mapping):
    """This function generate a link to a pad in the Etherpad for specified groupid

    Args:
        mapping (dict): This mapping contains 'authorID' about the user for whom the pad
                        link is generated, 'groupID' that is Etherpad group id associated with the pad,
                        and 'validUntil' which contains timestamp until when the pad is accessible.
    """
    result = call('createSession', mapping)
    if 'sessionID' in result['data']:
        return result['data']['sessionID']
    else:
        return None

def create_pads(pad_number, group_name):
    """This function creates n pads in Etherpad with a Etherpad group with the specified name

    Args:
        pad_number (int): Number of pads to create in Etherpad
        group_name (str): Name of Etherpad group

    Returns:
        str: Etherpad group id
    """
    result = {'status':'failure'}
    # call to create etherpad group
    group_create_response = call('createGroup')
    print(group_create_response)
    eth_group_id = None
            
    # check for successful execution of the call
    if (group_create_response["code"] == 0):
        eth_group_id = group_create_response["data"]["groupID"]
        pad_group_object = PadGroup.objects.create(group=group_name,
                                                    groupID=eth_group_id)

        # create n pads
        for num in range(int(pad_number)):
            #prepare pad name
            pad_name = f'{group_name}_group_{num}'

            # call to create pad
            pad_create_response = call('createGroupPad',
                                        {
                                            'groupID':eth_group_id,
                                            'padName':pad_name
                                        })
            print(pad_create_response)
            if pad_create_response["code"]==0:
                pad_object = Pad.objects.create(eth_group=pad_group_object,
                                                    eth_padid=pad_name)
                print('Pad created')
        result['status'] = 'success'
        result['group_id'] = eth_group_id
    return result
        

class PadCreateFormView(View):
    form_class = PadCreateForm
    template_name ='create_pad.html'
    success_template = 'success.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form':form})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            pad_number = form.cleaned_data.get('pad_number')
            group_name = form.cleaned_data.get('group_name')
            result = create_pads(pad_number, group_name)
            if result['status'] == 'failure':
                #@todo: failure message showing
                pass
        return render(request, self.success_template)
    

class PadListView(ListView):
    model = Pad
    template_name = 'pad_list.html'


class PadDetailView(DetailView):
    template_name = 'pad_detail.html'
    model = Pad
    """
    NOTE: Make sure your etherpad version has ep_auth_session module installed 
    https://github.com/Kurounin/ep_auth_session
    """
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        groupID = self.object.eth_group.groupID
        print('User:',self.request.user.id)
        author = AuthorMap.objects.all().filter(user=self.request.user.id)
        print('Author:',author)
        authorID = author[0].authorid
        print('Author:', authorID)

        # @createe session just for the duration of the activity
        NextDay_Date = datetime.datetime.today() + datetime.timedelta(days=1)
        res2 = call('createSession',{'authorID':authorID,'groupID':groupID,'validUntil':NextDay_Date.timestamp()})
        auth_session = res2['data']['sessionID']

        context['sessionid'] = auth_session
        return context
