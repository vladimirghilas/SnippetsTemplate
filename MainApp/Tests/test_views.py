from urllib.request import Request
from wsgiref.validate import assert_

from django.template.base import kwarg_re
from django.template.context_processors import request
import pytest
from MainApp.views import index_page, add_snippet_page
from django.test import Client, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User, AnonymousUser
from MainApp.models import Snippet, Tag

from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware

import pytest
# from django.test import Client
# from django.urls import reverse
# from django.contrib.auth.models import User
from MainApp.models import Snippet, Comment
from MainApp.factories import UserFactory, SnippetFactory, CommentFactory


@pytest.fixture
def client():
    """Фикстура для создания тестового клиента"""
    return Client()


@pytest.fixture
def user():
    """Фикстура для создания пользователя"""
    return UserFactory()


@pytest.fixture
def authenticated_client(client, user):
    """Фикстура для создания аутентифицированного клиента"""
    client.force_login(user)
    return client, user


@pytest.fixture
def snippet(user):
    """Фикстура для создания сниппета"""
    return SnippetFactory(user=user)


@pytest.fixture
def comment_data(snippet):
    """Фикстура для данных комментария"""
    return {
        'text': 'Тестовый комментарий',
        'snippet_id': snippet.id
    }


@pytest.mark.django_db
class TestCommentAdd:
    """Тесты для функции comment_add"""

    def test_comment_add_success(self, authenticated_client, snippet, comment_data):
        """Тест успешного добавления комментария"""
        client, user = authenticated_client

        # Проверяем, что пользователь аутентифицирован
        assert user.is_authenticated

        # Отправляем POST запрос для добавления комментария
        response = client.post(reverse('comment-add'), comment_data)

        # Проверяем, что произошло перенаправление на страницу сниппета
        assert response.status_code == 302
        assert response.url == reverse('snippet-detail', kwargs={'snippet_id': snippet.id})

        # Проверяем, что комментарий был создан в базе данных
        comment = Comment.objects.filter(snippet=snippet).first()
        assert comment is not None
        assert comment.text == comment_data['text']
        assert comment.author == user
        assert comment.snippet == snippet

    def test_comment_add_not_authenticated(self, client, snippet, comment_data):
        """Тест попытки добавления комментария неаутентифицированным пользователем"""
        # Отправляем POST запрос без аутентификации
        response = client.post(reverse('comment-add'), comment_data)

        # Проверяем, что произошло перенаправление на страницу входа
        assert response.status_code == 302
        assert '/login' in response.url

        # Проверяем, что комментарий не был создан
        comment_count = Comment.objects.filter(snippet=snippet).count()
        assert comment_count == 0

    def test_comment_add_invalid_snippet_id(self, authenticated_client, comment_data):
        """Тест добавления комментария к несуществующему сниппету"""
        client, user = authenticated_client

        # Устанавливаем несуществующий ID сниппета
        comment_data['snippet_id'] = 99999

        # Отправляем POST запрос
        response = client.post(reverse('comment-add'), comment_data)

        # Проверяем, что получили 404 ошибку
        assert response.status_code == 404

        # Проверяем, что комментарий не был создан
        comment_count = Comment.objects.count()
        assert comment_count == 0

    def test_comment_add_invalid_form_data(self, authenticated_client, snippet):
        """Тест добавления комментария с невалидными данными формы"""
        client, user = authenticated_client

        # Отправляем пустой текст комментария
        invalid_data = {
            'text': '',  # Пустой текст
            'snippet_id': snippet.id
        }

        # Отправляем POST запрос
        response = client.post(reverse('comment-add'), invalid_data)

        # Проверяем, что произошло перенаправление (форма невалидна, но сниппет существует)
        assert response.status_code == 302
        assert response.url == reverse('snippet-detail', kwargs={'snippet_id': snippet.id})

        # Проверяем, что комментарий не был создан из-за невалидности формы
        comment_count = Comment.objects.filter(snippet=snippet).count()
        assert comment_count == 0

    def test_comment_add_get_request(self, authenticated_client):
        """Тест GET запроса к comment_add (должен вернуть 404)"""
        client, user = authenticated_client
        response = client.get(reverse('comment-add'))

        # Проверяем, что получили 404 ошибку
        assert response.status_code == 404

    def test_comment_add_multiple_comments(self, authenticated_client, snippet):
        """Тест добавления нескольких комментариев к одному сниппету"""
        client, user = authenticated_client

        comments_data = [
            {'text': 'Первый комментарий', 'snippet_id': snippet.id},
            {'text': 'Второй комментарий', 'snippet_id': snippet.id},
            {'text': 'Третий комментарий', 'snippet_id': snippet.id}
        ]

        # Добавляем несколько комментариев
        for comment_data in comments_data:
            response = client.post(reverse('comment-add'), comment_data)
            assert response.status_code == 302

        # Проверяем, что все комментарии были созданы
        comments = Comment.objects.filter(snippet=snippet)
        assert comments.count() == 3

        # Проверяем содержимое комментариев
        comment_texts = [comment.text for comment in comments]
        expected_texts = ['Первый комментарий', 'Второй комментарий', 'Третий комментарий']
        assert sorted(comment_texts) == sorted(expected_texts)

    def test_comment_add_different_users(self, client, snippet):
        """Тест добавления комментариев разными пользователями"""
        users = UserFactory.create_batch(3)

        comments_data = [
            {'text': f'Комментарий от {user.username}', 'snippet_id': snippet.id}
            for user in users
        ]

        # Каждый пользователь добавляет свой комментарий
        for user, comment_data in zip(users, comments_data):
            client.force_login(user)
            response = client.post(reverse('comment-add'), comment_data)
            assert response.status_code == 302

        # Проверяем, что все комментарии были созданы с правильными авторами
        comments = Comment.objects.filter(snippet=snippet)
        assert comments.count() == 3

        for comment in comments:
            assert comment.author in users

    # @pytest.mark.skip(reason="Тест не закончен")
    def test_comment_add_missing_snippet_id(self, authenticated_client):
        """Тест добавления комментария без указания snippet_id"""
        client, user = authenticated_client
        # Отправляем POST запрос, не указав snippet_id
        response = client.post(reverse('comment-add'), {'text': 'simple text'})

        # Проверяем, что получили 404 ошибку
        assert response.status_code == 404
        # Проверяем, что комментарий не был создан
        assert Comment.objects.count() == 0

    def test_comment_add_long_text(self, authenticated_client, snippet):
        """Тест добавления комментария с длинным текстом"""
        client, user = authenticated_client

        long_text = 'Очень длинный комментарий .' * 100  # Создаем длинный текст 2600
        comment_data = {
            'text': long_text,
            'snippet_id': snippet.id
        }

        response = client.post(reverse('comment-add'), comment_data)

        # Проверяем, что комментарий был успешно добавлен
        assert response.status_code == 302
        assert response.url == reverse('snippet-detail', kwargs={'snippet_id': snippet.id})

        # Проверяем, что комментарий был создан с полным текстом
        comment = Comment.objects.filter(snippet=snippet).first()
        assert comment is not None
        assert len(comment.text) == len(long_text)



