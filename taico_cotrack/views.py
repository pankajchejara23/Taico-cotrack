from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.utils import translation
from urllib.parse import unquote
from django.conf import settings

def change_language(request, lang_code):
    """Change user language for translation.
       url: '/change_lang'

    Args:
        request (HttpRequest): request object
        lang_code(str): language code
    """
    next = request.META.get('HTTP_REFERER')
    next = next and unquote(next)  # HTTP_REFERER may be encoded.
    response = HttpResponse(status=204)
    if lang_code == 'et':
        next = next.replace('/en/', '/et/')
    if lang_code == 'en':
        next = next.replace('/et/', '/en/')
    response = HttpResponseRedirect(next)
    return response