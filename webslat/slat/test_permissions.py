sfrom django.test import TestCase, Client
from django.contrib.auth.models import User
from slat.models import Profile
from http import HTTPStatus
from pyquery import PyQuery
import django.http

class LoginTestCase(TestCase):
    def setUp(self):
        new_user = User.objects.create_user(username='samspade',
                                            first_name='Samuel',
                                            last_name='Spade',
                                            email='samspade@spadeandarcher.com',
                                            password='maltese')
        new_user.save()
        profile = Profile.objects.get(user=new_user)
        profile.organization = 'Spade and Archer'
        profile.save()

    def test_samspade_login(self):
        """Sam Spade can log in"""
        c = Client()
        response = c.get('/slat/')
        # Should redirect to the login page:
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)
        self.assertEqual(response.url, '/login?next=/slat/')

        # Bad password:
        #response = c.post('/login/?next=/slat/', {'username': 'samspade', 'password': 'malteser'})
        response = c.post(response.url, {'username': 'samspade', 'password': 'malteser'})
        self.assertEqual(response.status_code, HTTPStatus.MOVED_PERMANENTLY)
        self.assertIsInstance(response, django.http.response.HttpResponsePermanentRedirect)

        # Good password:
        response = c.post('/login/?next=/slat/', {'username': 'samspade', 'password': 'maltese'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)

        # Should redirect to the login page:
        response = c.get('/slat/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        pq = PyQuery(response.content)
        self.assertEqual(pq('title').text(), 'WebSLAT Project List')

        
