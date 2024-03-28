from django import forms
from django.utils.translation import gettext as _

class PadCreateForm(forms.Form):
    """
    Form to create etherpad group and N number of pads
    """

    pad_number = forms.IntegerField(label=_("Number of pads"),
                                    widget=forms.NumberInput(attrs={
                                        'class':'form-control'
                                        })
                                    )
    group_name = forms.CharField(label=_("Group name"), max_length=100,
                                 widget=forms.TextInput(attrs={
                                     'class':'form-control'
                                 }))