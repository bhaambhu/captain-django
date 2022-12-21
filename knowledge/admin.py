from django.contrib import admin
from . import models
from mptt.admin import DraggableMPTTAdmin

admin.site.register(
  models.Subject,
  DraggableMPTTAdmin,
  list_display=(
    'tree_actions',
    'indented_title',
  ),
  list_display_links=(
    'indented_title',
  ),
)

# @admin.register(models.Topic)
# class AuthorAdmin(admin.ModelAdmin):
#     list_display = ('title', 'id', 'author', 'parent', 'slug', 'status')


admin.site.register(models.Concept)
admin.site.register(models.Topic)
admin.site.register(models.Path)
admin.site.register(models.PathTopicSequence)
admin.site.register(models.TopicProgress)