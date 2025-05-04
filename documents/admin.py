from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'file', 'uuid', 'file_type', 'file_size', 'status')
    list_filter = ('file',)
    search_fields = ('file', 'title')
    list_per_page = 10