def add_messages_and_session_to_request(request):
    # Attach session for messages to work correctly
    middleware = SessionMiddleware(lambda r: None)  # Mock the get_response callable
    middleware.process_request(request)
    request.session.save()  # Ensure a session key is generated

    # Attach message storage
    setattr(request, '_messages', FallbackStorage(request))


class TestIndexPage:
    def test_index(self):
        client = Client()
        responce = client.get(reverse('home'))

        assert responce.status_code == 200
        assert "Добро пожаловать" in responce.content.decode()
        assert responce.context.get('pagename') == 'PythonBin'


@pytest.mark.django_db
class TestAddSnippetPage:
    def setup_method(self):
        self.factory = RequestFactory()

    def test_guest_user(self):
        request = self.factory.get(reverse('snippet-add'))
        request.user = AnonymousUser()
        response = add_snippet_page(request)

        assert response.status_code == 302

    def test_auth_user(self):
        request = self.factory.get(reverse('snippet-add'))
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        request.user = user
        response = add_snippet_page(request)

        assert response.status_code == 200

    def test_post_form_data(self):
        tag = Tag.objects.create(name='python')
        form_data = {
            'name': 'Test form snippet',
            'lang': 'python',
            'code': 'simple py code',
            'public': True,
            'tags': [tag.id]
        }
        user = User.objects.create_user(
            username="testuser2",
            email="test2@example.com",
            password="testpass123"
        )
        request = self.factory.post(reverse('snippet-add'), form_data)
        request.user = user
        add_messages_and_session_to_request(request)
        response = add_snippet_page(request)
        print(response.status_code)
        print(response.content)

        snippet = Snippet.objects.latest('id')

        assert response.status_code == 302
        assert snippet.name == form_data['name']
        assert snippet.lang == form_data['lang']
        assert snippet.public == form_data['public']


