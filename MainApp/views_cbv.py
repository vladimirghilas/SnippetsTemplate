from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView
from django.contrib import messages, auth
from MainApp.forms import SnippetForm, CommentForm
from MainApp.models import Snippet, Tag, Notification
from MainApp.signals import snippet_view


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        snippet = self.object

        # tags
        all_tags = Tag.objects.all()
        snippet_tags = snippet.tags.all()
        available_tags = all_tags.exclude(id__in=snippet_tags.values_list("id", flat=True))
        context["available_tags"] = available_tags

        # signal
        snippet_view.send(sender=None, snippet=snippet)

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
            return redirect("snippet-detail", pk=snippet_id)

        # fallback
        return redirect("home")
