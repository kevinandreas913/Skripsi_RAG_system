from django.db import models
import uuid
from django.contrib.auth.models import make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from .utils import generate_otp, verify_otp
from django.core.mail import send_mail
from django.conf import settings

class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)  # Hash password
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, password, **extra_fields)

class TbUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)
    gmail = models.CharField(max_length=255, unique=True)
    profile = models.FileField(upload_to='profile_images/', blank=False)  
    date_joined = models.DateTimeField(auto_now_add=True)
    email_otp = models.CharField(max_length=6, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2'): #hash awalan
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
        
    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username


class TbAPI(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(TbUser, on_delete=models.PROTECT, null=False)
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='pdf_files/', blank=False)  
    api_key = models.CharField(max_length=100, unique=True, blank=False)
    language = models.CharField(max_length=100, blank=False, default="en") #id = indonesia, en = english
    toxic = models.CharField(max_length=100, blank=False, default="no") #no = tidak toxic, yes = toxic
    note = models.TextField(blank=True)
    date_joined = models.DateTimeField(auto_now_add=True, editable=False)

    def save(self, *args, **kwargs):
        # Jika belum ada API key, buat dulu
        if not self.api_key:
            self.api_key = self.generate_api_key()
        super().save(*args, **kwargs)

    def generate_api_key(self):
        import secrets
        return secrets.token_urlsafe(32)  #contoh:panjang 43 karakter = aman

    def __str__(self):
        return f"{self.user.username} - {self.api_key[:8]}..."

class TbChat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, blank=False)
    gmail = models.CharField(max_length=255, unique=True)
    phone = models.CharField(max_length=20, blank=False)
    date = models.DateTimeField(auto_now_add=True)
    questions = models.TextField(blank=False)
    feedback = models.TextField(blank=True)
    status = models.CharField(max_length=100, blank=False, default="no")

    def __str__(self):
        return f"{self.name} - {self.gmail}"


