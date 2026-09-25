from django.contrib import admin
from .models import LearningMaterial, GeneratedContent

@admin.register(LearningMaterial)
class LearningMaterialAdmin(admin.ModelAdmin):
    list_display = ('title','class_subject','material_type','teacher','is_published','created_at')
    list_filter = ('material_type','is_published','class_subject__class_level')
    search_fields = ('title','description','class_subject__subject__name')

@admin.register(GeneratedContent)
class GeneratedContentAdmin(admin.ModelAdmin):
    list_display = ('title','teacher','class_subject','status','created_at')
    list_filter = ('status','content_type')
    search_fields = ('title','topic','content')
