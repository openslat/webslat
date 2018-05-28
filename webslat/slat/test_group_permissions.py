import pyslat
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
