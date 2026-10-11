from django.contrib import admin

from .models import AILog, EmailDraft

admin.site.register(AILog)
admin.site.register(EmailDraft)
