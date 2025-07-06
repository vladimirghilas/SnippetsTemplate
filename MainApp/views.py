from django.http import Http404, HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import is_valid_path
from MainApp.models import Snippet, Comment
from MainApp.forms import SnippetForm, UserRegistrationForm, CommentForm
from django.db.models import F, Q
from MainApp.models import LANG_ICONS
from django.contrib import auth
from django.contrib.auth.decorators import login_required

def get_icons_class(lang):
    return LANG_ICONS.get(lang)


def index_page(request):
    context = {'pagename': 'PythonBin'}
    return render(request, 'pages/index.html', context)

@login_required
def add_snippet_page(request):
    if request.method == "GET":
        form = SnippetForm()
        context = {'form': form, 'pagename': 'Создание сниппета'}
        return render(request, 'pages/add_snippet.html', context)

    if request.method == "POST":
        form = SnippetForm(request.POST)
        if form.is_valid():
            snippet = form.save(commit=False)
            snippet.user = request.user
            snippet.save()
            return redirect("snippets-list")
        else:
            context = {'form': form, 'pagename': 'Создание сниппета'}
            return render(request, 'pages/add_snippet.html', context)

#snippets/list
#snippets/list?sort=name
#snippets/list?sort=lang
#snippets/list?sort=-lang

def snippets_page(request):
    snippets = Snippet.objects.all()
    if request.user.is_authenticated:
        snippets = Snippet.objects.filter(Q(public=True) | Q(public=False, user=request.user))
    else:
        snippets = Snippet.objects.filter(public=True)
    #search
    search = request.GET.get('search')
    if search:
        snippets = snippets.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search)
        )
    #sort
    sort = request.GET.get('sort')
    if sort:
        snippets = snippets.order_by(sort)

    for snippet in snippets:
        snippet.icon_class = get_icons_class(snippet.lang)
    context = {
        'snippets': snippets,
        'pagename': 'Просмотр сниппетов',
        'sort': sort,
        'search': search
    }
    return render(request, 'pages/view_snippets.html', context)

@login_required()
def my_snippets_page(request):
    snippets = Snippet.objects.filter(user=request.user)
    context = {
            "snippets": snippets,
            "pagename": "Мои сниппеты"
        }
    return render(request, 'pages/view_snippets.html', context)

def snippet_detail(request, id):
    #snippet = get_object_or_404(Snippet, id=id)
    snippet = Snippet.objects.prefetch_related("comments").get(id=id)
    snippet.views_count = F('views_count') + 1
    snippet.save(update_fields=['views_count'])
    snippet.refresh_from_db()
    comments = snippet.comments.all()
    comment_form = CommentForm()
    context = {
        'pagename': f'Snippet: {snippet.name}',
        'snippet': snippet,
        'comments': comments,
        'comment_form': comment_form,
    }
    return render(request, 'pages/snippet_detail.html', context)


def snippet_delete(request, id):
    snippet = get_object_or_404(Snippet, id=id)
    if snippet.user !=request.user:
        raise PermissionDenied
    snippet.delete()
    return redirect('snippets-list')


def snippet_edit(request, id):
    snippet = get_object_or_404(Snippet, pk=id)

    if request.method == 'POST':
        form = SnippetForm(request.POST, instance=snippet)
        if form.is_valid():
            form.save()
            return redirect('snippets-list')
    else:
        form = SnippetForm(instance=snippet)

    return render(request, 'pages/view_snippets.html', {'form': form, 'snippet': snippet})

def login(request):
    if request.method =="POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('home')
        else:
            context={
                "errors": ["Incorrect username or password"],
                "username": username
            }
            return render(request, 'pages/index.html', context)

def user_logout(request):
    auth.logout(request)
    return redirect('home')

def user_registration(request):
    if request.method == "GET":
        form = UserRegistrationForm()
        context = {
            'form': form
        }
        return render(request,'pages/registration.html', context)
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
        else:
            context = {
                'form': form
            }
            return render(request, 'pages/registration.html', context)

@login_required()
def comment_add(request):
    if request.method =="POST":
        comment_form = CommentForm(request.POST)
        snippet_id = request.POST.get("snippet_id")
        snippet =get_object_or_404(Snippet, id=snippet_id)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.snippet = snippet
            comment.author = request.user
            comment.save()
            return redirect('snippet-detail', id=snippet.id)

    raise Http404




