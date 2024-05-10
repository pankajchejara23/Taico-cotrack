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
    if (group_diff > 0):
        for g in range(group_diff):
            g =  g +  org_groups + 1
            pad_name = f'{group_name}_group_{g}'
            print('Pad name:',pad_name)
            # call to create pad
            pad_create_response = call('createGroupPad',
                                        {
                                            'groupID':etherpad_groupid,
                                            'padName':pad_name
                                        })
            print('Creating pad:', pad_create_response)
            if pad_create_response["code"]==0:
                pad_object = Pad.objects.create(eth_group=pad_group_object,
                                                    eth_padid=pad_name)
                print('Pad created')
            else:
                status = False
    else:
        group_diff = abs(group_diff)
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
                                                    eth_padid=pad_create_response['data']['padID'])
                print('Pad created')
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

        for pad in pads:
            padid = pad.eth_padid
            params = {'padID':padid}
            print('Params:',params)
            rev_count = call('getRevisionsCount', params)

            total_revisions = rev_count['data']['revisions']

            for revision in range(total_revisions):
                params = {'padID':padid,'rev':revision+1}

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
                    logs.append([datetime.datetime.fromtimestamp(d["data"]/1000).strftime('%H:%M:%S %d-%m-%Y'),ath['data'],p.group,char_bank,rev['data'].replace('\n','<br/>'),cs['source_length'],cs['final_op'],cs['final_diff'],text])
                except:
                    continue
        return logs
   

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


# Etherpad changeset processing code

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