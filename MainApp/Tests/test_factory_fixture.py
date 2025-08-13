import factory.django
import pytest
# from factories import UserFactory, SnippetFactory
from MainApp.models import User, Snippet, Tag,Comment
from MainApp.factories import Tag, TagFactory, CommentFactory,SnippetFactory
from .test_views import Snippet


# @pytest.fixture
# def user_factory():
#     def _create_user(username) -> User:
#
#         return UserFactory(username=username)
#     return _create_user
#
#
# # использование фабрики в тесте
# @pytest.mark.django_db
# def test_create_user2(user_factory):
#     user = user_factory("Ivan")
#     assert user.username == "Ivan"
#
#
# @pytest.fixture
# def user():
#     """Фикстура для создания пользователя"""
#     return UserFactory()
#
# @pytest.fixture
# def snippets_factory():
#     def _create_snippets(n=5, user=None):
#         return SnippetFactory.create_batch(n, user=user)
#     return _create_snippets
#
# @pytest.mark.django_db
# def test_create_snippets(snippets_factory):
#     snippets_factory()
#     snippets = Snippet.objects.all()
#     assert snippets.count() == 5
#     for snippet in snippets:
#         assert snippet.user is None
#
# @pytest.mark.django_db
# def test_create_snippets_with_user(snippets_factory, user):
#     snippets_factory(n=4, user=user)
#     snippets = Snippet.objects.all()
#     assert snippets.count() == 4
#     for snippet in snippets:
#         assert snippet.user == user

# class TagFactory(factory.django.DjangoModelFactory):
#     class Meta:
#         model = Tag
#
#     name = factory.sequence(lambda n: f"tag_{n}")

@pytest.fixture
def tag_factory():
    def _create_tag(names: list[str]):
        return [TagFactory(name=name) for name in names]
    return _create_tag

@pytest.mark.django_db
def test_create_tags(tag_factory):
    tags = tag_factory(names=["js", "basic", "oop"])
    assert len(tags) == 3
    assert [tag.name for tag in tags] == ["js", "basic", "oop"]

@pytest.fixture
def snippet():
    return SnippetFactory()

@pytest.fixture
def comment_factory():
    def _create_comment_to_snippet(snippet, n):
        return CommentFactory.create_batch(n, snippet=snippet)
    return _create_comment_to_snippet

@pytest.mark.django_db
def test_create_comments(snippet, comment_factory):
    comment_factory(snippet=snippet, n=6)

    assert Comment.objects.count() == 6
    for comment in Comment.objects.all():
        assert comment.snippet == snippet