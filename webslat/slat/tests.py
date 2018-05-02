import pyslat
from django.test import TestCase, Client
from django.contrib.auth.models import User
from slat.models import Profile, Project, ProjectPermissions, EDP, Level
from http import HTTPStatus
from pyquery import PyQuery
from slat.views import make_demo
import numpy as np
import django.http

# Create your tests here.
class PermissionTestCase(TestCase):
    def setUp(self):
        data = np.genfromtxt('example2/imfunc.csv', comments="#", delimiter=",", invalid_raise=True)
        print(data)

    def test_stuff(self):
        self.assertTrue(True)
