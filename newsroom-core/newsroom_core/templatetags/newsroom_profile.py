from django import template
from django.utils.safestring import mark_safe
from newsroom_core.utils.profile import get_profile


register = template.Library()


class ProfileNode(template.Node):
    def __init__(self, user_var, context_name):
        self.user_var = user_var
        self.context_name = context_name

    def render(self, context):
        user = self.user_var.resolve(context)
        context[self.context_name] = get_profile(user)
        return ''


@register.tag('get_profile')
def do_get_profile(parser, token):
    bits = token.split_contents()
    if len(bits) != 4 or bits[2] != 'as':
        raise template.TemplateSyntaxError('Expected format {%% %s user_var as '
                                           'context_name %%}' % bits[0])
    user_var = parser.compile_filter(bits[1])
    context_name = bits[3]
    return ProfileNode(user_var=user_var, context_name=context_name)


@register.inclusion_tag('newsroom/tags/profile.html')
def profile(user):
    """
    Return the common HTML output for a user, showing their name and a link
    to their profile.
    """
    return {'profile': get_profile(user)}