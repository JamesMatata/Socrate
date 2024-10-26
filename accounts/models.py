from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import CustomUserManager
from django.utils.translation import gettext as _


class CustomUser(AbstractUser):
    is_admin = models.BooleanField('Is Admin', default=False)
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name',)

    objects = CustomUserManager()

    def __str__(self):
        return self.email
