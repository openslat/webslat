import sys
import pyslat
from django.contrib.auth.models import User
from slat.models import Project, Component_Group_Pattern, Component_Group
from django.test import TestCase, Client
from slat.views import make_demo
from slat.component_models import *

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

class GroupTestCase(TestCase):
    samspade=None

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
        
        self.samspade = User.objects.get(username='samspade')
        make_demo(self.samspade,
                  "Sam Spade's Demo Project",
                  "This is Sam's demo project.").save()
        

    def test_change_count(self):
        """Change the count for a pattern, and make sure the costs are re-calculated."""

        project = Project.objects.get(pk=1)
        self.assertEqual(round(project.model().AnnualCost().mean()), 383578)


        pattern = Component_Group_Pattern.objects.get(pk=1)
        groups = Component_Group.objects.filter(pattern=pattern)
        pattern.ChangePattern(pattern.component,
                              pattern.quantity_x,
                              pattern.quantity_y,
                              1, 
                              pattern.cost_adj,
                              pattern.comment)
        self.assertEqual(round(project.model().AnnualCost().mean()), 384818)

        pattern.ChangePattern(pattern.component,
                              pattern.quantity_x,
                              9,
                              pattern.quantity_u,
                              pattern.cost_adj,
                              pattern.comment)
        self.assertEqual(round(project.model().AnnualCost().mean()), 392254)
        return

        pattern.ChangePattern(pattern.component,
                              4,
                              pattern.quantity_y,
                              pattern.quantity_u, 
                              pattern.cost_adj,
                              pattern.comment)
        self.assertEqual(round(project.model().AnnualCost().mean()), 389775)

        pattern.ChangePattern(pattern.component,
                              pattern.quantity_x,
                              pattern.quantity_y,
                              pattern.quantity_u, 
                              pattern.cost_adj,
                              "Comment changed for testing.")
        self.assertEqual(round(project.model().AnnualCost().mean()), 389775)

        pattern.ChangePattern(pattern.component,
                              pattern.quantity_x,
                              pattern.quantity_y,
                              pattern.quantity_u, 
                              pattern.cost_adj * 3.5,
                              pattern.comment)
        self.assertEqual(round(project.model().AnnualCost().mean()), 433154)

        pattern.ChangePattern(ComponentsTab.objects.get(ident='208'),
                              pattern.quantity_x,
                              pattern.quantity_y,
                              pattern.quantity_u, 
                              pattern.cost_adj,
                              pattern.comment)
        self.assertEqual(round(project.model().AnnualCost().mean()), 373744)
