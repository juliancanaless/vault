"""
The Vault - Admin Configuration

Admin interface for managing prompts and viewing entries.
Optimized for content management and analytics visibility.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import Prompt, Entry, Couple, Profile, Spark

User = get_user_model()


# Inline Profile in User admin
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


# Extend the User admin to show Profile
class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]
    list_display = ['username', 'email', 'get_display_name', 'is_staff']
    
    def get_display_name(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.name
        return obj.username
    get_display_name.short_description = 'Display Name'


# Re-register User with our custom admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Couple)
class CoupleAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'invite_code', 'is_paired', 'is_ended', 'ended_date', 'anniversary_date', 'created_at']
    list_filter = ['is_ended', 'created_at']
    search_fields = ['user1__username', 'user2__username', 'invite_code']
    readonly_fields = ['invite_code', 'created_at']
    
    def is_paired(self, obj):
        return obj.user2 is not None
    is_paired.boolean = True
    is_paired.short_description = 'Paired'


@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = ['active_date', 'category', 'text_short', 'entry_count']
    list_filter = ['category', 'active_date']
    search_fields = ['text']
    ordering = ['active_date']
    date_hierarchy = 'active_date'
    
    def text_short(self, obj):
        return obj.text[:60] + '...' if len(obj.text) > 60 else obj.text
    text_short.short_description = 'Prompt'
    
    def entry_count(self, obj):
        return obj.entries.count()
    entry_count.short_description = 'Responses'


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'prompt_date', 'category', 'word_count', 'location_tag', 'created_at']
    list_filter = ['prompt__category', 'created_at', 'location_tag']
    search_fields = ['text_content', 'user__username', 'location_tag']
    readonly_fields = ['word_count', 'created_at', 'updated_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def prompt_date(self, obj):
        return obj.prompt.active_date
    prompt_date.short_description = 'Prompt Date'
    
    def category(self, obj):
        return obj.prompt.get_category_display()
    category.short_description = 'Category'


@admin.register(Spark)
class SparkAdmin(admin.ModelAdmin):
    list_display = ['text_short', 'category', 'vibe', 'has_option_b', 'created_at']
    list_filter = ['category', 'vibe', 'created_at']
    search_fields = ['text', 'option_b', 'subtitle']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('text', 'category', 'vibe')
        }),
        ('Would You Rather Options', {
            'fields': ('option_b',),
            'classes': ('collapse',),
            'description': 'Only used for "Would You Rather" category sparks'
        }),
        ('Optional', {
            'fields': ('subtitle',),
            'classes': ('collapse',)
        }),
    )
    
    def text_short(self, obj):
        return obj.text[:60] + '...' if len(obj.text) > 60 else obj.text
    text_short.short_description = 'Text'
    
    def has_option_b(self, obj):
        return bool(obj.option_b)
    has_option_b.boolean = True
    has_option_b.short_description = 'Has Option B'

