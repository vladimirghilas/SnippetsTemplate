import logging

from django.contrib.contenttypes.models import ContentType
from django.http import Http404, HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import is_valid_path
from MainApp.models import Snippet, Comment, LANG_CHOICES, Tag, Notification, LikeDislike
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
from django.views.decorators.http import require_http_methods, require_POST
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
            snippets = Snippet.objects.filter(Q(public=True) | Q(public=False, user=request.user)).select_related(
                'user').prefetch_related('tags')
        else:
            snippets = Snippet.objects.filter(public=True).select_related('user').prefetch_related('tags')

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
    valid_users = User.objects.annotate(public_snippets=Count('snippet', filter=Q(snippet__public=True))).filter(
        public_snippets__gt=0)
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
        messages.error(request, "У вас нет прав для удаления этого сниппета.")
        return redirect('snippets-list')
    snippet.delete()
    messages.success(request, f'Snippet "{snippet.name}" was deleted.')
    return redirect('snippets-list')


def snippet_edit(request, id):
    if request.method == 'GET':
        snippet = get_object_or_404(Snippet, id=id)
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
            messages.success(request, f'New comments {comment} added')

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
    return render(request, 'pages/statistic.html', context)


@login_required
def add_tag_to_snippet(request, snippet_id):
    snippet = get_object_or_404(Snippet, id=snippet_id)
    if request.method == 'POST':
        tag_id = request.POST.get('tag_id')
        if tag_id:
            tag = get_object_or_404(Tag, id=tag_id)
            snippet.tags.add(tag)
    return redirect('snippet-detail', snippet_id=snippet.id)


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
def user_notifications(request,id=None):
    """Страница с уведомлениями пользователя"""
    # Отмечаем 1 уведомление как прочитанные
    if id:
        notif = Notification.objects.get(recipient=request.user, id=id)
        notif.is_read = True
        notif.save()
        return redirect('snippet-detail', snippet_id=notif.comment.snippet.id)

    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    # Получаем все уведомления для авторизованного пользователя, сортируем по дате создания
    notifications = list(Notification.objects.filter(recipient=request.user).select_related('comment__snippet'))

    read_count = Notification.objects.filter(recipient=request.user, is_read=True)

    # notif_coment_snipet = Notification.objects.filter(
    #     recipient=request.user,
    #     comment__snippet_id=snippet_id
    # ).select_related('comment', 'comment__snippet')

    context = {
        'pagename': 'Мои уведомления',
        'notifications': notifications,
        'unread_count': unread_count,
        'read_count': read_count,
        # 'notif_coment_snipet': notif_coment_snipet,
    }
    return render(request, 'pages/notifications.html', context)


@login_required
def unread_notifications_count(request):
    # """
    # API endpoint для получения количества непрочитанных уведомлений
    # Использует long polling - отвечает только если есть непрочитанные уведомления
    # """
    import time

    # Максимальное время ожидания (30 секунд)
    max_wait_time = 10
    check_interval = 1  # Проверяем каждую секунду

    last_count = int(request.GET.get('last_count', 0))

    start_time = time.time()
    unread_count = 0

    while time.time() - start_time < max_wait_time:
        # Получаем количество непрочитанных уведомлений
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

        # Если есть непрочитанные уведомления, сразу отвечаем
        if unread_count > last_count:
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
        'unread_count': unread_count,
        'timestamp': str(datetime.now())
    })


@login_required
def notifications_delete(request, id=None):
    if id:
        notification = get_object_or_404(Notification, id=id, recipient=request.user)
        notification.delete()
    else:
        Notification.objects.filter(recipient=request.user, is_read=True).delete()

    return redirect('notifications')


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


def is_authenticated(request):
    if request.user.is_authenticated:
        return JsonResponse({'is_authenticated': True})
    else:
        return JsonResponse({'is_authenticated': False})

@require_POST
@login_required
def add_comment_like(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        comment_id = data.get('comment_id')
        vote = data.get('vote')

        existing_vote, created = LikeDislike.objects.get_or_create(
            user = request.user,
            content_type=ContentType.objects.get_for_model(Comment),
            object_id = comment_id,
            defaults={'vote':vote}
        )
        if not created:
            if existing_vote.vote == vote:
                existing_vote.delete()
            else:
                existing_vote = vote
                existing_vote.save()

        comment=Comment.objects.get(id=comment_id)
        responce_data = {
            "success": True,
            "likes_count": comment.likes_count(),
            "dislikes_count": comment.dislikes_count(),
        }

        return JsonResponse(responce_data)

@require_POST
@login_required
def add_snippet_like(request):
    data = json.loads(request.body)
    snippet_id = data.get('snippet_id')
    vote = data.get('vote')

    if not snippet_id:
        return JsonResponse({"success": False, "error": "No snippet_id provided"}, status=400)

    existing_vote, created = LikeDislike.objects.get_or_create(
        user=request.user,
        content_type=ContentType.objects.get_for_model(Snippet),
        object_id=snippet_id,
        defaults={'vote': vote}
    )
    snippet = Snippet.objects.get(id=snippet_id)
    if not created:
        if existing_vote.vote == vote:
            existing_vote.delete()
        else:
            existing_vote.vote = vote
            existing_vote.save()

    if vote == 1 and snippet.user != request.user:
        Notification.objects.create(
            recipient = snippet.user,
            notification_type = ('like'),
            title=f"{request.user.username} поставил лайк вашему сниппету",
            comment=None,
            message=f"Пользователь {request.user.username} поставил лайк вашему сниппету: {snippet.name}"
        )

    return JsonResponse({
        'success': True,
        'likes_count': snippet.likes_count(),
        'dislikes_count': snippet.dislikes_count(),
    })


def user_profile(request):
    context = {
        'profile_user': request.user
    }
    return render(request, 'pages/user_profile.html', context)

def user_statistics(request):
    user_snippets = Snippet.objects.filter(user=request.user)

    total_snippets = user_snippets.count()

    if total_snippets > 0:
        average_views = user_snippets.aggregate(avg_views=Avg('views'))['avg_views']

    else:
        average_views = 0

    top_snippets = user_snippets.order_by('-views')[:5]

    context = {
        'username': request.user.username,  # <--- aici denumirea utilizatorului
        'total_snippets': total_snippets,
        'average_views': average_views,
        'top_snippets': top_snippets,
    }

    return render(request, 'statistics.html', context)
