"""
Kullanıcı Yönetimi Admin Paneli
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Kullanıcı sayfasında profil bilgilerini göster"""
    model = UserProfile
    can_delete = False
    verbose_name = 'Profil Bilgileri'
    verbose_name_plural = 'Profil Bilgileri'
    
    fieldsets = (
        ('👔 Meslek Bilgileri', {
            'fields': ('profession', 'profession_detail', 'company_or_institution')
        }),
        ('🎓 Eğitim Bilgileri', {
            'fields': ('education_level', 'field_of_study', 'university', 'graduation_year')
        }),
        ('📝 Biyografi', {
            'fields': ('bio',)
        }),
        ('🎯 İlgi Alanları', {
            'fields': ('interests', 'research_areas')
        }),
        ('🔗 Sosyal Medya', {
            'fields': ('website', 'linkedin', 'twitter', 'orcid', 'google_scholar'),
            'classes': ('collapse',)
        }),
        ('📊 Durum', {
            'fields': ('is_profile_complete', 'avatar_url'),
            'classes': ('collapse',)
        }),
    )


class CustomUserAdmin(UserAdmin):
    """Özelleştirilmiş User Admin"""
    inlines = [UserProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'profile_status', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    def profile_status(self, obj):
        try:
            if obj.profile.is_profile_complete:
                return mark_safe('<span style="color:#10b981;font-weight:bold;">✓ Tamamlandı</span>')
            return mark_safe('<span style="color:#f59e0b;">⏳ Eksik</span>')
        except UserProfile.DoesNotExist:
            return mark_safe('<span style="color:#ef4444;">✗ Profil Yok</span>')
    profile_status.short_description = 'Profil Durumu'


# Default User admin'i değiştir
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Kullanıcı Profili Admin"""
    list_display = ['user', 'profession', 'field_of_study', 'is_profile_complete', 'created_at']
    list_filter = ['is_profile_complete', 'profession', 'education_level', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'field_of_study']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('👤 Kullanıcı', {
            'fields': ('user',)
        }),
        ('👔 Meslek Bilgileri', {
            'fields': ('profession', 'profession_detail', 'company_or_institution')
        }),
        ('🎓 Eğitim Bilgileri', {
            'fields': ('education_level', 'field_of_study', 'university', 'graduation_year')
        }),
        ('📝 Biyografi', {
            'fields': ('bio',)
        }),
        ('🎯 İlgi Alanları', {
            'fields': ('interests', 'research_areas')
        }),
        ('🔗 Sosyal Medya', {
            'fields': ('website', 'linkedin', 'twitter', 'orcid', 'google_scholar')
        }),
        ('📊 Durum', {
            'fields': ('is_profile_complete', 'avatar_url')
        }),
        ('📅 Sistem', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
