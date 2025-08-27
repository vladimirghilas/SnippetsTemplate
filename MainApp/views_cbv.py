from django.db.models import Q
from django.views.generic import ListView, UpdateView

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, FormView
from django.contrib import messages, auth
from MainApp.forms import SnippetForm, CommentForm, UserRegistrationForm
from MainApp.models import Snippet, Tag, Notification, LANG_CHOICES, Subscription
from MainApp.signals import snippet_view
from MainApp.utils import send_activation_email


class AddSnippetView(LoginRequiredMixin, CreateView):
    """Создание нового сниппета"""
    model = Snippet
    form_class = SnippetForm
    template_name = 'pages/add_snippet.html'
    success_url = reverse_lazy('snippets-list')
    # pk_url_kwarg = "id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pagename'] = 'Создание сниппета'
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Success!!!")
        return super().form_valid(form)

class SnippetDetailView(DetailView):
    model = Snippet
    template_name = "pages/snippet_detail.html"
    context_object_name = "snippet"
    pk_url_kwarg = "snippet_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        snippet = self.object

        # tags
        all_tags = Tag.objects.all()
        snippet_tags = snippet.tags.all()
        available_tags = all_tags.exclude(id__in=snippet_tags.values_list("id", flat=True))
        context["available_tags"] = available_tags

        # signal
        # snippet_view.send(sender=None, snippet=snippet)

        # comments + pagination (OPTIMIZED)
        comments_qs = (
            snippet.comments
            .select_related("snippet")     # optim pentru autorul comentariului
            .order_by("-creation_date")    # cel mai nou primul
        )
        paginator = Paginator(comments_qs, 2)
        page_number = self.request.GET.get("page")
        context["comments"] = paginator.get_page(page_number)

        # form
        context["comment_form"] = CommentForm()

        # autor snippet
        context["author"] = snippet.user

        # titlu
        context["pagename"] = f"Snippet: {snippet.name}"

        user = self.request.user
        if user.is_authenticated:
            context["is_subscribed"] = snippet.subscriptions.filter(user=user).exists()
        else:
            context["is_subscribed"] = False

        return context


class LogoutView(View):
    def get(self, request):# куда редиректить после выхода
        auth.logout(request)
        return redirect('home')

class UserNotificationsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        notif_id = kwargs.get("id") or request.GET.get("id")
        snippet_id = None

        if notif_id:
            try:
                notif = Notification.objects.get(recipient=request.user, id=int(notif_id))
                notif.is_read = True
                notif.save()

                if notif.comment:
                    snippet_id = notif.comment.snippet.id
                elif notif.snippet:
                    snippet_id = notif.snippet.id
            except Notification.DoesNotExist:
                pass

        if snippet_id:
            return redirect("snippet-detail", snippet_id=snippet_id)

        # fallback
        return redirect("home")


class SnippetsListView(ListView):
    """Отображение списка сниппетов с фильтрацией, поиском и сортировкой"""
    model = Snippet
    template_name = 'pages/view_snippets.html'
    context_object_name = 'snippets'
    paginate_by = 10

    def get_queryset(self):
        my_snippets = self.kwargs.get('my_snippets', False)

        if my_snippets:
            if not self.request.user.is_authenticated:
                raise PermissionDenied
            queryset = Snippet.objects.filter(user=self.request.user).prefetch_related('tags')
        else:
            if self.request.user.is_authenticated:  # auth: all public + self private
                queryset = Snippet.objects.filter(
                    Q(public=True) | Q(user=self.request.user)
                ).select_related("user").prefetch_related('tags')
            else:  # not auth: all public
                queryset = Snippet.objects.filter(public=True).select_related("user").prefetch_related('tags')

        # Поиск
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search)
            )

        # Фильтрация по языку
        lang = self.request.GET.get("lang")
        if lang:
            queryset = queryset.filter(lang=lang)

        # Фильтрация по пользователю
        user_id = self.request.GET.get("user_id")
        if user_id:
            queryset = queryset.filter(user__id=user_id)

        # Сортировка
        sort = self.request.GET.get("sort")
        if sort:
            queryset = queryset.order_by(sort)

        # by tag
        tag_id = self.request.GET.get('tag_id')
        if tag_id:
            queryset= queryset.filter(tags__id=tag_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        my_snippets = self.kwargs.get('my_snippets', False)

        if my_snippets:
            context['pagename'] = 'Мои сниппеты'
        else:
            context['pagename'] = 'Просмотр сниппетов'

        # Получаем пользователей со сниппетами
        users = User.objects.filter(snippet__isnull=False).distinct()
        available_tags = Tag.objects.all()
        context.update({
            'sort': self.request.GET.get("sort"),
            'LANG_CHOICES': LANG_CHOICES,
            'users': users,
            'lang': self.request.GET.get("lang"),
            'user_id': self.request.GET.get("user_id"),
            'tag_id': self.request.GET.get('tag_id'),
            'available_tags': available_tags,
        })

        return context

class SnippetUpdateView(UpdateView):
    model = Snippet
    form_class = SnippetForm
    template_name = "pages/add_snippet.html"
    context_object_name = 'snippet'

    def dispatch(self, request, *args, **kwargs):
        snippet = self.get_object()
        if snippet.user != request.user:
            messages.error(request, "У вас нет прав для редактирования этого сниппета.")
            return redirect("snippets-list")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pagename"] = "Редактировать Сниппет"
        context["edit"] = True
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Snippet "{self.object.name}" was updated successfully.')
        return response

    def get_success_url(self):
        return reverse_lazy("snippets-list")


# class SnippetEditView(UpdateView):
#     model = Snippet
#     form_class = SnippetForm
#     template_name = ""
#     success_url = ""
#     pk_url_kwarg = 'id'
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["pgename"]= ""
#         context["edit"] = True
#         context['id'] = self.kwargs.get('id')


class UserRegistrationView(FormView):
    template_name = "pages/registration.html"
    form_class = UserRegistrationForm
    success_url = "home"

    def form_valid(self, form):
        user = form.save(commit=True)
        send_activation_email(user, self.request)
        messages.success(
            self.request,
            f'Пользователь "{user.username}" успешно зарегистрирован. Проверьте ваш email для подтверждения аккаунта.'
        )

        return super().form_valid(form)

class AddTagToSnippetView(LoginRequiredMixin, View):
    # pk_url_kwarg = "snippet_id"
    def post(self, request, snippet_id):
        snippet = get_object_or_404(Snippet, id=snippet_id)
        # проверяем, что пользователь владелец сниппета
        if snippet.user != request.user:
            raise PermissionDenied

        tag_id = request.POST.get("tag_id")
        if tag_id:
            tag = get_object_or_404(Tag, id=tag_id)
            snippet.tags.add(tag)
            messages.success(request, f'Тег "{tag.name}" добавлен к сниппету "{snippet.name}".')
        else:
            messages.error(request, "Не выбран тег для добавления.")

        return redirect("snippet-detail", snippet_id=snippet.id)

