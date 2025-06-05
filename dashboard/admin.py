
from django.contrib import admin
from .models import Zone, Cell, UserProfile, Issue, Comment

admin.site.register(Zone)
admin.site.register(Cell)
admin.site.register(UserProfile)
admin.site.register(Issue)
admin.site.register(Comment)