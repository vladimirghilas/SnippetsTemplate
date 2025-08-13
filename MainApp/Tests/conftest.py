import pytest
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from MainApp.factories import UserFactory

@pytest.fixture
def browser():
    options = Options()
    options.add_argument("--headless")  # opțional
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    yield driver
    driver.quit()

@pytest.fixture
def user():
    """Фикстура для создания пользователя"""
    return UserFactory()


@pytest.fixture
def authenticated_client(client, user):
    """Фикстура для создания аутентифицированного клиента"""
    client.force_login(user)
    return client, user