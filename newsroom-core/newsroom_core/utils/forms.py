def form_kwargs(request):
    kwargs = {}
    if request.method == 'POST':
        kwargs['data'] = request.POST
        kwargs['files'] = request.FILES
    return kwargs