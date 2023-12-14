from asgiref.sync import sync_to_async

from django.db import models

class CustomQueryset(models.QuerySet):
    def soft_delete(self):
        return self.update(is_deleted=True)

    async def asoft_delete(self):
        return await sync_to_async(self.soft_delete)()


class BaseManager(models.Manager):
    def get_queryset(self):
        return CustomQueryset(self.model, using=self._db)


class ActiveManager(BaseManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class DeletedManager(BaseManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=True)
