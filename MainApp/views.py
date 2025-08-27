import logging
from operator import attrgetter

from django.contrib.contenttypes.models import ContentType
from django.http import Http404, HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import is_valid_path
from MainApp.models import Snippet, Comment, LANG_CHOICES, Tag, Notification, LikeDislike, Subscription
from MainApp.forms import SnippetForm, UserRegistrationForm, CommentForm, UserProfileForm, UserEditForm
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
from itertools import chain
from operator import attrgetter
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from .utils import send_activation_email, verify_activation_token

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
        'author': snippet.user,  # autorul snippet-ului
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

        if user:
            if user.is_active:
                auth.login(request, user)
                return redirect('home')
            else:
                # Аккаунт существует, но не активен
                try:
                    user = User.objects.get(username=username)
                    if not user.check_password(password):
                        raise User.DoesNotExist
                    context = {
                        "errors": ["Ваш аккаунт не подтвержден. Проверьте email для подтверждения."],
                        "username": username
                    }
                except User.DoesNotExist:
                    # Неверный логин или пароль
                    context = {
                        "errors": ["Неверные username или password"],
                        "username": username
                    }

                return render(request, 'pages/index.html', context)

    # GET-запрос, просто показываем форму
    return render(request, 'pages/index.html')


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
            user = form.save(commit=True)
            send_activation_email(user, request)
            messages.success(
                request,
                f'Пользователь "{user.username}" успешно зарегистрирован. Проверьте ваш email для подтверждения аккаунта.')
            return redirect('home')
        else:
            context = {
                'form': form
            }
            return render(request, 'pages/registration.html', context)


def activate_account(request, user_id, token):
    """
    Подтверждение аккаунта пользователя по токену
    """
    try:
        user = User.objects.get(id=user_id)

        # Проверяем, не подтвержден ли уже аккаунт
        if user.is_active:
            messages.info(request, 'Ваш аккаунт уже подтвержден.')
            return redirect('home')

        # Проверяем токен
        if verify_activation_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request,
                             'Ваш аккаунт успешно подтвержден! Теперь вы можете войти в систему.')
            return redirect('home')
        else:
            messages.error(request,
                           'Недействительная ссылка для подтверждения. Возможно, она устарела.')
            return redirect('home')

    except User.DoesNotExist:
        messages.error(request, 'Пользователь не найден.')
        return redirect('home')


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
        'avg_views': round(average_view, 2) if average_view is not None else 0,
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
def user_notifications(request, id=None):
    notif_id = id or request.GET.get('id')

    if notif_id:
        try:
            notif = Notification.objects.get(recipient=request.user, id=int(notif_id))
            notif.is_read = True
            notif.save()
        except Notification.DoesNotExist:
            notif = None

        snippet_id = None
        if notif:
            if notif.comment:
                snippet_id = notif.comment.snippet.id
            elif notif.snippet:
                snippet_id = notif.snippet.id

        if snippet_id:
            return redirect('snippet-detail', snippet_id=snippet_id)


def get_user_notification(user):
    unread_count = Notification.objects.filter(recipient=user, is_read=False).count()
    # Получаем все уведомления для авторизованного пользователя, сортируем по дате создания
    notifications = list(Notification.objects.filter(recipient=user).select_related('comment__snippet'))
    read_count = Notification.objects.filter(recipient=user, is_read=True)
    return {
        'notifications': notifications,
        'unread_count': unread_count,
        'read_count': read_count,
    }


@login_required
def unread_notifications_count(request):
    # if not request.user.is_authenticated:
    #     return JsonResponse({'error': 'Unauthorized'}, status=401)

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
        print(f"Deleted notification {id}")
    else:
        deleted_count, _ = Notification.objects.filter(recipient=request.user, is_read=True).delete()
        print(f"Deleted {deleted_count} read notifications")

    return redirect('user_profile', username=request.user.username)


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
    data = json.loads(request.body)
    comment_id = data.get('comment_id')
    vote = data.get('vote')

    comment = get_object_or_404(Comment, id=comment_id)

    content_type = ContentType.objects.get_for_model(Comment)
    existing_vote, created = LikeDislike.objects.get_or_create(
        user=request.user,
        content_type=content_type,
        object_id=comment_id,
        defaults={'vote': vote}
    )
    send_notification = False
    if not created:
        if existing_vote.vote == vote:
            existing_vote.delete()
        else:
            existing_vote.vote = vote
            existing_vote.save()
            if vote == LikeDislike.LIKE:
                send_notification = True
    else:
        if vote == LikeDislike.LIKE:
            send_notification = True

    if send_notification and comment.author != request.user:
        Notification.objects.create(
            recipient=comment.author,
            notification_type='like',
            title=f"{request.user.username} поставил лайк вашему комментарию",
            comment=comment,
            snippet=comment.snippet,
            message=f"Пользователь {request.user.username} поставил лайк вашему комментарию к сниппету: {comment.snippet.name}"
        )

    response_data = {
        "success": True,
        "likes_count": comment.likes_count(),
        "dislikes_count": comment.dislikes_count(),
    }

    return JsonResponse(response_data)


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
    send_notification = False

    if not created:
        if existing_vote.vote == vote:
            existing_vote.delete()
        else:
            existing_vote.vote = vote
            existing_vote.save()

            if vote == LikeDislike.LIKE:
                send_notification = True
    else:
        if vote == LikeDislike.LIKE:
            send_notification = True

    if send_notification and snippet.user != request.user:
        Notification.objects.create(
            recipient=snippet.user,
            notification_type=('like'),
            title=f"{request.user.username} поставил лайк вашему сниппету",
            comment=None,
            snippet=snippet,
            message=f"Пользователь {request.user.username} поставил лайк вашему сниппету: {snippet.name}"
        )

    return JsonResponse({
        'success': True,
        'likes_count': snippet.likes_count(),
        'dislikes_count': snippet.dislikes_count(),
    })


