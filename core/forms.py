"""
The Vault - Forms
"""

from django import forms
from .models import Entry, Profile, Couple


class EntryForm(forms.ModelForm):
    """Form for submitting journal entries."""
    
    class Meta:
        model = Entry
        fields = ['text_content', 'photo', 'location_tag']
        widgets = {
            'text_content': forms.Textarea(attrs={
                'placeholder': 'Write your thoughts...',
                'rows': 6,
                'class': 'w-full px-4 py-3 text-lg font-serif text-stone-800 bg-transparent border-0 resize-none focus:ring-0 focus:outline-none placeholder-stone-400',
            }),
            'location_tag': forms.TextInput(attrs={
                'placeholder': 'Where are you? (optional)',
                'class': 'w-full px-4 py-2 text-sm text-stone-600 bg-transparent border-0 focus:ring-0 focus:outline-none placeholder-stone-400',
            }),
            'photo': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*',
            }),
        }
        labels = {
            'text_content': '',
            'photo': '',
            'location_tag': '',
        }


class ProfileForm(forms.ModelForm):
    """Form for editing user profile settings."""
    
    class Meta:
        model = Profile
        fields = ['display_name', 'avatar', 'timezone', 'notify_partner_answered']
        widgets = {
            'display_name': forms.TextInput(attrs={
                'placeholder': 'How should your partner see you?',
                'class': 'w-full px-4 py-3 text-stone-800 bg-stone-50 border border-stone-200 rounded-xl focus:ring-2 focus:ring-vault-500 focus:border-vault-500 transition-colors',
            }),
            'timezone': forms.Select(attrs={
                'class': 'w-full px-4 py-3 text-stone-800 bg-stone-50 border border-stone-200 rounded-xl focus:ring-2 focus:ring-vault-500 focus:border-vault-500 transition-colors',
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'sr-only',
                'accept': 'image/*',
            }),
            'notify_partner_answered': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-vault-600 border-stone-300 rounded focus:ring-vault-500',
            }),
        }
        labels = {
            'display_name': 'Display Name',
            'avatar': 'Profile Photo',
            'timezone': 'Your Timezone',
            'notify_partner_answered': 'Notify me when my partner answers',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Common timezone choices
        self.fields['timezone'].widget = forms.Select(
            choices=[
                ('UTC', 'UTC'),
                ('America/New_York', 'Eastern Time (US)'),
                ('America/Chicago', 'Central Time (US)'),
                ('America/Denver', 'Mountain Time (US)'),
                ('America/Los_Angeles', 'Pacific Time (US)'),
                ('America/Phoenix', 'Arizona (US)'),
                ('America/Anchorage', 'Alaska (US)'),
                ('Pacific/Honolulu', 'Hawaii (US)'),
                ('Europe/London', 'London (UK)'),
                ('Europe/Paris', 'Paris (Europe)'),
                ('Europe/Berlin', 'Berlin (Europe)'),
                ('Asia/Tokyo', 'Tokyo (Japan)'),
                ('Asia/Shanghai', 'Shanghai (China)'),
                ('Asia/Singapore', 'Singapore'),
                ('Australia/Sydney', 'Sydney (Australia)'),
            ],
            attrs={
                'class': 'w-full px-4 py-3 text-stone-800 bg-stone-50 border border-stone-200 rounded-xl focus:ring-2 focus:ring-vault-500 focus:border-vault-500 transition-colors',
            }
        )


class CoupleSettingsForm(forms.ModelForm):
    """Form for editing couple settings (anniversary, etc.)."""
    
    class Meta:
        model = Couple
        fields = ['anniversary_date', 'is_ended', 'ended_date']
        widgets = {
            'anniversary_date': forms.DateInput(attrs={
                'type': 'date',
                # These date inputs are rendered inside a styled wrapper in the template.
                # Keep the input itself "unstyled" (transparent + no border) to avoid
                # mobile engines rendering a wider native control.
                'class': 'block w-full max-w-full min-w-0 box-border bg-transparent border-0 p-0 m-0 text-sm text-stone-800 focus:ring-0 focus:outline-none',
            }),
            'ended_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'block w-full max-w-full min-w-0 box-border bg-transparent border-0 p-0 m-0 text-sm text-stone-800 focus:ring-0 focus:outline-none',
            }),
            'is_ended': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-vault-600 border-stone-300 rounded focus:ring-vault-500',
                'id': 'id_is_ended',
                'onchange': 'confirmEndRelationship(event)',
            }),
        }
        labels = {
            'anniversary_date': 'When did your relationship start?',
            'is_ended': 'This relationship has ended',
            'ended_date': 'When did it end?',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If relationship is ended, disable the checkbox (use reactivation button instead)
        if self.instance and self.instance.is_ended:
            self.fields['is_ended'].widget.attrs['disabled'] = True
            self.fields['is_ended'].widget.attrs['style'] = 'opacity: 0.5; cursor: not-allowed;'
