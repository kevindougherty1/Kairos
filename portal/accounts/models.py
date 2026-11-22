from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Kairos user. Custom from the start so roles (coach / client) can be added later
    without swapping the user model mid-project. The role field arrives with the data model."""
