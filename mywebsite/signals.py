from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.conf import settings
from .models import TbUser

@receiver(post_migrate)
def create_superuser(sender, **kwargs):
    if not TbUser.objects.filter(is_superuser=True).exists():
        TbUser.objects.create_superuser(
            username="superuser8-25",
            password="admin123",
        )
        print("Superuser berhasil dibuat!")