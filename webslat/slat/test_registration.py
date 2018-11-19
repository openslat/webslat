from django.test import TestCase, Client
from django.contrib.auth.models import User
from slat.models import Profile
from http import HTTPStatus
from pyquery import PyQuery
import django.http

class RegistrationTestCase(TestCase):
    def test_registration(self):
        """Test registration"""

        c = Client()

        # Register a user, with a bad password:
        response = c.post('/slat/accounts/register/',
                          {
                              'first_name':'Samuel',
                              'last_name':'Spade',
                              'email':'samspade@spadeandarcher.com',
                              'username': 'samspade',
                              'password1':'maltese',
                              'password2':'maltese',
                              'organization':'Spade and Archer'
                          })
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIsInstance(response, django.template.response.TemplateResponse)

        pq = PyQuery(response.content)
        self.assertEqual(pq('ul').filter('.errorlist').eq(1).text(),
                         'This password is too short. It must contain at least 8 characters.')

        # Register a user, with mis-matched passwords:
        response = c.post('/slat/accounts/register/',
                          {
                              'first_name':'Samuel',
                              'last_name':'Spade',
                              'email':'samspade@spadeandarcher.com',
                              'username': 'samspade',
                              'password1':'maltesefalcon',
                              'password2':'maltesefulrum',
                              'organization':'Spade and Archer'
                          })
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIsInstance(response, django.template.response.TemplateResponse)

        pq = PyQuery(response.content)
        self.assertEqual(pq('ul').filter('.errorlist').eq(1).text(),
                         "The two password fields didn't match.")

        # Make sure user wasn't created:
        self.assertEqual(len(User.objects.all()), 0)

        # Register a user, with a good password:
        response = c.post('/slat/accounts/django_register/',
                          {
                              'first_name':'Samuel',
                              'last_name':'Spade',
                              'email':'samspade@spadeandarcher.com',
                              'username': 'samspade',
                              'password1':'maltesefalcon',
                              'password2':'maltesefalcon',
                              'organization':'Spade and Archer'
                          })
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)
        self.assertEqual(response.url, '/slat/')

        # Make sure the user was created, with the correct data:
        user = User.objects.get(username='samspade')
        self.assertEqual(user.username, 'samspade')
        self.assertEqual(user.first_name, 'Samuel')
        self.assertEqual(user.last_name, 'Spade')
        self.assertEqual(Profile.objects.get(user=user).organization, 'Spade and Archer')
        
