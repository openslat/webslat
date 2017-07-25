from django.shortcuts import render, get_object_or_404

def welcome(request):
    return render(request, 'welcome/welcome.html')
