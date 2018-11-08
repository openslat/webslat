from django.test import TestCase, Client
from django.test.utils import override_settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from slat.models import *
from http import HTTPStatus
from pyquery import PyQuery
from lxml.html import HTMLParser, fromstring
import django.http
import re
import pyslat
import os
import time
from slat.tasks import ImportETABS

class NewProjectTestCase(TestCase):
    def setUp(self):
        # Direct SLAT warnings to STDOUT, so they can easily be ignored
        pyslat.SetLogFile("permissions_test_log.txt")
        pyslat.LogToStdErr(False)
        pyslat.ClearCaches()

        # Create a user:
        new_user = User.objects.create_user(username='samspade',
                                            first_name='Samuel',
                                            last_name='Spade',
                                            email='samspade@spadeandarcher.com',
                                            password='maltesefalcon')
        new_user.save()
        profile = Profile.objects.get(user=new_user)
        profile.organization = 'Spade and Archer'
        profile.save()

    def test_Demo(self):
        """Create a demo project and check the results."""
        c = Client()
        response = c.post('/login/?next=/slat/', {'username': 'samspade', 'password': 'maltesefalcon'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponse)

        # Go to the "New Project" Page

        response = c.get('/slat/project')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIsInstance(response, django.http.response.HttpResponse)
        
        response = c.post('/slat/project', {'title': 'A demo project',
                                            'description': 'A project description.',
                                            'project_type': 'DEMO'})
        
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.demo_project_id = int(re.search("[0-9]+", response.url).group())
        response = c.get(response.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        pq = PyQuery(response.content) #, encoding="utf8")
        self.assertEqual(pq('input').filter(lambda i: \
                                            pq('input')[i].name == 'title_text')\
                         [0].value, 'A demo project')
        self.assertEqual(pq('textarea').filter(lambda i: \
                                            pq('textarea')[i].name == 'description_text')\
                         [0].value, '\nA project description.')
        self.assertEqual(pq('select').filter(lambda i: \
                                            pq('select')[i].name == 'rarity')\
                         [0].value, '0.002')
        self.assertEqual(pq('input').filter(lambda i: \
                                            pq('input')[i].name == 'mean_im_collapse')\
                         [0].value, None)
        self.assertEqual(pq('input').filter(lambda i: \
                                            pq('input')[i].name == 'sd_ln_im_collapse')\
                         [0].value, None)
        self.assertEqual(pq('input').filter(lambda i: \
                                            pq('input')[i].name == 'mean_cost_collapse')\
                         [0].value, None)
        self.assertEqual(pq('input').filter(lambda i: \
                                            pq('input')[i].name == 'sd_ln_cost_collapse')\
                         [0].value, None)

        text = pq("#slat_id_mean_annual_cost").text()
        self.assertEqual(text, '(waiting)')
        #match = re.match('Mean annual cost: *([0-9]*\.[0-9][0-9]) \(ln std dev: *([0-9]+\.[0-9][0-9])\).', text)
        #self.assertTrue(match)
        #self.assertTrue(abs(float(match.groups()[0]) - 383578) < 1.0)
        #self.assertTrue(abs(float(match.groups()[1]) - 1.75) < 0.5)

        # Get the project, and check aspects of it independently of the web
        # presentation. 
        project = Project.objects.get(pk=self.demo_project_id)
        
        # Check number of levels
        self.assertEqual(project.num_levels(), 5)

        # Check Level Names
        self.assertEqual(project.levels()[0].label, "Roof")
        self.assertEqual(project.levels()[1].label, "Floor #5")
        self.assertEqual(project.levels()[2].label, "Floor #4")
        self.assertEqual(project.levels()[3].label, "Floor #3")
        self.assertEqual(project.levels()[4].label, "Floor #2")
        self.assertEqual(project.levels()[5].label, "Ground Floor")

        # IM
        self.assertEqual(project.IM.flavour, IM_Types.objects.get(name_text="NZ Standard"))
        self.assertEqual(project.IM.nzs.soil_class, 
                         NZ_Standard_Curve.SOIL_CLASS_C)
        self.assertEqual(float(project.IM.nzs.period), 2.0)
        self.assertEqual(project.IM.nzs.location,
                         Location.objects.get(location="Christchurch"))
        # Demands
        # There should be 11 demand groups (acceleration and drift for each
        # level except the ground floor, which should only have acceleration):
        self.assertEqual(len(EDP_Grouping.objects.filter(project=project)), 11)
        demand_params = [
            {'accel': {'a': 4.05, 'b': 1.5}}, # Level 0
            {'accel': {'a': 4.15, 'b': 1.5},  # Level 1
             'drift': {'a': 0.0557, 'b': 0.5}},
            { 'accel': {'a': 4.25, 'b': 1.5}, # Level 2
             'drift': {'a': 0.0633, 'b': 0.5}}, 
            {'accel': {'a': 4.10, 'b': 1.5},  # Level 3
             'drift': {'a': 0.0506, 'b': 0.5}},
            {'accel': {'a': 4.18, 'b': 1.5},  # Level 4
             'drift': {'a': 0.0380, 'b': 0.5}},
            {'accel': {'a': 5.39, 'b': 1.5},  # Level 5
             'drift': {'a': 0.0202, 'b': 0.5}}]
        
        for level in project.levels():
            g = EDP_Grouping.objects.get(project=project, level=level, type='A')
            for demand in [g.demand_x, g.demand_y]:
                self.assertEqual(demand.flavour, EDP_Flavours.objects.get(id=EDP_FLAVOUR_POWERCURVE))
                self.assertEqual(demand.powercurve.median_x_a,
                                 demand_params[level.level]["accel"]["a"])
                self.assertEqual(demand.powercurve.median_x_b,
                                 demand_params[level.level]["accel"]["b"])
                self.assertEqual(demand.powercurve.sd_ln_x_a, 1.5)
                self.assertEqual(demand.powercurve.sd_ln_x_b, 0.0)
            if level.level > 0:
                g = EDP_Grouping.objects.get(project=project, level=level, type='D')
                for demand in [g.demand_x, g.demand_y]:
                    self.assertEqual(demand.flavour, 
                                     EDP_Flavours.objects.get(id=EDP_FLAVOUR_POWERCURVE))
                self.assertEqual(demand.powercurve.median_x_a,
                                 demand_params[level.level]["drift"]["a"])
                self.assertEqual(demand.powercurve.median_x_b,
                                 demand_params[level.level]["drift"]["b"])
                self.assertEqual(demand.powercurve.sd_ln_x_a, 1.5)
                self.assertEqual(demand.powercurve.sd_ln_x_b, 0.0)

        # Components                
        self.assertEqual(len(Component_Group.objects.filter(demand__project=project)), 25)

    def test_Empty(self):
        """Create an empty project and check the results."""
        c = Client()
        response = c.post('/login/?next=/slat/', {'username': 'samspade', 'password': 'maltesefalcon'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponse)

        # Go to the "New Project" Page

        response = c.get('/slat/project')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIsInstance(response, django.http.response.HttpResponse)
        
        response = c.post('/slat/project', {'title': 'An empty project',
                                            'description': 'A different description.',
                                            'project_type': 'EMPTY',
                                            'rarity': 0.02,
                                            'levels': 3})
        
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        # Get the project id from the response URL:
        self.empty_project_id = int(re.search("[0-9]+", response.url).group())

        # Confirm we're sent to the correct page, and stop there. Later, it may
        # be a good idea to step through the whole process to create a project
        # from scratch, but for now this will do.
        self.assertEqual(response.url, "/slat/project/{}/hazard/choose".format(self.empty_project_id))
        response = c.get(response.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_ETABS(self):
        """Import an ETABS project and check the results."""
        c = Client()
        response = c.post('/login/?next=/slat/', {'username': 'samspade', 'password': 'maltesefalcon'})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIsInstance(response, django.http.response.HttpResponse)

        # Go to the "New Project" Page
        response = c.get('/slat/project')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIsInstance(response, django.http.response.HttpResponse)
        
        file = open('slat/180626_ETABS outputs.xlsx', 'rb')
        contents = file.read()
        
        path = SimpleUploadedFile(
            'slat/180626_ETABS outputs.xlsx',
            contents, 
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        response = c.post('/slat/project',
                          {'title': 'An ETABS Project',
                           'description': 'Imported from ETABS.',
                           'project_type': 'ETABS',
                           'frame_type_x': 'Moment',
                           'frame_type_y': 'Moment',
                           'return_period': 50,
                           'strength': 4.0,
                           'path' : path,
                           'soil_class': NZ_Standard_Curve.SOIL_CLASS_C,
                           'location': Location.objects.get(location="Christchurch")
                          })
                                            
        self.assertEqual(response.status_code, HTTPStatus.FOUND)



        # Get the project id from the response URL:
        self.empty_project_id = int(re.search("[0-9]+", response.url).group())

        # Confirm we're sent to the correct page:
        self.assertTrue(re.match("/slat/etabs_confirm/[0-9]+", response.url))
        confirm_url = response.url
        response = c.get(confirm_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Parse the contents:
        # We do it this convoluted way to get the Unicode characters 
        # correct, due to a quirk (bug?) in PyQuery:
        UTF8_PARSER = HTMLParser(encoding='utf-8')
        pq = PyQuery(fromstring(response.content, parser=UTF8_PARSER))

        # Check the summary table at the top:
        t = pq('table')[0]
        self.assertEqual(len(t), 8)

        summary_data = [["Title", "An ETABS Project"],
                        ["Description:", "Imported from ETABS."],
                        ["Path:", "180626_ETABS outputs.xlsx"],
                        ["Location:", "Christchurch"],
                        ["Soil Class:", "C"],
                        ["Return Period:", "50"],
                        ["Frame Type X:", "Moment"],
                        ["Frame Type Y:", "Moment"]]
        for i in range(len(t)):
            r = t[i]
            self.assertEqual(r[0].text_content().strip(), summary_data[i][0])
            self.assertEqual(r[1].text_content().strip(), summary_data[i][1])
        
        # Check the Period section:
        self.assertEqual(pq('p')[0].text_content().strip(), "Period Units: sec")
        
        period_choices = [ "2.365", "2.051", "1.543",
                              "0.76", "0.665", "0.502",
                              "0.426", "0.378", "0.288",
                              "0.281", "0.254", "0.2",
                              "Manual"]
        x_period_labels = ["0.812", "0.000", "0.000",
                           "0.099", "0.000", "0.000",
                           "0.038", "0.000", "0.000",
                           "0.021", "0.000", "0.013",
                           "Manual X Period"]
        y_period_labels = ["0.000", "0.819", "0.000",
                           "0.000", "0.097", "0.000",
                           "0.000", "0.037", "0.000",
                           "0.000", "0.020", "0.000",
                           "Manual Y Period"]
        i = 0
        while pq("#id_Tx_{}".format(i)):
            self.assertEqual(pq("#id_Tx_{}".format(i)).val(), period_choices[i])
            l = pq('label').filter(lambda n, this: this.attrib['for'] == "id_Tx_{}".format(i))[0]
            self.assertEqual(l.text_content().strip(), x_period_labels[i])

            self.assertEqual(pq("#id_Ty_{}".format(i)).val(), period_choices[i])
            l = pq('label').filter(lambda n, this: this.attrib['for'] == "id_Ty_{}".format(i))[0]
            self.assertEqual(l.text_content().strip(), y_period_labels[i])
            i = i + 1
        self.assertEqual(i, 13)
        
        # Check the height section:
        self.assertEqual(pq('p')[1].text_content().strip(), "Height Unit: m")
        height_data = [
            ["Story", "Height"],
            ["Story1", "4"],
            ["Story2", "7.6"],
            ["Story3", "11.2"],
            ["Story4", "14.8"],
            ["Story5", "18.4"],
            ["Story6", "22"],
            ["Story7", "25.6"],
            ["Story8", "29.2"],
            ["Story9", "32.8"],
            ["Story10", "36.4"]]
        
        t = pq('table')[3]
        self.assertEqual(len(t), 11)
        for i in range(len(t)):
            r = t[i]
            self.assertEqual(r[0].text_content().strip(), height_data[i][0])
            self.assertEqual(r[1].text_content().strip(), height_data[i][1])
            
            
        # Check the Story Drift choices:
        drift_choices = [ "Dead", 
                          "ES EQX", "ES EQY",
                          "Live", "Live (ROOF)",
                          "MRS EQX mu=4 Max",
                          "MRS EQY mu=4 Max",
                          "Modal 1", "Modal 10", "Modal 11",
                          "Modal 12", "Modal 2", "Modal 3",
                          "Modal 4", "Modal 5", "Modal 6",
                          "Modal 7", "Modal 8", "Modal 9",
                          "SDL"
        ]
        s = pq("#id_x_drift_case")[0]
        self.assertEqual(len(drift_choices), len(s.getchildren()))
        for i in range(len(s.getchildren())):
            child = s.getchildren()[i]
            self.assertEqual(child.attrib['value'], drift_choices[i])
        s = pq("#id_y_drift_case")[0]
        self.assertEqual(len(drift_choices), len(s.getchildren()))
        for i in range(len(s.getchildren())):
            child = s.getchildren()[i]
            self.assertEqual(child.attrib['value'], drift_choices[i])

        # Check the accelleration choices:
        self.assertEqual(pq('p')[4].text_content().strip(), "X: mm/sec²")
        self.assertEqual(pq('p')[5].text_content().strip(), "Y: mm/sec²")
        
        accel_choices = [ "MRS EQX mu=4 Max",
                          "MRS EQY mu=4 Max"]
        s = pq("#id_x_accel_case")[0]
        self.assertEqual(len(accel_choices), len(s.getchildren()))
        for i in range(len(s.getchildren())):
            child = s.getchildren()[i]
            self.assertEqual(child.attrib['value'], accel_choices[i])
        s = pq("#id_y_accel_case")[0]
        self.assertEqual(len(accel_choices), len(s.getchildren()))
        for i in range(len(s.getchildren())):
            child = s.getchildren()[i]
            self.assertEqual(child.attrib['value'], accel_choices[i])

        response = c.post(confirm_url,
                          {'y_drift_case': 'ES EQY',
                           'x_accel_case': 'MRS EQX mu=4 Max',
                           'Ty': '2.051',
                           'x_drift_case': 'ES EQX',
                           'Tx': '2.365',
                           'y_accel_case': 'MRS EQY mu=4 Max',
                           'Period': 'TX'})
        self.assertTrue(re.match("/slat/etabs_progress\?job=", response.url))

        project = Project.objects.get(pk=1)
        self.assertEqual(len(EDP_Grouping.objects.filter(project=project)), 21)
