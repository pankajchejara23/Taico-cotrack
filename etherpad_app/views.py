from django.shortcuts import render
from django.views import View
from django.db import transaction
from .forms import PadCreateForm
from .models import PadGroup, Pad
from .models import call
# Create your views here.

class PadCreateFormView(View):
    form_class = PadCreateForm
    template_name ='create_pad.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form':form})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            pad_number = form.cleaned_data.get('pad_number')
            group_name = form.cleaned_data.get('group_name')

            # call to create etherpad group
            group_create_response = call('createGroup', request=self.request)
            eth_group_id = None
            
            # check for successful execution of the call
            if (group_create_response["code"] == 0):
                eth_group_id = group_create_response["data"]["groupID"]
                pad_group_object = PadGroup.objects.create(group=group_name,
                                                           groupID=eth_group_id)

                # create n pads
                for num in range(pad_number):
                    #prepare pad name
                    pad_name = f'{group_name}_group_{num}'

                    # call to create pad
                    pad_create_response = call('createGroupPad',
                                               {
                                                   'groupID':eth_group_id,
                                                   'padName':pad_name
                                               },request=self.request)
                    if pad_create_response["code"]==0:
                        pad_object = Pad.objects.create(eth_group=pad_group_object,
                                                    eth_padid=pad_name)

        return render('success.html')