import logging

from django.http import Http404, HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import is_valid_path
from MainApp.models import Snippet, Comment, LANG_CHOICES, Tag, Notification
from MainApp.forms import SnippetForm, UserRegistrationForm, CommentForm
from django.db.models import F, Q, Count, Avg
from MainApp.models import LANG_ICONS
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib import messages
from MainApp.signals import snippet_view
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def index_page(request):
    context = {'pagename': 'PythonBin'}
    messages.success(request, f'Hello word')
    messages.warning(request, f'Happy Sunday')
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
            form.save_m2m()
            messages.success(request, f'New snippet {snippet.name} added')
            return redirect("snippets-list")

        # if form.errors.get('name'):
        #         messages.error(request, f'Ошибка: некорректное имя сниппета.')
        else:
            context = {'form': form, 'pagename': 'Создание сниппета'}
            return render(request, 'pages/add_snippet.html', context)


# snippets/list
# snippets/list?sort=name
# snippets/list?sort=lang
# snippets/list?sort=-lang

def snippets_page(request, my_snippets, num_snippets_on_page=5):
    if my_snippets:
        if not request.user.is_authenticated:
            raise PermissionDenied
        pagename = "Мои сниппеты"
        snippets = Snippet.objects.filter(user=request.user).prefetch_related('tags')
    else:
        pagename = 'Просмотр сниппетов'
        if request.user.is_authenticated:
            snippets = Snippet.objects.filter(Q(public=True) | Q(public=False, user=request.user)).prefetch_related('tags')
        else:
            snippets = Snippet.objects.filter(public=True).prefetch_related('tags')

    # search
    search = request.GET.get('search')
    if search and search.lower() != 'none':
        snippets = snippets.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search)
        )

    # filter
    lang = request.GET.get('lang')
    if lang:
        snippets = snippets.filter(lang=lang)

    tag_id = request.GET.get('tag_id')
    if tag_id:
        snippets = snippets.filter(tags__id=tag_id)

    user_id = request.GET.get('user_id')
    valid_users = User.objects.annotate(public_snippets=Count('snippet', filter=Q(snippet__public=True))).filter(public_snippets__gt=0)
    if user_id and valid_users.filter(id=user_id).exists():
        snippets = snippets.filter(user__id=user_id)

    # sort
    sort = request.GET.get('sort')
    if sort:
        snippets = snippets.order_by(sort)

    paginator = Paginator(snippets, num_snippets_on_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    available_tags = Tag.objects.all()

    context = {
        'pagename': pagename,
        'page_obj': page_obj,
        'sort': sort,
        'LANG_CHOICES': LANG_CHOICES,
        'users': valid_users,
        'search': search,
        'lang': lang,
        'tag_id': tag_id,
        'available_tags': available_tags,
        'user_id': int(user_id) if user_id else None
        }
    return render(request, 'pages/view_snippets.html', context)

def snippet_detail(request, snippet_id):
    # snippet = get_object_or_404(Snippet, id=id)
    snippet = Snippet.objects.prefetch_related("comments", "tags").get(id=snippet_id)
    all_tags = Tag.objects.all()
    snippet_tags = snippet.tags.all()
    available_tags = all_tags.exclude(id__in=snippet_tags.values_list('id', flat=True))

    # send signal
    snippet_view.send(sender=None, snippet=snippet)

    comments = snippet.comments.all()

    paginator = Paginator(comments, 2)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    comment_form = CommentForm()
    context = {
        'pagename': f'Snippet: {snippet.name}',
        'snippet': snippet,
        'available_tags': available_tags,
        'comments': page_obj,
        'comment_form': comment_form,
    }
    return render(request, 'pages/snippet_detail.html', context)


def snippet_delete(request, id):
    snippet = get_object_or_404(Snippet, id=id)
    if snippet.user != request.user:
        raise PermissionDenied
    snippet.delete()
    messages.success(request,f'Snippet "{snippet.name}" was deleted.')
    return redirect('snippets-list')


def snippet_edit(request, id):
    if request.method == 'GET':
        snippet =get_object_or_404(Snippet, id=id)
        form = SnippetForm(instance=snippet)
        context = {
            'pagename': "Редактировать Сниппет",
            'form': form,
            'edit': True,
            'id': id,
            'snippet': snippet
        }
        return render(request, 'pages/add_snippet.html', context)

    if request.method == 'POST':
        snippet = get_object_or_404(Snippet, id=id)
        form = SnippetForm(request.POST, instance=snippet)
        if form.is_valid():
            form.save()
            messages.success(request, f'Snippet "{snippet.name}" was updated successfully.')
            return redirect('snippets-list')
        else:
            # forma nu e validă → arătăm din nou pagina de editare
            context = {
                'pagename': "Редактировать Сниппет",
                'form': form,
                'edit': True,
                'snippet': snippet
            }
            return render(request, 'pages/add_snippet.html', context)

def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('home')
        else:
            context = {
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
        return render(request, 'pages/registration.html', context)
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.username}" registered successfully.')
            return redirect('home')
        else:
            context = {
                'form': form
            }
            return render(request, 'pages/registration.html', context)


# 302
# 404
@login_required()
def comment_add(request):
    if request.method == "POST":
        comment_form = CommentForm(request.POST)
        snippet_id = request.POST.get("snippet_id")
        snippet = get_object_or_404(Snippet, id=snippet_id)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.snippet = snippet
            comment.author = request.user
            comment.save()
            messages.success(request,f'New comments {comment} added')

        return redirect('snippet-detail', snippet_id=snippet.id)
    raise Http404

def snippets_stats_view(request):
    total_snippets = Snippet.objects.count()
    public_snippets = Snippet.objects.filter(public=True).count()
    average_view = Snippet.objects.aggregate(Avg('views_count'))['views_count__avg']
    top_snippets = Snippet.objects.order_by('-views_count')[:5]
    top_users = User.objects.annotate(snippet_count=Count('snippet')).order_by('-snippet_count')[:3]
    messages.success(request, f'Here is statistic')
    context = {
        'total_snippets': total_snippets,
        'public_snippets': public_snippets,
        'avg_views': round(average_view, 2),
        'top_snippets': top_snippets,
        'top_users': top_users,
    }
    return render(request,'pages/statistic.html', context)

@login_required
def add_tag_to_snippet(request,snippet_id):
    snippet = get_object_or_404(Snippet, id=snippet_id)
    if request.method == 'POST':
        tag_id = request.POST.get('tag_id')
        if tag_id:
            tag = get_object_or_404(Tag, id=tag_id)
            snippet.tags.add(tag)
    return redirect('snippet-detail',snippet_id=snippet.id)

def snippets_by_tag(request, tag_id):
    tag = Tag.objects.get(id=tag_id)
    snippets = Snippet.objects.filter(tags=tag)
    context = {
        'snippets': snippets,
        'tag': tag,
        'pagename': f"Сниппеты с тегом: {tag.name}"
    }
    return render(request, 'pages/snippets_by_tag.html', context)


@login_required
def user_notifications(request):
    """Страница с уведомлениями пользователя"""
    # Отмечаем все уведомления как прочитанные при переходе на страницу
    ...
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    # Получаем все уведомления для авторизованного пользователя, сортируем по дате создания
    notifications = Notification.objects.filter(recipient=request.user)

    context = {
        'pagename': 'Мои уведомления',
        'notifications': notifications
    }
    return render(request, 'pages/notifications.html', context)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def simple_api_view(request):
    """
    Простой API endpoint для обработки GET и POST запросов
    """

    if request.method == 'GET':
        # Обработка GET запроса
        try:
            # Здесь может быть логика получения данных из базы
            data = {
                'success': True,
                'message': 'Данные успешно получены!',
                'timestamp': str(datetime.now()),
                'items': [
                    {'id': 1, 'name': 'Элемент 1'},
                    {'id': 2, 'name': 'Элемент 2'},
                    {'id': 3, 'name': 'Элемент 3'}
                ]
            }
            return JsonResponse(data)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    elif request.method == 'POST':
        # Обработка POST запроса
        try:
            # Парсим JSON данные из запроса
            data = json.loads(request.body)

            # Обрабатываем полученные данные
            received_message = data.get('message', '')

            # Здесь может быть логика сохранения в базу данных

            response_data = {
                'success': True,
                'message': f'Получено сообщение: {received_message}',
                'processed': True
            }

            return JsonResponse(response_data)

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Неверный формат JSON'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@login_required
def unread_notifications_count(request):
    """
    API endpoint для получения количества непрочитанных уведомлений
    Использует long polling - отвечает только если есть непрочитанные уведомления
    """
    import time

    # Максимальное время ожидания (30 секунд)
    max_wait_time = 30
    check_interval = 1  # Проверяем каждую секунду

    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        # Получаем количество непрочитанных уведомлений
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

        # Если есть непрочитанные уведомления, сразу отвечаем
        if unread_count > 0:
            return JsonResponse({
                'success': True,
                'unread_count': unread_count,
                'timestamp': str(datetime.now())
            })

        # Ждем перед следующей проверкой
        time.sleep(check_interval)

    # Если время истекло и нет уведомлений, возвращаем 0
    return JsonResponse({
        'success': True,
        'unread_count': 0,
        'timestamp': str(datetime.now())
    })

def is_authenticated(request):
    if request.user.is_authenticated:
        return JsonResponse({'is_authenticated': True})
    else:
        return JsonResponse({'is_authenticated': False})