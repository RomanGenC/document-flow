from django.db import models
from django.contrib.auth import get_user_model
import uuid
import os

User = get_user_model()


def document_upload_to(instance, filename):
    ext = filename.split('.')[-1]
    new_filename = f"{instance.title.replace(' ', '_')}.{ext}"
    return os.path.join('documents', new_filename)


class Document(models.Model):
    ACCESS_LEVELS = [
        ('private', 'Приватный'),
        ('public_read', 'Публичное чтение'),
        ('public_edit', 'Публичное редактирование'),
    ]
    FILE_TYPES = [
        ('pdf', 'PDF'),
        ('docx', 'DOCX'),
        ('xlsx', 'XLSX'),
        ('jpg', 'JPG'),
        ('png', 'PNG'),
    ]
    FILE_STATUSES = [
        ('draft', 'Черновик'),
        ('in_review', 'На согласовании'),
        ('approved', 'Одобрен'),
        ('archived', 'Архивирован'),
        ('deleted', 'Удален'),
    ]

    file = models.FileField(upload_to=document_upload_to)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_documents'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    file_size = models.PositiveIntegerField()
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=FILE_STATUSES, default='draft')
    default_access = models.CharField(
        max_length=20,
        choices=ACCESS_LEVELS,
        default='private'
    )
    encryption_key = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['uuid']),
            models.Index(fields=['owner']),
            models.Index(fields=['status']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} (v{self.version})"


class DocumentAccess(models.Model):
    PERMISSION_CHOICES = [
        ('view', 'Просмотр'),
        ('edit', 'Редактирование'),
        ('comment', 'Комментирование'),
    ]
    ACCESS_LEVELS = [
        ('private', 'Приватный'),
        ('public_read', 'Публичное чтение'),
        ('public_edit', 'Публичное редактирование'),
    ]

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='accesses',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='document_accesses',
    )
    permissions = models.CharField(
        max_length=20,
        choices=ACCESS_LEVELS,
        default='private',
    )
    granted_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='granted_accesses',
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('document', 'user')
        indexes = [
            models.Index(fields=['document', 'user']),
            models.Index(fields=['expires_at']),
        ]
