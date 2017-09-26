from django.conf.urls import url

from . import views
from . import component_views

app_name = 'slat'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^project/(?P<project_id>[0-9]+)$', views.project, name='project'),
    url(r'^project$', views.project, name='project'),
    url(r'^components$', component_views.components, name='components'),
    url(r'^components/(?P<component_id>[A-Za-z0-9.]+)$', component_views.component, name='component'),
    url(r'^project/(?P<project_id>[0-9]+)/hazard$', views.hazard, name='hazard'),
    url(r'^project/(?P<project_id>[0-9]+)/hazard/choose$', views.hazard_choose, name='hazard_choose'),
    url(r'^project/(?P<project_id>[0-9]+)/hazard/nlh$', views.nlh, name='nlh'),
    url(r'^project/(?P<project_id>[0-9]+)/hazard/nlh/edit$', views.nlh_edit, name='nlh_edit'),
    url(r'^project/(?P<project_id>[0-9]+)/hazard/interp$', views.im_interp, name='im_interp'),
    url(r'^project/(?P<project_id>[0-9]+)/hazard/interp/edit$', views.im_interp_edit, name='im_interp_edit'),
    url(r'^project/(?P<project_id>[0-9]+)/hazard/interp/import$', views.im_file, name='im_file'),
    url(r'^project/(?P<project_id>[0-9]+)/hazard/nzs$', views.im_nzs, name='nzs'),
    url(r'^project/(?P<project_id>[0-9]+)/hazard/nzs/edit$', views.im_nzs_edit, name='im_nzs_edit'),
    url(r'^project/(?P<project_id>[0-9]+)/edp$', views.edp, name='edp'),
    url(r'^project/(?P<project_id>[0-9]+)/edp/(?P<edp_id>[0-9]+)$', views.edp_view, name='edp_view'),
    url(r'^project/(?P<project_id>[0-9]+)/edp/init$', views.edp_init, name='edp_init'),
    url(r'^project/(?P<project_id>[0-9]+)/edp/(?P<edp_id>[0-9]+)/choose$', views.edp_choose, name='edp_choose'),
    url(r'^project/(?P<project_id>[0-9]+)/edp/(?P<edp_id>[0-9]+)/power$', views.edp_power, name='edp_power'),
    url(r'^project/(?P<project_id>[0-9]+)/edp/(?P<edp_id>[0-9]+)/power/edit$', views.edp_power_edit, name='edp_power_edit'),
    url(r'^project/(?P<project_id>[0-9]+)/edp/(?P<edp_id>[0-9]+)/userdef$', views.edp_userdef, name='edp_userdef'),
    url(r'^project/(?P<project_id>[0-9]+)/edp/(?P<edp_id>[0-9]+)/userdef/edit$', views.edp_userdef_edit, name='edp_userdef_edit'),
    url(r'^project/(?P<project_id>[0-9]+)/edp/(?P<edp_id>[0-9]+)/userdef/import$', views.edp_userdef_import, name='edp_userdef_import'),
    url(r'^project/(?P<project_id>[0-9]+)/edp/(?P<edp_id>[0-9]+)/cgroups$', views.edp_cgroups, name='edp_cgroups'),
    url(r'^project/(?P<project_id>[0-9]+)/edp/(?P<edp_id>[0-9]+)/cgroup$', views.edp_cgroup, name='edp_cgroup'),
    url(r'^project/(?P<project_id>[0-9]+)/edp/(?P<edp_id>[0-9]+)/cgroup/(?P<cg_id>[0-9]+)$', views.edp_cgroup, name='edp_cgroup'),
    url(r'^project/(?P<project_id>[0-9]+)/cgroups$', views.cgroups, name='compgroups'),
    url(r'^project/(?P<project_id>[0-9]+)/floor/(?P<floor_num>[0-9]+)/cgroup$', views.floor_cgroup, name='floor_compgroup'),
    url(r'^project/(?P<project_id>[0-9]+)/floor/(?P<floor_num>[0-9]+)/cgroup/(?P<cg_id>[0-9]+)$', views.floor_cgroup, name='floor_compgroup'),
    url(r'^project/(?P<project_id>[0-9]+)/cgroup$', views.cgroup, name='compgroup'),
    url(r'^project/(?P<project_id>[0-9]+)/cgroup/(?P<cg_id>[0-9]+)$', views.cgroup, name='compgroup'),
    url(r'^project/(?P<project_id>[0-9]+)/analysis$', views.analysis, name='analysis'),
    url(r'^project/(?P<project_id>[0-9]+)/floor/(?P<floor_num>[0-9]+)/cgroups$', views.floor_cgroups, name='floor_cgroups'),
    url(r'^project/(?P<project_id>[0-9]+)/floor$', views.floors, name='floors'),
    url(r'^project/(?P<project_id>[0-9]+)/floor/(?P<floor_num>[0-9]+)/(?P<type>(acceleration)|(drift))$', views.demand, name='demand'),
    url(r'^component-autocomplete/$', views.ComponentAutocomplete.as_view(), name='component-autocomplete'),
]
