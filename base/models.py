from asgiref.sync import sync_to_async

from django.db import models

from base.managers import ActiveManager, DeletedManager



class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    objects = models.Manager()
    active_objects = ActiveManager()
    deleted_objects = DeletedManager()

    class Meta:
        abstract = True

    def soft_delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])

    async def asoft_delete(self, *args, **kwargs):
        return await sync_to_async(self.soft_delete)(*args, **kwargs)
