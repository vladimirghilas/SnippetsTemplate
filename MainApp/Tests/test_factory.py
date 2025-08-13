from MainApp.factories import *
import pytest
from MainApp.models import User

@pytest.mark.django_db
def test_task():
    UserFactory(username="Alice")
    user = User.objects.get(username="Alice")

    assert user.username== 'Alice'