@pytest.mark.django_db
class TestSnippetDeletePage:
    def setup_method(self):
        self.client = Client()

    def test_delete_not_existing(self):
        response = self.client.get(reverse('snippet-delete', kwargs={'id': 2}))

        assert response.status_code == 404

    def test_delete(self):
        user = User.objects.create_user(
            username="testuser2",
            email="test2@example.com",
            password="testpass123"
        )
        Snippet.objects.create(
            name="For delete",
            lang="javascript",
            code="snippet code",
            user=user
        )
        self.client.login(username="testuser2", password="testpass123")
        response = self.client.get(reverse('snippet-delete', kwargs={'id': 1}))

        assert response.status_code == 302
        assert Snippet.objects.count() == 0

    def test_delete_not_auth(self):
        user = User.objects.create_user(
            username="testuser2",
            email="test2@example.com",
            password="testpass123"
        )
        Snippet.objects.create(
            name="For delete",
            lang="javascript",
            code="snippet code",
            user=user
        )
        response = self.client.get(reverse('snippet-delete', kwargs={'id': 1}))

        assert response.status_code == 403


@pytest.mark.django_db
class TestSnippetsPage:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.another_user = User.objects.create_user(
            username="anotheruser",
            email="another@example.com",
            password="testpass123"
        )
        self.third_user = User.objects.create_user(
            username="thirduser",
            email="third@example.com",
            password="testpass123"
        )

        # Создаем множество тестовых сниппетов для более надежных тестов
        self.snippets = []

        # Сниппеты первого пользователя
        self.snippets.extend([
            Snippet.objects.create(
                name="Python Hello World",
                code="print('Hello, World!')",
                lang="python",
                user=self.user,
                public=True
            ),
            Snippet.objects.create(
                name="Python Calculator",
                code="def add(a, b):\n    return a + b",
                lang="python",
                user=self.user,
                public=True
            ),
            Snippet.objects.create(
                name="Private Python Snippet",
                code="print('This is private')",
                lang="python",
                user=self.user,
                public=False
            ),
            Snippet.objects.create(
                name="JavaScript Alert",
                code="alert('Hello from JS');",
                lang="javascript",
                user=self.user,
                public=True
            ),
            Snippet.objects.create(
                name="HTML Template",
                code="<html><body><h1>Hello</h1></body></html>",
                lang="html",
                user=self.user,
                public=True
            )
        ])

        # Сниппеты второго пользователя
        self.snippets.extend([
            Snippet.objects.create(
                name="Another Python Code",
                code="import os\nprint(os.getcwd())",
                lang="python",
                user=self.another_user,
                public=True
            ),
            Snippet.objects.create(
                name="CSS Styles",
                code="body { color: red; }",
                lang="css",
                user=self.another_user,
                public=True
            ),
            Snippet.objects.create(
                name="Private Another User Snippet",
                code="console.log('private');",
                lang="javascript",
                user=self.another_user,
                public=False
            )
        ])

        # Сниппеты третьего пользователя
        self.snippets.extend([
            Snippet.objects.create(
                name="SQL Query",
                code="SELECT * FROM users WHERE active = 1;",
                lang="sql",
                user=self.third_user,
                public=True
            ),
            Snippet.objects.create(
                name="Bash Script",
                code="#!/bin/bash\necho 'Hello from bash'",
                lang="bash",
                user=self.third_user,
                public=True
            )
        ])

    def test_my_snippets_authenticated_user(self):
        """Тест для просмотра своих сниппетов авторизованным пользователем"""
        self.client.force_login(self.user)
        response = self.client.get('/snippets/my')

        assert response.status_code == 200
        assert response.context['pagename'] == 'Мои сниппеты'
        # Проверяем, что видны только сниппеты текущего пользователя
        user_snippets = [s for s in self.snippets if s.user == self.user]
        assert len(response.context['page_obj']) == len(user_snippets)

    def test_my_snippets_anonymous_user(self):
        """Тест для просмотра своих сниппетов неавторизованным пользователем"""
        response = self.client.get('/snippets/my')

        assert response.status_code == 403  # PermissionDenied возвращает 403

    def test_all_snippets_authenticated_user(self):
        """Тест для просмотра всех сниппетов авторизованным пользователем"""
        num_snippets_on_page = 5
        self.client.force_login(self.user)
        response = self.client.get('/snippets/list', {'num_snippets_on_page': num_snippets_on_page})

        assert response.status_code == 200
        assert response.context['pagename'] == 'Просмотр сниппетов'
        # Проверяем, что видны публичные сниппеты всех пользователей + приватные текущего
        public_snippets = [s for s in self.snippets if s.public]
        private_own_snippets = [s for s in self.snippets if not s.public and s.user == self.user]
        expected_count = len(public_snippets) + len(private_own_snippets)
        if expected_count > num_snippets_on_page:
            expected_count = num_snippets_on_page
        assert len(response.context['page_obj']) == expected_count

    def test_all_snippets_anonymous_user(self):
        """Тест для просмотра всех сниппетов неавторизованным пользователем"""
        num_snippets_on_page = 5
        response = self.client.get('/snippets/list')

        assert response.status_code == 200
        assert response.context['pagename'] == 'Просмотр сниппетов'
        # Проверяем, что видны только публичные сниппеты
        public_snippets = [s for s in self.snippets if s.public]
        count = len(public_snippets)
        if count > num_snippets_on_page:
            count = num_snippets_on_page
        assert len(response.context['page_obj']) == count

    def test_snippets_with_search(self):
        """Тест поиска сниппетов"""
        self.client.force_login(self.user)
        response = self.client.get('/snippets/list?search=Python')

        assert response.status_code == 200
        # Проверяем, что найдены сниппеты с "Python" в названии или коде
        found_snippets = response.context['page_obj']
        assert len(found_snippets) > 0
        for snippet in found_snippets:
            assert 'Python' in snippet.name or 'Python' in snippet.code

    def test_snippets_with_lang_filter(self):
        """Тест фильтрации по языку"""
        self.client.force_login(self.user)
        response = self.client.get('/snippets/list?lang=python')

        assert response.status_code == 200
        assert response.context['lang'] == 'python'
        # Проверяем, что все найденные сниппеты имеют язык python
        found_snippets = response.context['page_obj']
        assert len(found_snippets) > 0
        for snippet in found_snippets:
            assert snippet.lang == 'python'

    def test_snippets_with_user_filter(self):
        """Тест фильтрации по пользователю"""
        self.client.force_login(self.user)
        response = self.client.get(f'/snippets/list?user_id={self.another_user.id}')

        assert response.status_code == 200
        assert response.context['user_id'] == self.another_user.id
        # Проверяем, что найдены только сниппеты указанного пользователя
        found_snippets = response.context['page_obj']
        assert len(found_snippets) > 0
        for snippet in found_snippets:
            assert snippet.user == self.another_user

    def test_snippets_with_sorting(self):
        """Тест сортировки сниппетов"""
        self.client.force_login(self.user)
        response = self.client.get('/snippets/list?sort=name')

        assert response.status_code == 200
        assert response.context['sort'] == 'name'
        snippets_list = list(response.context['page_obj'])
        # Проверяем, что сниппеты отсортированы по имени
        for i in range(len(snippets_list) - 1):
            assert snippets_list[i].name <= snippets_list[i + 1].name

    def test_snippets_with_reverse_sorting(self):
        """Тест обратной сортировки сниппетов"""
        self.client.force_login(self.user)
        response = self.client.get('/snippets/list?sort=-name')

        assert response.status_code == 200
        assert response.context['sort'] == '-name'
        snippets_list = list(response.context['page_obj'])
        # Проверяем, что сниппеты отсортированы по имени в обратном порядке
        for i in range(len(snippets_list) - 1):
            assert snippets_list[i].name >= snippets_list[i + 1].name

    def test_snippets_with_lang_sorting(self):
        """Тест сортировки по языку"""
        self.client.force_login(self.user)
        response = self.client.get('/snippets/list?sort=lang')

        assert response.status_code == 200
        assert response.context['sort'] == 'lang'
        snippets_list = list(response.context['page_obj'])
        # Проверяем, что сниппеты отсортированы по языку
        for i in range(len(snippets_list) - 1):
            assert snippets_list[i].lang <= snippets_list[i + 1].lang

    def test_multiple_filters_combined(self):
        """Тест комбинирования нескольких фильтров"""
        self.client.force_login(self.user)
        response = self.client.get(f'/snippets/list?lang=python&user_id={self.user.id}&search=Hello')

        assert response.status_code == 200
        assert response.context['lang'] == 'python'
        assert response.context['user_id'] == self.user.id
        # Проверяем, что найдены сниппеты, соответствующие всем фильтрам
        found_snippets = response.context['page_obj']
        for snippet in found_snippets:
            assert snippet.lang == 'python'
            assert snippet.user == self.user
            assert 'Hello' in snippet.name or 'Hello' in snippet.code

    def test_public_and_private_snippets_for_authenticated_user(self):
        """Тест доступа к публичным и приватным сниппетам для авторизованного пользователя"""
        self.client.force_login(self.user)
        response = self.client.get('/snippets/list')

        assert response.status_code == 200
        snippets_list = list(response.context['page_obj'].paginator.object_list)

        # Проверяем, что видны публичные сниппеты всех пользователей
        public_snippets = [s for s in self.snippets if s.public]
        for snippet in public_snippets:
            assert snippet in snippets_list

        # Проверяем, что видны приватные сниппеты текущего пользователя
        private_own_snippets = [s for s in self.snippets if not s.public and s.user == self.user]
        for snippet in private_own_snippets:
            assert snippet in snippets_list

        # Проверяем, что НЕ видны приватные сниппеты других пользователей
        private_others_snippets = [s for s in self.snippets if not s.public and s.user != self.user]
        for snippet in private_others_snippets:
            assert snippet not in snippets_list

    def test_only_public_snippets_for_anonymous_user(self):
        """Тест доступа только к публичным сниппетам для неавторизованного пользователя"""
        response = self.client.get('/snippets/list')

        assert response.status_code == 200
        snippets_list = list(response.context['page_obj'].paginator.object_list)

        # Проверяем, что видны только публичные сниппеты
        public_snippets = [s for s in self.snippets if s.public]
        for snippet in public_snippets:
            assert snippet in snippets_list

        # Проверяем, что НЕ видны приватные сниппеты
        private_snippets = [s for s in self.snippets if not s.public]
        for snippet in private_snippets:
            assert snippet not in snippets_list

    def test_pagination(self):
        """Тест пагинации"""
        self.client.force_login(self.user)
        response = self.client.get('/snippets/list')

        assert response.status_code == 200
        assert 'page_obj' in response.context
        # Проверяем, что пагинация работает (по 5 элементов на страницу)
        assert hasattr(response.context['page_obj'], 'has_other_pages')
        assert hasattr(response.context['page_obj'], 'number')
        assert hasattr(response.context['page_obj'], 'paginator')

    def test_empty_search_results(self):
        """Тест поиска с пустыми результатами"""
        self.client.force_login(self.user)
        response = self.client.get('/snippets/list?search=NonExistentSnippet')

        assert response.status_code == 200
        assert len(response.context['page_obj']) == 0

    def test_empty_lang_filter(self):
        """Тест фильтрации по несуществующему языку"""
        self.client.force_login(self.user)
        response = self.client.get('/snippets/list?lang=nonexistent')

        assert response.status_code == 200
        assert len(response.context['page_obj']) == 0


