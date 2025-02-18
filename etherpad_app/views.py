from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView
from django.db import transaction
from .forms import PadCreateForm
from .models import PadGroup, Pad, AuthorMap
from .models import call
import datetime
from django.conf import settings
import re
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
    # make a call to etherpad using http api for creating a new user
    res = call('createAuthorIfNotExistsFor', mapping)
    if 'authorID' in res['data']:
        return res['data']['authorID']
    else:
        return None


def get_author_user_objects(authorid):
    """Returns User object associated with authorid

    Args:
        authorid (str): Etherapd user id
    """
    author_map =  AuthorMap.objects.filter(authorid=authorid)

    return author_map

def get_padid(etherpad_group, group_number):
    """This function returns pad id of specified group number belonging to a particular etherpad group.

    Args:
        etherpad_group (str): Etherpad group id
        group_number (int): Group number

    Returns:
        int: Pad id
    """
    pad_group_object = PadGroup.objects.filter(groupID=etherpad_group).first()

    pad_object = Pad.objects.filter(eth_group=pad_group_object, group_number=group_number).first()

    if pad_object is not None:
        return pad_object.id
    else:
        return None


def create_session(mapping):
    """This function generate a link to a pad in the Etherpad for specified groupid

    Args:
        mapping (dict): This mapping contains 'authorID' about the user for whom the pad
                        link is generated, 'groupID' that is Etherpad group id associated with the pad,
                        and 'validUntil' which contains timestamp until when the pad is accessible.
    """
    # make a call to etherpad using http api for creating a new session
    result = call('createSession', mapping)
    if 'sessionID' in result['data']:
        return result['data']['sessionID']
    else:
        return None


def update_pads(etherpad_groupid, group_name, org_groups, new_groups):
    """This function updates the pads according to new number of groups.

    Args:
        etherpad_groupid (str): Etherpad Groupid
        session_id(int): Session primary key
        org_groups (int): number of groups before update
        newgroups (int): number of groups after update
    """
    status = True
    pad_group_object = PadGroup.objects.filter(groupID = etherpad_groupid)[0]
    group_diff = new_groups - org_groups

    # check if need to create more pads or delete them
    if (group_diff > 0):
        for g in range(group_diff):
            g =  g +  org_groups + 1
            pad_name = f'{group_name}_group_{g}'
            # call to create a group pad in etherpad
            pad_create_response = call('createGroupPad',
                                        {
                                            'groupID':etherpad_groupid,
                                            'padName':pad_name
                                        })
            if pad_create_response["code"]==0:

                # saving group pad data
                pad_object = Pad.objects.create(eth_group=pad_group_object,
                                                    eth_padid=pad_name)
            else:
                status = False
    else:
        group_diff = abs(group_diff)

        # delete pads according to new number of groups
        for g in range(group_diff):
            del_group = g + new_groups + 1
            pad_name = f'{group_name}_group_{del_group}'
            res = call('deletePad',{'padID':pad_name})
            Pad.objects.filter(eth_group = pad_group_object).fitler(group=del_group).delete()
    return status
  

def create_pads(pad_number, group_name):
    """This function creates n pads in Etherpad with a Etherpad group with the specified name

    Args:
        pad_number (int): Number of pads to create in Etherpad
        group_name (str): Name of Etherpad group

    Returns:
        str: Etherpad group id
    """
    result = {'status':'failure'}
    # call to create etherpad group, all pads in etherpad are associated with a group
    group_create_response = call('createGroup')
    eth_group_id = None
            
    # check for successful execution of the call
    if (group_create_response["code"] == 0):
        eth_group_id = group_create_response["data"]["groupID"]
        pad_group_object = PadGroup.objects.create(group=group_name,
                                                    groupID=eth_group_id)

        # create n pads in etherpad
        for num in range(1,int(pad_number)+1):
            #prepare pad name
            pad_name = f'{group_name}_group_{num}'

            # call to create pad
            pad_create_response = call('createGroupPad',
                                        {
                                            'groupID':eth_group_id,
                                            'padName':pad_name
                                        })
            if pad_create_response["code"]==0:
                pad_object = Pad.objects.create(eth_group=pad_group_object,
                                                    eth_padid=pad_create_response['data']['padID'],
                                                    group_number = num)
        result['status'] = 'success'
        result['group_id'] = eth_group_id
    return result


