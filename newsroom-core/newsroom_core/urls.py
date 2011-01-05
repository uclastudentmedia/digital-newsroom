from django.conf.urls.defaults import *
from newsroom_core.apps import build_tabs


# Build the newsroom tabs.
build_tabs()


urlpatterns = patterns('newsroom_core.views',
    url(r'^$', 'core.initial', name='newsroom-home'),

    url(r'^assignments/$', 'assignments.listing', name='newsroom-assignments'),
    url(r'^assignments/(\d{4})/(\d{2})/(\d{2})/$', 'assignments.listing_day',
        name='newsroom-assignments-day'),
    url(r'^assignments/(\d{4})/(\d{2})/(\d{2})/compiled/$',
        'assignments.compiled', name='newsroom-assignments-day-compiled'),
    url(r'^assignments/for/([\w-]+)/$', 'assignments.assignments_involved',
        name='newsroom-assignments-profile'),
    url(r'^assignments/add/([\w-]+)/$', 'assignments.add_assignment',
        name='newsroom-add-assignment'),
    url(r'^assignments/(?P<slug>[\w-]+)/$', 'assignments.assignment_detail',
        name='newsroom-assignment'),
    url(r'^assignments/(?P<slug>[\w-]+)/(?:(?P<child_id>\d+)/)?$',
        'assignments.assignment_detail', name='newsroom-assignment'),
    url(r'^assignments/(?P<slug>[\w-]+)/(?:(?P<child_id>\d+)/)?edit/$',
        'assignments.edit_assignment', name='newsroom-assignment-edit'),
    url(r'^assignments/change/status/$', 'assignments.change_status',
        name='newsroom-assignment-change-status'),

    url(r'^requests/$', 'requests.listing', name='newsroom-requests'),
    url(r'^requests/add/(?P<category_slug>[\w-]+)/$', 'requests.add_request',
        name='newsroom-add-request'),
    url(r'^assignments/(?P<assignment_slug>[\w-]+)/add-request/'\
                                                '(?P<category_slug>[\w-]+)/$',
        'requests.add_request_to_assignment',
        name='newsroom-assignment-add-request'),
    url(r'^requests/(?P<slug>[\w-]+)/(?P<child_id>\d+)/edit/$',
        'assignments.edit_assignment', {'is_request': True},
        name='newsroom-request-edit'),
    url(r'^requests/(?P<slug>[\w-]+)/(?P<child_id>\d+)/accept/$',
        'requests.accept', name='newsroom-request-accept'),

    url(r'^people/$', 'people.listing', name='newsroom-people'),
    url(r'^people/edit-profile/$', 'people.edit_profile',
        name='newsroom-edit-profile'),
    url(r'^people/([\w-]+)/$', 'people.listing',
        name='newsroom-people-section'),
    url(r'^profile/([\w-]+)/$', 'people.detail', name='newsroom-person'),
    url(r'^profile/([\w-]+)/edit/$', 'people.edit_profile',
        name='newsroom-edit-profile'),

    url(r'^login/$', 'core.login', name='newsroom-login'),
)

urlpatterns += patterns('django.contrib.auth.views',
    url(r'^logout/$', 'logout',
        {'template_name': 'newsroom/registration/logged_out.html'},
        name='newsroom-logout'),
    (r'^password_change/$', 'password_change',
     {'template_name': 'newsroom/registration/password_change_form.html'}),
    (r'^password_change/done/$', 'password_change_done',
     {'template_name': 'newsroom/registration/password_change_done.html'}),
    (r'^password_reset/$', 'password_reset',
     {'template_name': 'newsroom/registration/password_reset_form.html',
      'email_template_name':
      'newsroom/registration/password_reset_email.html'}),
    (r'^password_reset/sent/$', 'password_reset_done',
     {'template_name': 'newsroom/registration/password_reset_done.html'}),
    (r'^password_reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
     'password_reset_confirm',
     {'template_name': 'newsroom/registration/password_reset_confirm.html'}),
    (r'^password_reset/done/$', 'password_reset_complete',
     {'template_name': 'newsroom/registration/password_reset_complete.html'}),
)