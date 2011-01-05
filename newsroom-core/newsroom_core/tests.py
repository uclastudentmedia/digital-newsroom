from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.datastructures import MultiValueDict
from newsroom_core import models
from newsroom_core.utils.profile import get_profile


class BaseTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='tester', first_name='Test',
                                        last_name='Er', email='test@test.com')
        self.user.set_password('pw')
        self.user.save()
        self.user2 = User.objects.create(username='tester2', first_name='Test2',
                                        last_name='Er!', email='test2@test.com')
        self.superuser = User.objects.create(username='superuser',
                                        first_name='Super', last_name='User',
                                        email='super@test.com')
        self.superuser.set_password('pw')
        self.superuser.save()
        self.section = models.Section.objects.create(
            title='Test', slug='test'
        )
        self.category = models.Category.objects.create(
            title='Story', slug='story', top_category=True
        )
        self.status_open = models.Status.objects.create(
            order=1, slug='open', title='Open', means_completed=False
        )
        self.status_closed = models.Status.objects.create(
            order=2, slug='closed', title='Closed', means_completed=True
        )
        for user in [self.user, self.user2, self.superuser]:
            models.NewsroomProfile.objects.create(user=user,
                                                  section=self.section)
        self.client.login(username='tester', password='pw')

    def create_assignment(self, title, user=None, section=None, category=None,
                          status=None):
        user = user or self.user
        assignment = models.Assignment.objects.create(
            section=section or self.section,
            category=category or self.category,
            responsible=user, created_by=user,
            title='Test Article',
            status=status or self.status_open,
            confirmed=True,
        )
        assignment.involved.add(user)
        return assignment


class DynamicFieldTest(BaseTest):
    def setUp(self):
        super(DynamicFieldTest, self).setUp()
        f = models.CategoryTextField.objects.create(
            category=self.category, name='Field 2', required=False, length=10,
            order=2
        )
        f = models.CategoryTextField.objects.create(
            category=self.category, name='Field 1', required=True, length=10,
            order=1
        )
        f = models.CategoryChoiceField.objects.create(
            category=self.category, name='Field 3', required=True, order=3
        )
        f.choices.create(option='choice3')
        f.choices.create(option='choice1')
        f.choices.create(option='choice2')
        f = models.CategoryBigTextField.objects.create(
            category=self.category, name='Body', required=True,
            is_property=False
        )

    def test_category(self):
        detail_names = [f.name for f in self.category.details]
        self.assertEqual(detail_names, ['Body'])
        property_names = [f.name for f in self.category.properties]
        self.assertEqual(property_names, ['Field 1', 'Field 2', 'Field 3'])
        choices = self.category.properties[2].choices.values_list('option',
                                                                  flat=True)
        self.assertEqual(list(choices), ['choice1', 'choice2', 'choice3'])

    def test_assignment(self):
        assignment = self.create_assignment(title='Test Article')

        # Set some initial dynamic values for assignment
        self.category.field_set.get(name='Body').field.values.create(
            assignment=assignment, value='b',
        )
        self.category.field_set.get(name='Field 1').field.values.create(
            assignment=assignment, value='1',
        )
        f = self.category.field_set.get(name='Field 3').field
        f.values.create(
            assignment=assignment, value=f.choices.all()[0],
        )

        # Now test values
        details = [(f.name, unicode(v)) for f, v in assignment.details]
        self.assertEqual(details, [(u'Body', u'b')])

        properties = [(f.name, unicode(v)) for f, v in assignment.properties]
        expected = [(u'Field 1', u'1'), (u'Field 3', u'choice1')]
        self.assertEqual(properties, expected)
        self.category.field_set.get(name='Field 2').field.values.create(
            assignment=assignment, value='2',
        )
        assignment.clear_values_cache()
        properties = [(f.name, unicode(v)) for f, v in assignment.properties]
        expected = [(u'Field 1', u'1'), (u'Field 2', u'2'),
                    (u'Field 3', u'choice1')]
        self.assertEqual(properties, expected)


class AssignmentsTest(BaseTest):
    def test_create(self):
        url = reverse('newsroom-add-assignment', args=[self.category.slug])
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'newsroom/add_assignment.html')

        data = {'title': 'Test', 'section': '1', 'status': '1',
                'responsible': self.user.pk}
        response = self.client.post(url, data)
        self.assertEqual(models.Assignment.objects.assignments().count(), 1)
        url = models.Assignment.objects.assignments().all()[0].get_absolute_url()
        self.assertRedirects(response, url)

    def test_assignment_emails(self):
        add_url = reverse('newsroom-add-assignment', args=[self.category.slug])

        # Creating assignment doesn't send email to self.
        data = {'title': 'Test', 'section': '1', 'status': '1',
                'responsible': self.user.pk, 'involved': [self.user.pk]}
        response = self.client.post(add_url, data)
        self.assertEqual(len(mail.outbox), 0)

        # Creating assignment sends emails to everyone else involved.
        data = {
            'title': 'Test 2', 'section': '1', 'status': '1',
            'responsible': self.user.pk,
            'involved': [self.user2.pk, self.superuser.pk]
        }
        response = self.client.post(add_url, data)
        self.assertEqual(len(mail.outbox), 2)

        # Commenting on an assignment sends notification to everyone else
        # involved.
        assignment = models.Assignment.objects.assignments().get(title='Test 2')
        data = {'comment': "Here's a comment"}
        mail.outbox = []
        response = self.client.post(assignment.get_absolute_url(), data)
        self.assertEqual(len(mail.outbox), 2)

        # Updating status history sends notification to others involved.
        status_url = reverse('newsroom-assignment-change-status')
        data = {'assignment_id': assignment.pk, 'change_status': 'closed'}
        mail.outbox = []
        response = self.client.post(status_url, data)
        self.assertEqual(len(mail.outbox), 2)

    def test_tab_assignments_count(self):
        tab_text = 'Assignments <span class="number"><span>(</span>%s<span>)'\
                   '</span></span>'
        profile = get_profile(self.user)
        profile.section = self.section
        profile.my_assignments_default = True
        profile.save()
        a1 = self.create_assignment('Article one')
        a2 = self.create_assignment('Article two')
        a3 = self.create_assignment('Article three', user=self.superuser)
        url = reverse('newsroom-add-assignment', args=[self.category.slug])

        response = self.client.get(url)
        self.assertContains(response, tab_text % '2')

        a1.status = self.status_closed
        a1.save()
        response = self.client.get(url)
        self.assertContains(response, tab_text % '1')
