from django.test import TestCase, Client
from django.contrib.auth.models import User
from slat.models import Profile, Project
from http import HTTPStatus
from pyquery import PyQuery
from slat.views import make_demo
import django.http

class PermissionTestCase(TestCase):
    def setUp(self):
        # Create three new users:
        new_user = User.objects.create_user(username='samspade',
                                            first_name='Samuel',
                                            last_name='Spade',
                                            email='samspade@spadeandarcher.com',
                                            password='maltesefalcon')
        new_user.save()
        profile = Profile.objects.get(user=new_user)
        profile.organization = 'Spade and Archer'
        
        profile.save()

        new_user = User.objects.create_user(username='marlowe',
                                            first_name='Philip',
                                            last_name='Malowe',
                                            email='marlowe@marlowinvestigations.com',
                                            password='thebigsleep')
        new_user.save()
        profile = Profile.objects.get(user=new_user)
        profile.organization = 'Marlowe Investigations'
        profile.save()

        new_user = User.objects.create_user(username='holmes',
                                            first_name='Sherlock',
                                            last_name='Holmes',
                                            email='sholmes@holmesandwatson.co.uk',
                                            password='elementary')
        new_user.save()
        profile = Profile.objects.get(user=new_user)
        profile.organization = 'Holmes and Watson'
        profile.save()

        # Create some demo projects
        samspade = User.objects.get(username='samspade')

        if len(Project.objects.filter(title_text="Sam Spade's Demo Project")) == 0:
            project = make_demo(samspade)
            project.title_text = "Sam Spade's Demo Project"
            project.save()

        if len(Project.objects.filter(title_text="Sam Spade's Other Demo Project")) == 0:
            project = make_demo(samspade)
            project.title_text = "Sam Spade's Other Demo Project"
            project.save()

        marlowe = User.objects.get(username='marlowe')
        if len(Project.objects.filter(title_text="Phil Marlowe's First Project")) == 0:
            project = make_demo(marlowe)
            project.title_text = "Phil Marlowe's First Project"
            project.save()

        if len(Project.objects.filter(title_text="Phil Marlowe's Second Project")) == 0:
            project = make_demo(marlowe)
            project.title_text = "Phil Marlowe's Second Project"
            project.save()

        if len(Project.objects.filter(title_text="Sherlock's Project")) == 0:
            holmes = User.objects.get(username='holmes')
            project = make_demo(holmes)
            project.title_text = "Sherlock's Project"
            project.save()

    def test_default_access(self):
        """Each user can only see their own projects"""
        c = Client()
        # Log in as Sam Spade:
        response = c.post('/login/?next=/slat/', {'username': 'samspade', 'password': 'maltesefalcon'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)

        # Should redirect to the login page:
        response = c.get('/slat/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        pq = PyQuery(response.content)
        self.assertEqual(pq('title').text(), 'WebSLAT Project List')

        # Check the list of projects:
        self.assertEqual(len(pq('ul').children()), 2)
        self.assertEqual(pq('ul').children().eq(0).text(), "Sam Spade's Demo Project")
        self.assertEqual(pq('ul').children().eq(1).text(), "Sam Spade's Other Demo Project")

        # Log in as Philip Marlowe:
        response = c.post('/login/?next=/slat/', {'username': 'marlowe', 'password': 'thebigsleep'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)

        # Should redirect to the login page:
        response = c.get('/slat/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        pq = PyQuery(response.content)
        self.assertEqual(pq('title').text(), 'WebSLAT Project List')

        # Check the list of projects:
        self.assertEqual(len(pq('ul').children()), 2)
        self.assertEqual(pq('ul').children().eq(0).text(), "Phil Marlowe's First Project")
        self.assertEqual(pq('ul').children().eq(1).text(), "Phil Marlowe's Second Project")

        # Log in as Sherlock Holmes:
        response = c.post('/login/?next=/slat/', {'username': 'holmes', 'password': 'elementary'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)

        # Should redirect to the login page:
        response = c.get('/slat/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        pq = PyQuery(response.content)
        self.assertEqual(pq('title').text(), 'WebSLAT Project List')

        # Check the list of projects:
        self.assertEqual(len(pq('ul').children()), 1)
        self.assertEqual(pq('ul').children().eq(0).text(), "Sherlock's Project")


