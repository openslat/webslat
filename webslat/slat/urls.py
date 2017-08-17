from django.conf.urls import url

from . import views
from . import component_views

app_name = 'slat'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^project/(?P<project_id>[0-9]+)$', views.project, name='project'),
    url(r'^project$', views.project, name='project'),
    url(r'^components$', component_views.components, name='components'),
    url(r'^components/(?P<component_id>[0-9]+)$', component_views.component, name='component'),
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
]
