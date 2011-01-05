import re


var_bit = r'''(?:[\w.]+|"[^"\\]*(?:\\.[^"\\]*)*"|'[^'\\]*(?:\\.[^'\\]*)*')'''
re_kwargs = re.compile(r'(?:(\w+)\s*=\s*)?(%(var)s(?:\|%(var)s(?::%(var)s)?)?)'
                       % {'var': var_bit})


def parse_token(token, parser, compile_args=True, compile_kwargs=True,
                leave_args=None):
    """
    Returns a tuple containing the tag name, a list of args and a dictionary of
    keyword args parsed from the token contents.

    Usually, args and kwargs are compiled as FilterExpressions but this can be
    turned off by passing ``compile_args=False`` and/or
    ``compile_kwargs=False``.

    Alternately, if there are only specific arguments which should be left as
    strings, set ``leave_args`` to a list of 0-based integers for arguments that
    should be left alone. For example, if you wanted '{% mytag as [var] %}'::

        tag_name, args, kwargs = parse_token(token, parser, leave_args=[0])
        if kwargs or len(args) < 3 or args[0] != 'as':
            raise template.TemplateSyntaxError('expected ...')
        # ...
    """
    leave_args = leave_args or []
    if ' ' in token.contents:
        tag_name, value = token.contents.split(' ', 1)
    else:
        tag_name, value = token.contents, ''
    args, kwargs = get_kwargs(value)
    if compile_args:
        new_args = args
        for i, var in enumerate(args):
            if i not in leave_args:
                var = parser.compile_filter(var)
            new_args.append(var)
        args = new_args
    if compile_kwargs:
        kwargs = dict([(key, parser.compile_filter(var)) for key, var in
                       kwargs.items()])
    return tag_name, args, kwargs


def get_kwargs(value, parser=None):
    """
    Compiles a list of args and a dictionary of keyword args from a string
    value (usually the contents of a template tag token).

    If a parser is passed in, variables will be compiled.
    """
    args = []
    kwargs = {}
    for key, var in re_kwargs.findall(value):
        if parser:
            var = parser.compile_filter(var)
        if key:
            kwargs[key] = var
        else:
            args.append(var)
    return args, kwargs
