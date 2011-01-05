from django.db import models


class AssignmentManager(models.Manager):
    use_for_related_fields = True

    def assignments(self):
        return self.get_query_set().filter(confirmed=True)

    def requests(self):
        return self.get_query_set().filter(confirmed=False)
