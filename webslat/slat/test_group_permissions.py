import pyslat
import re
from django.test import TestCase, Client
from django.contrib.auth.models import User
from slat.models import Profile, Project, \
    ProjectUserPermissions, Group, \
    EDP, Level
from http import HTTPStatus
from pyquery import PyQuery
from slat.views import make_demo
import django.http
from django.db import transaction

class GroupTestCase(TestCase):
    samspade=None
    marlowe=None
    holmes=None
    
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
        self.samspade = User.objects.get(username='samspade')

        if len(Project.objects.filter(title_text="Sam Spade's Demo Project")) == 0:
            project = make_demo(self.samspade)
            project.title_text = "Sam Spade's Demo Project"
            project.save()

        if len(Project.objects.filter(title_text="Sam Spade's Empty Project")) == 0:
            project = Project()
            setattr(project, 'title_text', "Sam Spade's Empty Project")
            setattr(project, 'description_text', "Describe this project...")
            setattr(project, 'rarity', 1/500)
            project.save()
            project.AssignRole(self.samspade, ProjectUserPermissions.ROLE_FULL)

        self.marlowe = User.objects.get(username='marlowe')
        if len(Project.objects.filter(title_text="Phil Marlowe's First Project")) == 0:
            project = make_demo(self.marlowe)
            project.title_text = "Phil Marlowe's First Project"
            project.save()

        if len(Project.objects.filter(title_text="Phil Marlowe's Second Project")) == 0:
            project = make_demo(self.marlowe)
            project.title_text = "Phil Marlowe's Second Project"
            project.save()

        if len(Project.objects.filter(title_text="Sherlock's Project")) == 0:
            self.holmes = User.objects.get(username='holmes')
            project = make_demo(self.holmes)
            project.title_text = "Sherlock's Project"
            project.save()

    def test_group_create(self):
        """Create a group. Make sure it has no members, and cannot access any projects."""
        group = Group(name="Empty Group")
        group.save()

        for user in User.objects.all():
            self.assertFalse(group.IsMember(user))

    def test_group_create_duplicate(self):
        """Create a group, then create a second group with the same name. This
        should *not* be allowed."""
        group1 = Group(name="Empty Group")
        group1.save()

        group2 = Group(name="Empty Group")
        self.assertRaises(django.db.utils.IntegrityError, group2.save)

    def test_group_rename(self):
        """Renaming a group should be allowed, unless it conflicts with an 
        existing name."""
        group1 = Group(name="Group 1")
        group1.save()

        group2 = Group(name="Group 2")
        group2.save()

        group1.name = "The Best Group"
        group1.save()

        group2.name = "The Best Group"
        with transaction.atomic():
            self.assertRaises(django.db.utils.IntegrityError, group2.save)

        group2.name = "The Second Best Group"
        group2.save()

    def test_group_membership(self):
        """Create a group. Add and remove members, confirming correct membership 
        along the way."""
        group1 = Group(name="Group #1")
        group1.save()
        group2 = Group(name="Group #2")
        group2.save()

        group1.AddMember(self.samspade)
        self.assertTrue(group1.IsMember(self.samspade))
        self.assertFalse(group1.IsMember(self.marlowe))
        self.assertFalse(group1.IsMember(self.holmes))

        self.assertFalse(group2.IsMember(self.samspade))
        self.assertFalse(group2.IsMember(self.marlowe))
        self.assertFalse(group2.IsMember(self.holmes))

        group2.AddMember(self.marlowe)
        self.assertTrue(group1.IsMember(self.samspade))
        self.assertFalse(group1.IsMember(self.marlowe))
        self.assertFalse(group1.IsMember(self.holmes))

        self.assertFalse(group2.IsMember(self.samspade))
        self.assertTrue(group2.IsMember(self.marlowe))
        self.assertFalse(group2.IsMember(self.holmes))

        group1.AddMember(self.holmes)
        group2.AddMember(self.holmes)
        self.assertTrue(group1.IsMember(self.samspade))
        self.assertFalse(group1.IsMember(self.marlowe))
        self.assertTrue(group1.IsMember(self.holmes))

        self.assertFalse(group2.IsMember(self.samspade))
        self.assertTrue(group2.IsMember(self.marlowe))
        self.assertTrue(group2.IsMember(self.holmes))

        # Remove a group member, and confirm group memberships are still correct:
        group1.RemoveMember(self.holmes)
        self.assertTrue(group1.IsMember(self.samspade))
        self.assertFalse(group1.IsMember(self.marlowe))
        self.assertFalse(group1.IsMember(self.holmes))

        self.assertFalse(group2.IsMember(self.samspade))
        self.assertTrue(group2.IsMember(self.marlowe))
        self.assertTrue(group2.IsMember(self.holmes))

    def test_project_addess(self):
        """Create a groups, and test user permissions based on group membership."""
        group1 = Group(name="Group #1")
        group1.save()
        group2 = Group(name="Group #2")
        group2.save()

        # Make sure no group has access yet:
        for project in Project.objects.all():
            self.assertFalse(group1.HasAccess(project))
            self.assertFalse(group2.HasAccess(project))

            
        sams_demo_project = Project.objects.get(title_text="Sam Spade's Demo Project")
        group1.GrantAccess(sams_demo_project)
        
        for project in Project.objects.all():
            if project == sams_demo_project:
                self.assertTrue(group1.HasAccess(project))
            else:
                self.assertFalse(group1.HasAccess(project))
                
            self.assertFalse(group2.HasAccess(project))
            
        # No one is in the group, so only Sam should be able to access the project:
        self.assertTrue(sams_demo_project.CanRead(self.samspade))
        self.assertTrue(sams_demo_project.CanWrite(self.samspade))

        self.assertFalse(sams_demo_project.CanRead(self.marlowe))
        self.assertFalse(sams_demo_project.CanWrite(self.marlowe))

        self.assertFalse(sams_demo_project.CanRead(self.holmes))
        self.assertFalse(sams_demo_project.CanWrite(self.holmes))

        # Add marlowe to the group, and confirm he has access:
        group1.AddMember(self.marlowe)
        self.assertTrue(sams_demo_project.CanRead(self.marlowe))
        self.assertTrue(sams_demo_project.CanWrite(self.marlowe))

        # ...but Holmes doesn't:
        self.assertFalse(sams_demo_project.CanRead(self.holmes))
        self.assertFalse(sams_demo_project.CanWrite(self.holmes))

        # Add holmes to the second group, and make sure he still doesn't have
        # access:
        group2.AddMember(self.holmes)
        self.assertFalse(sams_demo_project.CanRead(self.holmes))
        self.assertFalse(sams_demo_project.CanWrite(self.holmes))

        # Grant permission to group2; holmes should now have access:
        group2.GrantAccess(sams_demo_project)
        self.assertTrue(sams_demo_project.CanRead(self.holmes))
        self.assertTrue(sams_demo_project.CanWrite(self.holmes))

        # Remove access for group1; marlow no longer has access:
        group1.DenyAccess(sams_demo_project)
        self.assertFalse(sams_demo_project.CanRead(self.marlowe))
        self.assertFalse(sams_demo_project.CanWrite(self.marlowe))

    def test_web_membership(self):        
        """Create a group, and add a some members. Make sure the group
        page shows the correct members, and that each user is correctly shown
        as a member/non-member."""
        
        group1 = Group(name="Group #1")
        group1.save()
        
        c = Client()
        # Log in as Sam Spade:
        response = c.post('/login/?next=/slat/',
                          {'username': 'samspade', 
                           'password': 'maltesefalcon'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)
        
        # Go to Sam's home page, and check the list of groups:
        response = c.get('/slat/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        pq = PyQuery(response.content)
        groups = []
        for child in pq('ul').children():
            if re.compile("^/slat/group/").match(child.getchildren()[0].get('href')):
                groups.append(child.text_content().strip())
        self.assertEqual(len(groups), 0)

        # Should be denied access to the group page, because Sam's not a member:
        group_id = Group.objects.get(name="Group #1").id
        response = c.get('/slat/group/{}'.format(group_id))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

        # Add Sam to the group, and make sure he shows up on the group's page,
        # and that the group shows up on his:
        group1.AddMember(self.samspade)

        # Go to Sam's home page, and check the list of groups:
        response = c.get('/slat/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        pq = PyQuery(response.content)
        groups = []
        for child in pq('ul').children():
            if re.compile("^/slat/group/").match(child.getchildren()[0].get('href')):
                groups.append(child.text_content().strip())
        self.assertEqual(len(groups), 1)
        self.assertTrue("Group #1" in groups)

        # Should be allowed access to the group page, now that Sam's a member:
        group_id = Group.objects.get(name="Group #1").id
        response = c.get('/slat/group/{}'.format(group_id))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        pq = PyQuery(response.content)
        members = list(map(lambda x: x.text_content(), pq('ul').children()))
        self.assertEqual(len(members), 1)
        self.assertTrue("samspade" in members)

        # Other users should *not* be able to access the page:
        # Try Philip Marlowe first
        response = c.post('/login/?next=/slat/',
                          {'username': 'marlowe', 
                           'password': 'thebigsleep'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)
        
        # Go to Phil's home page, and check the list of groups:
        response = c.get('/slat/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        pq = PyQuery(response.content)
        groups = []
        for child in pq('ul').children():
            if re.compile("^/slat/group/").match(child.getchildren()[0].get('href')):
                groups.append(child.text_content().strip())
        self.assertEqual(len(groups), 0)
        
        # Should be denied access to the group page, because Sam's not a member:
        group_id = Group.objects.get(name="Group #1").id
        response = c.get('/slat/group/{}'.format(group_id))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

        # Now try Sherlock Holmes first
        response = c.post('/login/?next=/slat/',
                          {'username': 'holmes', 
                           'password': 'elementary'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)
        
        # Go to Sherlock's home page, and check the list of groups:
        response = c.get('/slat/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        pq = PyQuery(response.content)
        groups = []
        for child in pq('ul').children():
            if re.compile("^/slat/group/").match(child.getchildren()[0].get('href')):
                groups.append(child.text_content().strip())
        self.assertEqual(len(groups), 0)
        
        # Should be denied access to the group page, because Sam's not a member:
        group_id = Group.objects.get(name="Group #1").id
        response = c.get('/slat/group/{}'.format(group_id))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

        # Make sure Phil doesn't have access to Sam Spade's Demo Project:
        response = c.post('/login/?next=/slat/',
                          {'username': 'marlowe', 
                           'password': 'thebigsleep'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)
        
        # Go to Phil's home page, and check the list of projects:
        response = c.get('/slat/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        pq = PyQuery(response.content)
        projects = []
        for child in pq('ul').children():
            if re.compile("^/slat/project/").match(child.getchildren()[0].get('href')):
                projects.append(child.text_content().strip())
        self.assertFalse("Sam Spade's Demo Project" in projects)
        
        # Log in as Sam, and add Phil to the group:
        response = c.post('/login/?next=/slat/',
                          {'username': 'samspade', 
                           'password': 'maltesefalcon'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)

        response = c.post('/slat/group/{}/add_user'.format(group_id), {'userid': 'marlowe'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        # Try adding a non-existent user to the group:
        response = c.post('/slat/group/{}/add_user'.format(group_id), {'userid': 'wolfe'})
        self.assertTrue(re.compile("User wolfe not found.").search(str(response.content)))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        
        # Log in as Phil, and check group list:
        response = c.post('/login/?next=/slat/',
                          {'username': 'marlowe', 
                           'password': 'thebigsleep'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)

        # Go to Phil's home page, and check the project list--should *not* have
        # access to project yet, as it hasn't been added to the group:
        response = c.get('/slat/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        pq = PyQuery(response.content)
        projects = []
        for child in pq('ul').children():
            if re.compile("^/slat/project/").match(child.getchildren()[0].get('href')):
                projects.append(child.text_content().strip())
        self.assertFalse("Sam Spade's Demo Project" in projects)

        # ... but Phil should now be in the group:
        groups = []
        for child in pq('ul').children():
            if re.compile("^/slat/group/").match(child.getchildren()[0].get('href')):
                groups.append(child.text_content().strip())
        self.assertTrue("Group #1" in groups)

        # As Sam, add the project to the group:
        response = c.post('/login/?next=/slat/',
                          {'username': 'samspade', 
                           'password': 'maltesefalcon'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)

        project_id = Project.objects.get(title_text="Sam Spade's Demo Project").id
        response = c.post('/slat/project/{}/add_group'.format(project_id), {'groupid': 'Group #1'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        # Log in as Phil, and check that he now as access:
        response = c.post('/login/?next=/slat/',
                          {'username': 'marlowe', 
                           'password': 'thebigsleep'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)

        response = c.get('/slat/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        pq = PyQuery(response.content)
        projects = []
        for child in pq('ul').children():
            if re.compile("^/slat/project/").match(child.getchildren()[0].get('href')):
                projects.append(child.text_content().strip())
        self.assertTrue("Sam Spade's Demo Project" in projects)
        self.assertFalse("Sam Spade's Empty Project" in projects)

        # Log in as Holmes, and create another group. Add Sam to the group.
        # Sam can give the group access to his project--now Holmes has access.
        # Holmes adds Phil to the group; # now Phil has access. 
        # Phil removes Holmes from the group; Holmes no longer has access
        ## Log in as Holmes
        response = c.post('/login/?next=/slat/',
                          {'username': 'holmes', 
                           'password': 'elementary'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)

        ## Create the groups
        response = c.post('/slat/group', {'name': 'Sherlock\'s Friends'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        ## Make sure no one else is in the group:
        sherlocks_friends = Group.objects.get(name="Sherlock's Friends")
        self.assertTrue(sherlocks_friends.IsMember(self.holmes))
        self.assertFalse(sherlocks_friends.IsMember(self.samspade))
        self.assertFalse(sherlocks_friends.IsMember(self.marlowe))

        ## Add Sam to the group:
        response = c.post('/slat/group/{}/add_user'.format(sherlocks_friends.id),
                          {'userid': 'samspade'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        ## Sam gives the group permission to access his project:
        response = c.post('/login/?next=/slat/',
                          {'username': 'samspade', 
                           'password': 'maltesefalcon'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)
        
        empty_project_id = Project.objects.get(title_text="Sam Spade's Empty Project").id
        response = c.post('/slat/project/{}/add_group'.format(empty_project_id),
                          {'groupid': "Sherlock's Friends"})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        ## Log in as Holmes, and confirm Holmes has access:
        response = c.post('/login/?next=/slat/',
                          {'username': 'holmes', 
                           'password': 'elementary'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)
        
        ## Go to Sherlock's home page, and check the list of projects:
        response = c.get('/slat/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        pq = PyQuery(response.content)
        projects = []
        for child in pq('ul').children():
            if re.compile("^/slat/project/").match(child.getchildren()[0].get('href')):
                projects.append(child.text_content().strip())
        self.assertEqual(len(projects), 2)
        self.assertTrue("Sherlock's Project" in projects)
        self.assertTrue("Sam Spade's Empty Project" in projects)

        ## Go to Phil's home page, and make sure he can't see the project:
        response = c.post('/login/?next=/slat/',
                          {'username': 'marlowe', 
                           'password': 'thebigsleep'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)

        response = c.get('/slat/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        pq = PyQuery(response.content)
        projects = []
        for child in pq('ul').children():
            if re.compile("^/slat/project/").match(child.getchildren()[0].get('href')):
                projects.append(child.text_content().strip())
        self.assertFalse("Sam Spade's Empty Project" in projects)
        
        ## As Sam, add Phil to the group:
        response = c.post('/login/?next=/slat/',
                          {'username': 'samspade', 
                           'password': 'maltesefalcon'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)

        response = c.post('/slat/group/{}/add_user'.format(sherlocks_friends.id),
                          {'userid': 'marlowe'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        ## Now Phil should have access:
        response = c.post('/login/?next=/slat/',
                          {'username': 'marlowe', 
                           'password': 'thebigsleep'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponseRedirect)

        response = c.get('/slat/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        pq = PyQuery(response.content)
        projects = []
        for child in pq('ul').children():
            if re.compile("^/slat/project/").match(child.getchildren()[0].get('href')):
                projects.append(child.text_content().strip())
        self.assertTrue("Sam Spade's Empty Project" in projects)
        

        # More tests to perform:
        # - Add another group; make sure permissions don't get confused
        # - Remove user from a group
        # - Non-owner can't change permissions (i.e, someone who only has
        #   access by virtue of belonging to a group)
        # - When non-owner adds a member to a group, new member should have
        #   appropriate permissions
        # - When removing self from group, go back to your home page
        # - When removing someone else from a group, go back to the group page

        

