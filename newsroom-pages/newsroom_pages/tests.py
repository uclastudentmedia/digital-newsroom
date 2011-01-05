from django.contrib.auth.models import User
from django.test import TestCase
from django.core.urlresolvers import reverse
from newsroom_core import models as core_models
from newsroom_pages import models


class PageTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='tester', first_name='Test',
                                        last_name='Er')
        self.user.set_password('test')
        self.user.save()
        self.editor = User.objects.create(username='editor', first_name='Edit',
                                          last_name='Or')
        self.editor.set_password('test')
        self.editor.save()
        s = core_models.Section.objects.create(title='Section', slug='section')
        core_models.NewsroomProfile.objects.create(user=self.editor,
                                                   is_editor=True,
                                                   section=s)

    def test_page(self):
        """
        Test adding a page.
        """
        add_url = reverse('newsroom-page-add')
        login_url = reverse('newsroom-login')

        # Normal users can't access
        self.client.login(username='tester', password='test')
        response = self.client.get(add_url)
        self.assertRedirects(response, '%s?next=%s' % (login_url, add_url))

        # But editors can
        self.client.login(username='editor', password='test')
        response = self.client.get(add_url)
        self.assertTemplateUsed(response, 'newsroom/pages/edit.html')

        slug = 'idea'
        response = self.client.post(add_url, {
            'title': 'This is my idea', 'slug': slug, 'summary': 'Summary',
            'content': 'This is the content of the page'})
        list_url = reverse('newsroom-page', args=[slug])

        self.assertRedirects(response, list_url)
        self.assertEqual(models.Page.objects.count(), 1)
