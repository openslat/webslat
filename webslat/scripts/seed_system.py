from django.contrib.auth.models import User
from slat.models import Profile, Project, Level, EDP, \
    EDP_Grouping, Component_Group, Group
from slat.component_models import ComponentsTab
from slat.views import make_demo, make_example_2
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.db import transaction

@transaction.atomic
def run():
    # Create a superuser:
    try:
        User.objects.get(username='slat-admin')
    except:
        new_user = User.objects.create_superuser('slat-admin',
                                            'openslat@gmail.com',
                                            'swordfish',
                                            first_name='Michael',
                                            last_name='Gauland')
        new_user.save()
        profile = Profile.objects.get(user=new_user)
        profile.organization = 'UC Quake Centre'
        profile.save()

    if settings.SINGLE_USER_MODE:
        # Create projects:
        if len(Project.objects.filter(title_text="Demo Project")) == 0:
            project = make_demo(AnonymousUser(),  "Demo Project", "A demo project")
            project.save()

            # Add a component group with a cost adjustment and comment
            roof = Level.objects.get(project=project, level=project.num_levels())
            demand_group = EDP_Grouping.objects.get(project=project, 
                                     level=roof, 
                                     type=EDP_Grouping.EDP_TYPE_ACCEL)
            component = ComponentsTab.objects.get(ident='206')
            group = Component_Group(demand=demand_group, 
                                    component=component,
                                    quantity_x=1,
                                    quantity_y=0,
                                    quantity_u=0,
                                    comment="THE Maltese Falcon",
                                    cost_adj=100)
            group.save()
        
        if len(Project.objects.filter(title_text="Red Book Project")) == 0:
            project = make_example_2(AnonymousUser(), "Red Book Project")
            project.save()
    else:
        # Create Users:
        users = [{'username': 'samspade', 
                  'email': 'samspade@spadeandarcher.com', 
                  'password': 'maltesefalcon', 
                  'first_name': 'Samuel',
                  'last_name': 'Spade',
                  'organization': 'Spade & Archer'},
                 {'username': 'miles', 
                  'email': 'milesarcher@spadeandarcher.com', 
                  'password': 'samspartner', 
                  'first_name': 'Miles',
                  'last_name': 'Archer',
                  'organization': 'Spade & Archer'},
                 {'username': 'marlowe',
                  'email': 'marlowe@marlowe.com',
                  'password': 'thebigsleep',
                  'first_name': 'Philip',
                  'last_name': 'Marlowe',
                  'organization': 'The Marlowe Agency'},
                 {'username': 'holmes',
                  'email': 'holmes@yahoo.com',
                  'password': 'elementary',
                  'first_name': 'Sherlock',
                  'last_name': 'Holmes',
                  'organization': 'Holmes and Associates'},]

        for user in users:
            try:
                User.objects.get(username=user['username'])
            except:
                new_user = User.objects.create_user(user['username'],
                                                    user['email'],
                                                    user['password'],
                                                    first_name=user['first_name'],
                                                    last_name=user['last_name'])
                new_user.save()

                profile = Profile.objects.get(user=new_user)
                profile.organization = user['organization']
                profile.save()

        for user in User.objects.all():
            print(user.username)


        # Create some demo projects
        samspade = User.objects.get(username='samspade')
        if len(Project.objects.filter(title_text="Sam Spade's Demo Project")) == 0:
            project = make_demo(samspade, 
                                "Sam Spade's Demo Project", 
                                "A demo project")
            project.save()

            # Add a component group with a cost adjustment and comment
            roof = Level.objects.get(project=project, level=project.num_levels())
            demand_group = EDP_Grouping.objects.get(project=project, 
                                     level=roof, 
                                     type=EDP_Grouping.EDP_TYPE_ACCEL)
            component = ComponentsTab.objects.get(ident='206')
            group = Component_Group(demand=demand_group, 
                                    component=component,
                                    quantity_x=1,
                                    quantity_y=0,
                                    quantity_u=0,
                                    comment="THE Maltese Falcon",
                                    cost_adj=100)
            group.save()

        if len(Project.objects.filter(title_text="Sam Spade's Other Demo Project")) == 0:
            project = make_demo(samspade, 
                                "Sam Spade's Other Demo Project",
                                "Anothe demo project")
            project.save()

        if len(Project.objects.filter(title_text="Sam Spade's Red Book Project")) == 0:
            project = make_example_2(samspade, "Sam Spade's Red Book Project")
            project.save()

        marlowe = User.objects.get(username='marlowe')
        if len(Project.objects.filter(title_text="Phil Marlowe's First Project")) == 0:
            project = make_demo(marlowe, 
                                "Phil Marlowe's First Project",
                                "A demo project")
            project.save()

        if len(Project.objects.filter(title_text="Phil Marlowe's Second Project")) == 0:
            project = make_demo(marlowe, 
                                "Phil Marlowe's Second Project",
                                "A second demo project")
            project.save()

        if len(Project.objects.filter(title_text="Sherlock's Project")) == 0:
            holmes = User.objects.get(username='holmes')
            project = make_example_2(holmes, "Sherlock's Project")
            project.title_text = "Sherlock's Project"
            project.save()

        # Create a group
        if len(Group.objects.filter(name="Spade & Archer")) == 0:
            group = Group(name="Spade & Archer")
            group.save()

            group.AddMember(samspade)

            milesarcher = User.objects.get(username='miles')
            group.AddMember(milesarcher)

            project = Project.objects.get(title_text="Sam Spade's Demo Project")
            group.GrantAccess(project)
            group.save()

        if len(Group.objects.filter(name="Everyone")) == 0:
            everyone = Group(name="Everyone")
            everyone.save()

            for user in User.objects.filter(is_staff=False):
                everyone.AddMember(user)
        
    