def download_logs(etherpad_group_id):
    """This function downloads logs of all pads associated with etherpad_group_id.

    Args:
        etherpad_group_id (str): Etherpad group id
    Returns:
        HttpResponse: download a csv file on client
    """
    pad_groups = PadGroup.objects.filter(groupID = etherpad_group_id)
    if pad_groups.count() == 0:
        return None
    else:
        logs = []
        pad_group = pad_groups[0]
        pads = Pad.objects.filter(eth_group = pad_group)

        # iterate for each pad associated with pad_group
        for pad in pads:
            padid = pad.eth_padid.split('$')[1]
            params = {'padID':padid}

            # call to get number of revisions made in the pad
            # change in etherpad 1.9.7 (previously:getRevisionsCount, new:getSavedRevisionsCount)
            rev_count = call('getRevisionsCount', params)

            # pad has not bee used (means no revision data)
            if rev_count is None:
                continue

            # get the number of revisions
            if rev_count and rev_count['data']:
                total_revisions = rev_count['data']['revisions']
            else:
                total_revisions = 0

            # for each revision get information, i.e., author, time, changeset.
            for revision in range(total_revisions):
                try:
                    params = {'padID':padid,'rev':revision+1}

                    # call to get the revision changeset; changeset is a way of etherpad to keep information about the update
                    rev = call('getRevisionChangeset',params)
   
                    # call to get author info who made the update
                    ath = call('getRevisionAuthor',params)

                    # call to get timestamp of update
                    d = call('getRevisionDate',params)

                    # call to get text in the etherpad
                    t = call('getText',params)

                    # process changeset to extract information about the udpate (what operation, what was added/deleted, etc.)
                    cs = changeset_parse(rev['data'])
                    tp = int(d['data'])
                    text = t['data']['text']
                    char_bank = cs['bank']

                    # adding <br/> for new lines
                    char_bank = "<br/>".join(char_bank.split("\n"))

                    # adding <br/> for new lines
                    text = "<br/>".join(text.split("\n"))

                    # adding log data to the list
                    logs.append([datetime.datetime.fromtimestamp(d["data"]/1000).strftime('%H:%M:%S %d-%m-%Y'),
                                 ath['data'],
                                 pad.group_number,
                                 char_bank,rev['data'].replace('\n','<br/>'),
                                 cs['source_length'],
                                 cs['final_op'],
                                 cs['final_diff'],
                                 text])
                except Exception as error:
                    print('Error:',error)
        # return the list 
        return logs
   

class PadCreateFormView(View):
    """View to display and handle pad creation

    """
    form_class = PadCreateForm
    template_name ='create_pad.html'
    success_template = 'success.html'

    def get(self, request, *args, **kwargs):
        """This function renders pad creation form

        """
        form = self.form_class()
        return render(request, self.template_name, {'form':form})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """This function processes pad creation form submission.

        """
        # populating form with input data
        form = self.form_class(request.POST)

        # form validity check
        if form.is_valid():
            pad_number = form.cleaned_data.get('pad_number')
            group_name = form.cleaned_data.get('group_name')

            # call to make pads in etherpad
            result = create_pads(pad_number, group_name)
            if result['status'] == 'failure':
                #@todo: failure message showing
                pass
        return render(request, self.success_template)
    

class PadListView(ListView):
    """This view shows a list of all created pads.

    """
    model = Pad
    template_name = 'pad_list.html'


