from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import cloudinary.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Couple',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invite_code', models.CharField(blank=True, help_text='Share this code with your partner to join', max_length=20, unique=True)),
                ('anniversary_date', models.DateField(blank=True, help_text='When did your relationship start?', null=True)),
                ('is_ended', models.BooleanField(db_index=True, default=False, help_text='Mark when the relationship has ended (vault becomes read-only)')),
                ('ended_date', models.DateField(blank=True, help_text='Optional: when the relationship ended', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='couple_as_user1', to=settings.AUTH_USER_MODEL)),
                ('user2', models.ForeignKey(blank=True, help_text='Leave blank to generate an invite code', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='couple_as_user2', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Couple',
                'verbose_name_plural': 'Couples',
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('display_name', models.CharField(blank=True, help_text='Nickname shown to your partner (defaults to username)', max_length=50)),
                ('avatar', cloudinary.models.CloudinaryField(blank=True, help_text='Profile photo', max_length=255, null=True, verbose_name='avatar')),
                ('timezone', models.CharField(default='UTC', help_text="For showing the correct 'today' prompt", max_length=50)),
                ('notify_partner_answered', models.BooleanField(default=True, help_text='Get notified when partner answers')),
                ('wrapped_share_consent', models.BooleanField(default=False, help_text='Allow sharing Wrapped publicly')),
                ('active_couple', models.ForeignKey(blank=True, help_text='The currently selected vault/couple for this user', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='active_profiles', to='core.couple')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Prompt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(help_text='The question/prompt shown to users', max_length=500)),
                ('category', models.CharField(choices=[('wholesome', 'Wholesome'), ('lore', 'The Lore'), ('chaos', 'Chaos Mode'), ('spicy', 'Spicy'), ('grind', 'The Grind'), ('plot', 'The Plot'), ('intellectual', 'Big Brain'), ('wildcard', 'Wildcard')], db_index=True, default='wildcard', help_text='Category the prompt belongs to', max_length=20)),
                ('active_date', models.DateField(db_index=True, help_text='The specific date this prompt is shown (MM-DD used for cycling)', unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Prompt',
                'verbose_name_plural': 'Prompts',
                'ordering': ['active_date'],
            },
        ),
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text_content', models.TextField(help_text="The user's journal response")),
                ('photo', cloudinary.models.CloudinaryField(blank=True, help_text='Optional photo attachment', max_length=255, null=True, verbose_name='photo')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('word_count', models.PositiveIntegerField(db_index=True, default=0, help_text='Auto-calculated: Total words in text_content')),
                ('sentiment_score', models.FloatField(blank=True, help_text='Placeholder: -1.0 (negative) to 1.0 (positive) sentiment', null=True)),
                ('location_tag', models.CharField(blank=True, db_index=True, default='', help_text="Optional: Where was this entry written? (e.g., 'Home', 'Paris')", max_length=200)),
                ('couple', models.ForeignKey(blank=True, help_text='Which vault/couple this entry belongs to', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='entries', to='core.couple')),
                ('prompt', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='entries', to='core.prompt')),
                ('user', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='entries', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Entry',
                'verbose_name_plural': 'Entries',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='entry',
            constraint=models.UniqueConstraint(fields=('user', 'prompt', 'couple'), name='unique_user_prompt_couple_entry'),
        ),
        migrations.AddIndex(
            model_name='entry',
            index=models.Index(fields=['user', 'created_at'], name='entry_user_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='entry',
            index=models.Index(fields=['couple', 'created_at'], name='entry_couple_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='entry',
            index=models.Index(fields=['couple', 'prompt', 'user'], name='entry_couple_prompt_user_idx'),
        ),
    ]