def user_profile(request, username):
    tab = request.GET.get("tab", "profile")
    profile_user = get_object_or_404(User, username=username)

    # если у тебя есть отдельная модель Profile
    profile = getattr(profile_user, "profile", None)
    #  История только для владельца профиля
    if request.user.is_authenticated and request.user == profile_user:
        user_snippets = Snippet.objects.filter(user=request.user)
        user_comments = Comment.objects.filter(author=request.user)

        # Сниппеты в унифицированный формат
        snippet_actions = [
            {
                "url": f"/snippet/{s.id}",
                "title": f" Сниппет: {s.name}",
                "creation_date": s.creation_date,
                "extra": f"{s.views_count} просмотров",
            }
            for s in user_snippets
        ]

        # Комментарии в унифицированный формат
        comment_actions = [
            {
                "url": f"/snippet/{c.snippet.id}",
                "title": f" Комментарий к {c.snippet.name}",
                "creation_date": c.creation_date,
                "extra": c.text[:100],
            }
            for c in user_comments
        ]

        # Объединяем и сортируем по дате
        recent_actions = sorted(
            chain(snippet_actions, comment_actions),
            key=lambda obj: obj["creation_date"],
            reverse=True,
        )[:20]
    else:
        recent_actions = []  # для чужих профилей историю не показываем

    # Общая статистика по пользователю
    total_snippets = Snippet.objects.filter(user=profile_user).count()
    average_views = round(
        Snippet.objects.filter(user=profile_user).aggregate(avg_views=Avg("views_count"))["avg_views"] or 0,
        1,
    )
    top_snippets = Snippet.objects.filter(user=profile_user).order_by("-views_count")[:5]

    if tab in ("notifications", "info") and request.user.is_authenticated and request.user == profile_user:
        notifications_context = get_user_notification(request.user)
    else:
        notifications_context = {"notifications": [], "unread_count": 0, "read_count": []}

    context = {
        "tab": tab,
        "profile": profile,
        "profile_user": profile_user,
        "total_snippets": total_snippets,
        "average_views": average_views,
        "top_snippets": top_snippets,
        "recent_actions": recent_actions,
        **notifications_context,
    }

    return render(request, "pages/user_profile.html", context)


def edit_profile(request):
    if request.method == 'POST':
        user_profile = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        user_form = UserEditForm(request.POST, request.FILES, instance=request.user)
        if user_form.is_valid() and user_profile.is_valid():
            user_form.save()
            user_profile.save()
            messages.success(request, "Профиль успешно обновлен!")
            return redirect('profile')  # перенаправляем на страницу профиля
    else:
        user_profile = UserProfileForm(instance=request.user.profile)
        user_form = UserEditForm(instance=request.user)

        context = {
            'pagename': 'Редактирование профиля',
            'user_form': user_form,
            'user_profile': user_profile,
        }

    # Возвращаем шаблон с формой для GET-запроса или если форма невалидна
    return render(request, 'pages/edit_profile.html', context)


def my_profile(request):
    if not request.user.is_authenticated:
        return redirect('login')  # sau pagina de login
    return redirect('user_profile', username=request.user.username)


def resend_email(request):
    if request.method == 'GET':
        return render(request, 'pages/resend_email.html/')
    elif request.method == 'POST':
        email = request.POST.get('email')
        # TODO:
        user = User.objects.get(email=email)
        try:
            send_activation_email(user, request)
            messages.success(request, f'Email для подтверждения аккаунта отправлен повторно. Проверьте ваш email.')
        except:
            messages.error(request, f'ask your administration')
        return redirect('home')
    else:
        raise Http404


@login_required
def delete_account_view(request):
    if request.method == 'POST':
        user = request.user
        user_logout(request)  # разлогиниваем пользователя
        user.delete()  # удаляем аккаунт
        messages.success(request, "Ваш аккаунт был успешно удалён.")
        return redirect('home')  # перенаправление на главную страницу после удаления
    return redirect('user_profile', username=request.user.username)


@login_required
def toggle_subscription(request, snippet_id):
    snippet = get_object_or_404(Snippet, id=snippet_id)
    subscription = Subscription.objects.filter(user=request.user, snippet=snippet)

    if subscription.exists():
        subscription.delete()
    else:
        Subscription.objects.create(user=request.user, snippet=snippet)

    return redirect('snippet-detail', snippet_id=snippet.id)


@login_required
def subscriptions_page(request):
    # Сниппеты, на которые подписан текущий пользователь
    my_subscriptions = Subscription.objects.filter(user=request.user).select_related("snippet", "snippet__user")

    # Пользователи, подписавшиеся на ваши сниппеты
    subscribers_to_my_snippets = Subscription.objects.filter(snippet__user=request.user).select_related("user", "snippet")
    context = {
        **get_user_notification(request.user),
        "my_subscriptions": my_subscriptions,
        "subscribers_to_my_snippets": subscribers_to_my_snippets,
    }
    return render(request, "pages/subscribe.html", context)
