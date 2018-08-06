from celery import shared_task,current_task
from numpy import random
from scipy.fftpack import fft

@shared_task
def fft_random(n):
    """
    Brainless number crunching just to have a substantial task:
    """
    for i in range(n):
        x = random.normal(0, 0.1, 2000)
        y = fft(x)
        if(i%30 == 0):
            process_percent = int(100 * float(i) / float(n))
            current_task.update_state(state='PROGRESS',
                                      meta={'process_percent': process_percent})
    return random.random()

@shared_task
def add(x,y):
    for i in range(1000000000):
        a = x+y
    return x+y

from .etabs import ImportETABS
from .models import User, ProjectUserPermissions

@shared_task
def celery_ImportETABS(title, description, strength, path, location, soil_class, return_period, frame_type):
    current_task.update_state(state='PROGRESS', meta={'process_percent': 50})
    time.sleep(0.25)
    project = ImportETABS(title, description, 
                          strength, path, location,
                          soil_class, return_period, frame_type)
    project.AssignRole(User.objects.get(username='samspade'),
                                        ProjectUserPermissions.ROLE_FULL)
    return project


