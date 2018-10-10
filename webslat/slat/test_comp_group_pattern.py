import sys
import pyslat
from django.contrib.auth.models import User
from slat.models import Project, Component_Group_Pattern, Component_Group
from django.test import TestCase, Client
from slat.views import make_demo

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
        self.assertTrue(round(project.model().AnnualCost().mean()) == 381286)


        pattern = Component_Group_Pattern.objects.get(pk=1)
        groups = Component_Group.objects.filter(pattern=pattern)

        pattern.ChangePattern(pattern.component,
                              pattern.quantity_x,
                              pattern.quantity_y,
                              0, 
                              pattern.cost_adj,
                              pattern.comment)
        self.assertTrue(round(project.model().AnnualCost().mean()) == 378084)

        pattern.ChangePattern(pattern.component,
                              pattern.quantity_x,
                              9,
                              pattern.quantity_u,
                              pattern.cost_adj,
                              pattern.comment)
        self.assertTrue(round(project.model().AnnualCost().mean()) == 382566)

        pattern.ChangePattern(pattern.component,
                              4,
                              pattern.quantity_y,
                              pattern.quantity_u, 
                              pattern.cost_adj,
                              pattern.comment)
        self.assertTrue(round(project.model().AnnualCost().mean()) == 384487)
        
