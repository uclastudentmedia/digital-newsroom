import re
from django import template
from django.http import HttpRequest
from django.utils.html import escape
from newsroom_core.utils.profile import get_profile
from newsroom_core.utils.template import parse_token


register = template.Library()


class TruncateNode(template.Node):
    def __init__(self, list_name, length_var, output_name=None, more_name=None):
        self.list_name, self.length_var = list_name, length_var
        self.output_name = output_name or list_name
        self.more_name = more_name or 'more'
        super(TruncateNode, self).__init__()

    def render(self, context):
        list_ = template.Variable(self.list_name).resolve(context)
        if not list_:
            self.set_context(context, list_)
            return ''
        length = self.length_var.resolve(context)
        try:
            length = int(length)
        except (TypeError, ValueError):
            self.set_context(context, list_)
            return ''
        short_list = list(list_[:length + 1])
        self.set_context(context, short_list[:length], len(short_list) > length)
        return ''

    def set_context(self, context, list_, more=False):
        context[self.output_name] = list_
        context[self.more_name] = more


class QueryStringNode(template.Node):
    def __init__(self, delete, update):
        self.delete, self.update = delete, update

    def render(self, context):
        try:
            querystring = self.get_querystring(context)
        except KeyError:
            return ''
        url = querystring.urlencode()
        if url:
            url = '?%s' % url
        else:
            url = '.'
        return escape(url)

    def get_querystring(self, context):
        request = context['request']
        if not isinstance(request, HttpRequest):
            raise KeyError('"request" key existed but was not an HttpRequest')
        querystring = request.GET.copy()
        for item in self.delete:
            if item in querystring:
                del querystring[item]
        for key, value in self.update.items():
            if isinstance(value, (template.FilterExpression,
                                  template.Variable)):
                value = value.resolve(context)
            querystring[key] = value
        return querystring


class FormQueryStringNode(QueryStringNode):
    def render(self, context):
        try:
            querystring = self.get_querystring(context)
        except KeyError:
            return ''
        output = []
        for key, value in querystring.items():
            output.append('<input type="hidden" name="%s" value="%s" />' %
                          (key, value))
        return '\n'.join(output)


@register.tag
def truncate_list(parser, token):
    """
    Truncates a list to ``count`` items and sets a ``more`` variable as to
    whether there are still more items in the list.

    Optionally, you can output the preserve the original context variable name
    by providing an alternate output variable name.

    For example (showing the optional "as output_var"):

        {% truncate_list long_list 5 as short_list %}
        {% for item in short_list %}...{% endfor %}
        {% if more %}<a href="...">more</a>{% endif %}
    """
    bits = token.split_contents()
    if len(bits) != 3 and (len(bits) != 5 or bits[2] != 'as'):
        raise template.TemplateSyntaxError(
            'expected {%% %s [list] [length] %%} or '
            '{%% %s [list] [length] as [output_var] %%}' % (bits[0], bits[0]))
    length_var = parser.compile_filter(bits[2])
    if len(bits) == 5:
        output_name = bits[4]
    else:
        output_name = None
    return TruncateNode(list_name=bits[1], length_var=length_var,
                        output_name=output_name)


@register.tag
def querystring(parser, token):
    """
    An easy way for bits of the query string to be added/modified or popped
    in a template.
    """
    tag_name, args, kwargs = parse_token(token, parser, compile_args=False)
    return QueryStringNode(delete=args, update=kwargs)


@register.tag
def form_querystring(parser, token):
    """
    Output hidden input tags based on the current query string (adding and
    modifying like the querystring tag does).
    """
    tag_name, args, kwargs = parse_token(token, parser, compile_args=False)
    return FormQueryStringNode(delete=args, update=kwargs)
