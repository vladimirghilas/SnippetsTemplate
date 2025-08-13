from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Получает список зарегистрированных пользователей"

    def add_arguments(self, parser):
        parser.add_argument('--max_users',
                            type=int,
                            help='...')

    def handle(self, *args, **options):
        print("Получает зарегистрированных пользователей")
        max_users = options.get('max_users')
        users = User.objects.all()[0:max_users]

        for user in users:
            self.stdout.write(f"get_users: {user}")