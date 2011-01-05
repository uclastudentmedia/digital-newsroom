import re

from django.core.mail import EmailMessage
from django.template import Context
from django.template.loader import find_template_source, get_template_from_string
from django.contrib.sites.models import Site

RE_SUBJECT = re.compile(r'SUBJECT:\s*(.+)')


def send_mail_from_template(to, template_name, context=None, fail_silently=True):
    if not to:
        return
    # Build the context
    context = context or {}
    context['site'] = Site.objects.get_current()
    context = Context(context, autoescape=False)
    # Get the text email body
    source, origin = find_template_source('newsroom/emails/%s.txt' % template_name)
    template = get_template_from_string(source, origin, template_name)
    body = template.render(context)
    # Get the subject line
    match = RE_SUBJECT.search(source)
    if not match:
        raise ValueError('The email source did not contain a "SUBJECT:" line')
    subject_source = match.group(1)
    template = get_template_from_string(subject_source, origin, template_name)
    subject = template.render(context)
    # Fire off the email
    if isinstance(to, basestring):
        to = [to]
    msg = EmailMessage(subject, body, to=to)
    msg.send(fail_silently=fail_silently)
