import os
from django.contrib.auth.models import User
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings
from newsroom_files import models


class FileTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='tester', first_name='Test',
                                        last_name='Er')
        self.user.set_password('test')
        self.user.save()
        self.section = models.Section.objects.create(
            title='Test Section', slug='test'
        )
        self.section2 = models.Section.objects.create(
            title='Test Section 2', slug='test2'
        )
        self.files = []

    def tearDown(self):
        # Remove any test files.
        while self.files:
            file = self.files.pop()
            try:
                os.remove(file)
            except:
                pass

    def create_test_file(self, filename, content, section):
        """
        Create a test file ready for uploading. Returns the file opened for
        reading.

        Both the original file and the expected upload file are queued for
        deletion at the end of the test.
        """
        filename = 'newsroom_filetest_%s' % filename
        path = os.path.abspath(filename)
        test_file = open(path, 'w')
        test_file.write(content)
        test_file.close()
        self.files.append(path)
        upload_filename = os.path.join(
            models.File(file=filename, section=section).file.path
        )
        self.files.append(upload_filename)
        return open(path)

    def test_add_file(self):
        self.client.login(username='tester', password='test')
        upload_url = reverse('newsroom-file-upload')
        list_url = reverse('newsroom-files')

        # Add a file.
        f = self.create_test_file('test1.txt', content='some test text',
                                  section=self.section)
        data = {'section': self.section.pk, 'description': 'test 1', 'file': f}
        response = self.client.post(upload_url, data)

        self.assertRedirects(response, list_url)
        self.assertEqual(models.File.objects.count(), 1)
        file1 = models.File.objects.get(pk=1)
        self.assertEqual(file1.created_by, self.user)
        self.assertEqual(file1.file_size, 14)

        # Add a second file.
        f = self.create_test_file('test2.txt', content='short',
                                  section=self.section2)
        data = {'section': self.section2.pk, 'description': 'test 1', 'file': f}
        response = self.client.post(upload_url, data)

        self.assertRedirects(response, list_url)
        self.assertEqual(models.File.objects.count(), 2)
        file2 = models.File.objects.get(pk=2)
        self.assertEqual(file2.file_size, 5)

        # Check the default ordering shows the latest file first by default.
        self.assertEqual(models.File.objects.all()[0], file2)

        # Upload a new file over the first.
        replace_url = reverse('newsroom-file-replace', args=[file1.pk])
        f = self.create_test_file('test1-new.txt', content='shrt',
                                  section=self.section)
        data = {'section': self.section.pk, 'description': 'test 1', 'file': f}
        response = self.client.post(replace_url, data)
        file1 = models.File.objects.get(pk=1)
        self.assertEqual(file1.file_size, 4)

        # Check that the section counts in the right column are correct.
        response = self.client.get(list_url)
        self.assertContains(response, 'All files (2)')
        self.assertContains(response, 'Test Section (1)')
        self.assertContains(response, 'Test Section 2 (1)')

        # Delete a file.
        delete_url = reverse('newsroom-file-delete', args=[file2.pk])
        response = self.client.post(delete_url)
        self.assertRedirects(response, list_url)
        response = self.client.get(list_url)
        self.assertContains(response, 'All files (1)')
