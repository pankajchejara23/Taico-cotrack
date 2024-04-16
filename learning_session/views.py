from django.shortcuts import render
from .models import Session
from django.views.generic import ListView, DetailView


# Create your views here.

class SessionListView(ListView):
    model = Session
    template_name = ''

