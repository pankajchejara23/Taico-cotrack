from django.apps import AppConfig
import os
from django.conf import settings
import pickle

class LearningSessionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "learning_session"


class ApiConfig(AppConfig):
    name = 'api'
    CQ_MODEL_FILE = os.path.join(settings.MEDIA_ROOT,"CQ_model_66percent.pkl")
    ARG_MODEL_FILE = os.path.join(settings.MEDIA_ROOT,"ARG_model_66percent.pkl")
    #cq_model = pickle.load(open(CQ_MODEL_FILE,'rb'))
    #arg_model = pickle.load(open(ARG_MODEL_FILE,'rb'))