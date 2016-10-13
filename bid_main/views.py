from django.shortcuts import render


def index(request):
    context = {
        'page_id': 'index',
    }
    return render(request, 'index.html', context)


def about(request):
    context = {
    }
    return render(request, 'about.html', context)
