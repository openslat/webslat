import pyslat
from django.test import TestCase, Client
from django.contrib.auth.models import User
from slat.models import Profile, Project, ProjectUserPermissions, EDP, Level, EDP_Grouping
from http import HTTPStatus
from pyquery import PyQuery
from slat.views import make_demo
import django.http

class PermissionTestCase(TestCase):
    def setUp(self):
        # Direct SLAT warnings to STDOUT, so they can easily be ignored
        pyslat.SetLogFile("permissions_test_log.txt")
        pyslat.LogToStdErr(False)

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
            project = make_demo(samspade, 
                                "Sam Spade's Demo Project",
                                "This is Sam's demo project.")
            project.save()

        if len(Project.objects.filter(title_text="Sam Spade's Empty Project")) == 0:
            project = Project()
            setattr(project, 'title_text', "Sam Spade's Empty Project")
            setattr(project, 'description_text', "Describe this project...")
            setattr(project, 'rarity', 1/500)
            project.save()
            project.AssignRole(samspade, ProjectUserPermissions.ROLE_FULL)

        marlowe = User.objects.get(username='marlowe')
        if len(Project.objects.filter(title_text="Phil Marlowe's First Project")) == 0:
            project = make_demo(marlowe, 
                                "Phil Marlowe's First Project",
                                "This is Marlowes' first project.")
            project.save()

        if len(Project.objects.filter(title_text="Phil Marlowe's Second Project")) == 0:
            project = make_demo(marlowe, 
                                "Phil Marlowe's Second Project",
                                "This is Marlowe's second project.")
            project.save()

        if len(Project.objects.filter(title_text="Sherlock's Project")) == 0:
            holmes = User.objects.get(username='holmes')
            project = make_demo(holmes, 
                                "Sherlock's Project",
                                "This is Sherlock's project.")
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
        projects = list(map(lambda x: x.text_content().strip(), pq('ul').children()))
        self.assertEqual(len(pq('ul').children()), 2)
        self.assertTrue( "Sam Spade's Demo Project" in projects)
        self.assertTrue( "Sam Spade's Empty Project" in projects)

        # Log in as Philip Marlowe:
        response = c.post('/login/?next=/slat/', {'username': 'marlowe', 'password': 'thebigsleep'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)

        # Should redirect to the login page:
        response = c.get('/slat/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(pq('title').text(), 'WebSLAT Project List')

        # Check the list of projects:
        pq = PyQuery(response.content)
        projects = list(map(lambda x: x.text_content().strip(), pq('ul').children()))
        self.assertEqual(len(projects), 2)
        self.assertTrue( "Phil Marlowe's First Project" in projects)
        self.assertTrue( "Phil Marlowe's Second Project" in projects)

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
        pq = PyQuery(response.content)
        projects = list(map(lambda x: x.text_content().strip(), pq('ul').children()))
        self.assertEqual(len(projects), 1)
        self.assertTrue( "Sherlock's Project" in projects)


    def test_access_changes(self):
        """Change permissions, and make sure projects are visible to the correct users."""

        # Grant Philip Marlowe access to one of Sam Spade's projects:
        Project.objects.get(title_text="Sam Spade's Empty Project").AssignRole(
            User.objects.get(username="marlowe"),
            ProjectUserPermissions.ROLE_FULL)
        
        c = Client()

        # Phil Marlowe should be able to see the project:
        response = c.post('/login/?next=/slat/', {'username': 'marlowe', 'password': 'thebigsleep'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)

        # Should redirect to the login page:
        response = c.get('/slat/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        pq = PyQuery(response.content)
        self.assertEqual(pq('title').text(), 'WebSLAT Project List')

        # Check the list of projects:
        pq = PyQuery(response.content)
        projects = list(map(lambda x: x.text_content().strip(), pq('ul').children()))
        self.assertEqual(len(projects), 3)
        self.assertTrue( "Sam Spade's Empty Project" in projects)
        self.assertTrue( "Phil Marlowe's First Project" in projects)
        self.assertTrue( "Phil Marlowe's Second Project" in projects)

        # Sam should still see all his projects:
        response = c.post('/login/?next=/slat/', {'username': 'samspade', 'password': 'maltesefalcon'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)

        # Should redirect to the login page:
        response = c.get('/slat/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        pq = PyQuery(response.content)
        self.assertEqual(pq('title').text(), 'WebSLAT Project List')

        # Check the list of projects:
        pq = PyQuery(response.content)
        projects = list(map(lambda x: x.text_content().strip(), pq('ul').children()))
        self.assertEqual(len(projects), 2)
        self.assertTrue( "Sam Spade's Demo Project" in projects)
        self.assertTrue( "Sam Spade's Empty Project" in projects)

        # Sherlock still sees only his own projects:
        response = c.post('/login/?next=/slat/', {'username': 'holmes', 'password': 'elementary'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)

        # Should redirect to the login page:
        response = c.get('/slat/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        pq = PyQuery(response.content)
        self.assertEqual(pq('title').text(), 'WebSLAT Project List')

        # Check the list of projects:
        pq = PyQuery(response.content)
        projects = list(map(lambda x: x.text_content().strip(), pq('ul').children()))
        self.assertEqual(len(projects), 1)
        self.assertTrue( "Sherlock's Project" in projects)

        # Remove access from Sam:
        Project.objects.get(title_text="Sam Spade's Empty Project").AssignRole(
            User.objects.get(username="samspade"),
            ProjectUserPermissions.ROLE_NONE)
        
        # Phil Marlowe should still be able to see the project:
        response = c.post('/login/?next=/slat/', {'username': 'marlowe', 'password': 'thebigsleep'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)

        # Should redirect to the login page:
        response = c.get('/slat/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        pq = PyQuery(response.content)
        self.assertEqual(pq('title').text(), 'WebSLAT Project List')

        # Check the list of projects:
        projects = list(map(lambda x: x.text_content().strip(), pq('ul').children()))
        self.assertEqual(len(projects), 3)
        self.assertTrue("Sam Spade's Empty Project" in projects)
        self.assertTrue("Phil Marlowe's First Project" in projects)
        self.assertTrue("Phil Marlowe's Second Project" in projects)

        # Sam should no longer see this project:
        response = c.post('/login/?next=/slat/', 
                          {'username': 'samspade', 'password': 'maltesefalcon'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)

        # Should redirect to the login page:
        response = c.get('/slat/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        pq = PyQuery(response.content)
        self.assertEqual(pq('title').text(), 'WebSLAT Project List')

        # Check the list of projects:
        pq = PyQuery(response.content)
        projects = list(map(lambda x: x.text_content().strip(), pq('ul').children()))
        self.assertEqual(len(projects), 1)
        self.assertTrue( "Sam Spade's Demo Project" in projects)

        # Sherlock still sees only his own projects:
        response = c.post('/login/?next=/slat/', {'username': 'holmes', 'password': 'elementary'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)

        # Should redirect to the login page:
        response = c.get('/slat/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        pq = PyQuery(response.content)
        self.assertEqual(pq('title').text(), 'WebSLAT Project List')

        # Check the list of projects:
        pq = PyQuery(response.content)
        projects = list(map(lambda x: x.text_content().strip(), pq('ul').children()))
        self.assertEqual(len(projects), 1)
        self.assertTrue( "Sherlock's Project" in projects)

    def test_url_munging(self):
        """Make sure projects are protected against URL editing"""
        c = Client()
        # Log in as Sam Spade:
        response = c.post('/login/?next=/slat/', {'username': 'samspade', 'password': 'maltesefalcon'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)

        urls = ["/slat/project/{PROJECT}",
                "/slat/project/{PROJECT}/hazard",
                "/slat/project/{PROJECT}/hazard/choose",
                "/slat/project/{PROJECT}/hazard/nzs",
                "/slat/project/{PROJECT}/hazard/nzs/edit",
                "/slat/project/{PROJECT}/hazard/nlh",
                "/slat/project/{PROJECT}/hazard/nlh/edit",
                "/slat/project/{PROJECT}/hazard/interp",
                "/slat/project/{PROJECT}/hazard/interp/edit",
                "/slat/project/{PROJECT}/hazard/interp/import",
                "/slat/project/{PROJECT}/level",
                "/slat/project/{PROJECT}/edp/{EDP}",
                "/slat/project/{PROJECT}/edp/{EDP}/choose",
                "/slat/project/{PROJECT}/edp/{EDP}/power",
                "/slat/project/{PROJECT}/edp/{EDP}/power/edit",
                "/slat/project/{PROJECT}/edp/{EDP}/userdef",
                "/slat/project/{PROJECT}/edp/{EDP}/userdef/import",
                "/slat/project/{PROJECT}/edp/{EDP}/userdef/edit",
                "/slat/project/{PROJECT}/analysis"]

        for project_title, status in [
                ["Sam Spade's Demo Project", [HTTPStatus.OK, HTTPStatus.FOUND]],
                ["Sam Spade's Empty Project", [HTTPStatus.OK, HTTPStatus.FOUND, HTTPStatus.NOT_FOUND]],
                ["Phil Marlowe's First Project", [HTTPStatus.FORBIDDEN]]]:

            project = Project.objects.get(title_text=project_title)
            
            levels = Level.objects.filter(project=project)
            demands =  EDP_Grouping.objects.filter(project=project)

            if len(levels) > 0:
                demand = demands.get(level=levels.get(level=project.num_levels())).pk
            else:
                demand = None

            for url in urls:
                u = url.replace("{PROJECT}", str(project.pk)).replace("{EDP}", str(demand))
                response = c.get(u)
                self.assertIn(response.status_code, status)
