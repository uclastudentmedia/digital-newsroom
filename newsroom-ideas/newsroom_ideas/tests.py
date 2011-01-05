from django.contrib.auth.models import User
from django.test import TestCase
from django.core.urlresolvers import reverse
from newsroom_ideas import models


class IdeaTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='tester', first_name='Test',
                                        last_name='Er')
        self.user.set_password('test')
        self.user.save()
        self.section = models.Section.objects.create(
            title='Test Section', slug='test'
        )

    def test_idea(self):
        """
        Test adding an idea and replying.
        """
        #TODO: should test that only logged in users can see this page

        self.client.login(username='tester', password='test')

        # Add an idea.
        url = reverse('newsroom-ideas')
        response = self.client.post(url, {'idea': 'This is my idea'})

        self.assertRedirects(response, url)
        self.assertEqual(models.Idea.objects.count(), 1)
        first_idea = models.Idea.objects.all()[0]
        self.assertEqual(first_idea.created_by, self.user)

        # Add a second idea to a section.
        ideas_url = reverse('newsroom-ideas')
        data = {'idea': 'This is my second idea', 'section': self.section.pk}
        response = self.client.post(url, data)
        self.assertRedirects(response, url)

        # Now test that the section idea counts in the right column are correct.
        response = self.client.get(url)
        self.assertContains(response, 'All ideas (2)')
        self.assertContains(response, 'Test Section (1)')

        # Add a reply to the first idea.
        url = reverse('newsroom-idea', args=[first_idea.pk])
        response = self.client.post(url, {'comment': 'Great!'})
        self.assertRedirects(response, url)
        self.assertEqual(first_idea.comment_set.count(), 1)
        first_comment = first_idea.comment_set.all()[0]
        self.assertEqual(first_comment.created_by, self.user)