class PadDetailView(DetailView):
    """This view creates a session for etherpad and displays the pad.
    """
    template_name = 'pad_detail.html'
    model = Pad
    """
    Important: Make sure your etherpad version has ep_auth_session module installed 
    https://github.com/Kurounin/ep_auth_session
    """
    def get_context_data(self, *args, **kwargs):
        """This function adds additional data to the context.

        """
        # get the context data
        context = super().get_context_data(**kwargs)

        # get groupid
        groupID = self.object.eth_group.groupID

        # get etherpad user-id for the current user
        author = AuthorMap.objects.all().filter(user=self.request.user.id)
        authorID = author[0].authorid

        # createe session just for the duration of the activity
        NextDay_Date = datetime.datetime.today() + datetime.timedelta(days=1)
        res2 = call('createSession',{'authorID':authorID,'groupID':groupID,'validUntil':NextDay_Date.timestamp()})
        auth_session = res2['data']['sessionID']

        # adding session id 
        context['sessionid'] = auth_session

        context['protocol'] = 'https'
        context['server'] = 'www.etherpad.website'
        return context

######### REST APIs START ###############


######### REST APIs END   ###############




################### Etherpad Changeset Processing ######################
def changeset_parse (c) :
    changeset_pat = re.compile(r'^Z:([0-9a-z]+)([><])([0-9a-z]+)(.+?)\$')
    op_pat = re.compile(r'(\|([0-9a-z]+)([\+\-\=])([0-9a-z]+))|([\*\+\-\=])([0-9a-z]+)')

    def parse_op (m):
        g = m.groups()
        if g[0]:
            if g[2] == "+":
                op = "insert"
            elif g[2] == "-":
                op = "delete"
            else:
                op = "hold"
            return {
                'raw': m.group(0),
                'op': op,
                'lines': int(g[1], 36),
                'chars': int(g[3], 36)
            }
        elif g[4] == "*":
            return {
                'raw': m.group(0),
                'op': 'attr',
                'index': int(g[5], 36)
            }
        else:
            if g[4] == "+":
                op = "insert"
            elif g[4] == "-":
                op = "delete"
            else:
                op = "hold"
            return {
                'raw': m.group(0),
                'op': op,
                'chars': int(g[5], 36)
            }

    m = changeset_pat.search(c)
    bank = c[m.end():]
    g = m.groups()
    ops_raw = g[3]
    op = None

    ret = {}
    ret['raw'] = c
    ret['source_length'] = int(g[0], 36)
    ret['final_op'] = g[1]
    ret['final_diff'] = int(g[2], 36)
    ret['ops_raw'] = ops_raw
    ret['ops'] = ops = []
    ret['bank'] = bank
    ret['bank_length'] = len(bank)
    for m in op_pat.finditer(ops_raw):
        ops.append(parse_op(m))
    return ret

def perform_changeset_curline (text, c):
    textpos = 0
    curline = 0
    curline_charpos = 0
    curline_insertchars = 0
    bank = c['bank']
    bankpos = 0
    newtext = ''
    current_attributes = []

    # loop through the operations
    # rebuilding the final text
    for op in c['ops']:
        if op['op'] == "attr":
            current_attributes.append(op['index'])
        elif op['op'] == "insert":
            newtextposition = len(newtext)
            insertion_text = bank[bankpos:bankpos+op['chars']]
            newtext += insertion_text
            bankpos += op['chars']
            if 'lines' in op:
                curline += op['lines']
                curline_charpos = 0
            else:
                curline_charpos += op['chars']
                curline_insertchars = op['chars']
            # todo PROCESS attributes
            # NB on insert, the (original/old/previous) textpos does *not* increment...
        elif op['op'] == "delete":
            newtextposition = len(newtext) # is this right?
            # todo PROCESS attributes
            textpos += op['chars']

        elif op['op'] == "hold":
            newtext += text[textpos:textpos+op['chars']]
            textpos += op['chars']
            if 'lines' in op:
                curline += op['lines']
                curline_charpos = 0
            else:
                curline_charpos += op['chars']

    # append rest of old text...
    newtext += text[textpos:]
    return newtext, curline, curline_charpos, curline_insertchars
###############################################################