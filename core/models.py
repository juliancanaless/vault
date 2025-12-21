"""
The Vault - Data Models
=======================

These models form the "Wrapped Engine" - designed from the ground up
to support year-end analytics and relationship insights.

Key Analytics Capabilities:
- Total Words Written (per user, per couple, per year)
- Top Vibe of the Year (category distribution)
- Sentiment Trends (placeholder for future NLP)
- Places We Connected (location tagging)
- Streak tracking (consecutive days answered)
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from cloudinary.models import CloudinaryField


class Profile(models.Model):
    """
    Extends Django's User with additional fields for The Vault.
    
    Created automatically when a User is created via signals.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Display
    display_name = models.CharField(
        max_length=50,
        blank=True,
        help_text="Nickname shown to your partner (defaults to username)"
    )
    avatar = CloudinaryField(
        'avatar',
        blank=True,
        null=True,
        help_text="Profile photo"
    )
    
    # Preferences
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text="For showing the correct 'today' prompt"
    )
    
    # Notifications
    notify_partner_answered = models.BooleanField(
        default=True,
        help_text="Get notified when partner answers"
    )
    
    # Wrapped preferences
    wrapped_share_consent = models.BooleanField(
        default=False,
        help_text="Allow sharing Wrapped publicly"
    )

    # Vault selection (multi-vault support)
    # A user can belong to multiple Couples ("vaults") over time; this sets
    # which vault is currently active for journaling + viewing history.
    active_couple = models.ForeignKey(
        'Couple',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='active_profiles',
        help_text="The currently selected vault/couple for this user"
    )
    
    def __str__(self):
        return f"Profile: {self.user.username}"
    
    @property
    def name(self):
        """Returns display_name if set, otherwise username."""
        return self.display_name or self.user.username


class Couple(models.Model):
    """
    Pairs two users together as a couple.
    
    This is the core relationship model that enables:
    - Partner lookups (who is my partner?)
    - Privacy (only see your partner's entries)
    - Couple-level Wrapped analytics
    """
    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='couple_as_user1'
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='couple_as_user2',
        null=True,
        blank=True,  # Allows inviting a partner later
        help_text="Leave blank to generate an invite code"
    )
    
    # Invite system
    invite_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text="Share this code with your partner to join"
    )
    
    # Relationship metadata (fun for Wrapped!)
    anniversary_date = models.DateField(
        null=True,
        blank=True,
        help_text="When did your relationship start?"
    )

    # Relationship ended (vault can outlive the couple)
    is_ended = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Mark when the relationship has ended (vault becomes read-only)"
    )
    ended_date = models.DateField(
        null=True,
        blank=True,
        help_text="Optional: when the relationship ended"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Couple'
        verbose_name_plural = 'Couples'
    
    def __str__(self):
        if self.user2:
            return f"{self.user1.username} & {self.user2.username}"
        return f"{self.user1.username} (waiting for partner)"
    
    def save(self, *args, **kwargs):
        # Auto-generate invite code if not set
        if not self.invite_code:
            import secrets
            self.invite_code = secrets.token_urlsafe(8)
        super().save(*args, **kwargs)
    
    def get_partner(self, user):
        """Given one user, return their partner."""
        if user == self.user1:
            return self.user2
        elif user == self.user2:
            return self.user1
        return None
    
    def includes_user(self, user):
        """Check if this couple includes the given user."""
        return user == self.user1 or user == self.user2

    @classmethod
    def get_couples_for_user(cls, user):
        """Return all couples (vaults) that include this user."""
        return cls.objects.filter(
            models.Q(user1=user) | models.Q(user2=user)
        ).order_by('-created_at')
    
    @classmethod
    def get_couple_for_user(cls, user):
        """Get the couple that includes this user."""
        return cls.objects.filter(
            models.Q(user1=user) | models.Q(user2=user)
        ).first()
    
    @classmethod
    def join_with_code(cls, user, invite_code):
        """
        Join an existing couple using an invite code.
        Returns (couple, error_message).
        """
        try:
            couple = cls.objects.get(invite_code=invite_code)
        except cls.DoesNotExist:
            return None, "Invalid invite code"
        
        if couple.user2 is not None:
            return None, "This couple already has two members"
        
        if couple.user1 == user:
            return None, "You can't join your own couple"
        
        couple.user2 = user
        couple.save()
        return couple, None


class PromptCategory(models.TextChoices):
    """
    Vibe-based categories.
    These map directly to specific 'Wrapped' slides at year-end.
    """
    WHOLESOME = 'wholesome', 'Wholesome'       # Comfort, safety, cute moments
    LORE = 'lore', 'The Lore'                  # History, backstory, inside jokes
    CHAOS = 'chaos', 'Chaos Mode'              # Unhinged questions, funny hypotheticals
    SPICY = 'spicy', 'Spicy'                   # Intimacy
    GRIND = 'grind', 'The Grind'               # Career, ambition, money
    PLOT = 'plot', 'The Plot'                  # Future planning, moving the relationship forward
    INTELLECTUAL = 'intellectual', 'Big Brain' # Philosophy, deep theory, politics
    WILDCARD = 'wildcard', 'Wildcard'          # Random, daily life, unclassifiable


class Prompt(models.Model):
    """
    Daily journal prompts - one per day, cycling annually.
    
    Analytics Usage:
    - Filter by year via active_date__year
    - Category distribution for "Vibe Charts"
    - Can track which prompts generate longest responses
    """
    text = models.CharField(
        max_length=500,
        help_text="The question/prompt shown to users"
    )
    category = models.CharField(
        max_length=20,
        choices=PromptCategory.choices,
        default=PromptCategory.WILDCARD,
        db_index=True,  # Index for fast category analytics
        help_text="Category the prompt belongs to"
    )
    active_date = models.DateField(
        unique=True,
        db_index=True,  # Index for daily lookups
        help_text="The specific date this prompt is shown (MM-DD used for cycling)"
    )
    
    # Metadata for content management
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['active_date']
        verbose_name = 'Prompt'
        verbose_name_plural = 'Prompts'
    
    def __str__(self):
        return f"[{self.get_category_display()}] {self.text[:50]}..."
    
    @classmethod
    def get_todays_prompt(cls):
        """
        Get the prompt for today, matching by month and day.
        This allows prompts to cycle annually.
        """
        today = timezone.now().date()
        return cls.objects.filter(
            active_date__month=today.month,
            active_date__day=today.day
        ).first()


class Entry(models.Model):
    """
    User journal entries - the core data for "Wrapped" analytics.
    
    Analytics Fields (Auto-populated on save):
    - word_count: Used for "Total Words Written" stats
    - sentiment_score: Placeholder for future NLP sentiment analysis
    - location_tag: Used for "Places We Connected" map/stats
    
    Key Wrapped Queries:
    - Total words: Entry.objects.filter(user=u, created_at__year=2025).aggregate(Sum('word_count'))
    - Category breakdown: Entry.objects.filter(...).values('prompt__category').annotate(count=Count('id'))
    - Response frequency: Can calculate streaks from created_at dates
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='entries',
        db_index=True
    )
    prompt = models.ForeignKey(
        Prompt,
        on_delete=models.CASCADE,
        related_name='entries',
        db_index=True
    )

    # Vault relationship: which couple this entry belongs to.
    # This enables users to keep separate histories across relationships.
    couple = models.ForeignKey(
        Couple,
        on_delete=models.PROTECT,
        related_name='entries',
        db_index=True,
        null=True,
        blank=True,
        help_text="Which vault/couple this entry belongs to"
    )
    
    # Core content
    text_content = models.TextField(
        help_text="The user's journal response"
    )
    photo = CloudinaryField(
        'photo',
        blank=True,
        null=True,
        help_text="Optional photo attachment"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # =========================================================
    # WRAPPED ANALYTICS FIELDS - Auto-populated on save
    # =========================================================
    
    word_count = models.PositiveIntegerField(
        default=0,
        db_index=True,  # Index for aggregation queries
        help_text="Auto-calculated: Total words in text_content"
    )
    
    sentiment_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Placeholder: -1.0 (negative) to 1.0 (positive) sentiment"
    )
    
    location_tag = models.CharField(
        max_length=200,
        blank=True,
        default='',
        db_index=True,  # Index for location-based grouping
        help_text="Optional: Where was this entry written? (e.g., 'Home', 'Paris')"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Entry'
        verbose_name_plural = 'Entries'
        # Ensure one entry per user per prompt per vault
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'prompt', 'couple'],
                name='unique_user_prompt_couple_entry'
            )
        ]
        indexes = [
            # Composite index for common wrapped queries
            models.Index(fields=['couple', 'created_at'], name='entry_couple_created_at_idx'),
            models.Index(fields=['user', 'created_at'], name='entry_user_created_at_idx'),
            # Partner + prompt lookup within a vault
            models.Index(fields=['couple', 'prompt', 'user'], name='entry_couple_prompt_user_idx'),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.prompt.active_date}"
    
    def save(self, *args, **kwargs):
        """
        Override save to auto-calculate analytics fields.
        This ensures word_count is always accurate for Wrapped stats.
        """
        # Auto-calculate word count
        if self.text_content:
            self.word_count = len(self.text_content.split())
        else:
            self.word_count = 0
        
        super().save(*args, **kwargs)
    
    @property
    def category(self):
        """Shortcut to access the prompt's category."""
        return self.prompt.category
    
    @classmethod
    def get_user_entry_for_prompt(cls, user, prompt, couple):
        """Get a user's entry for a specific prompt within a vault, if it exists."""
        return cls.objects.filter(user=user, prompt=prompt, couple=couple).first()
    
    @classmethod
    def get_partner_entry_for_prompt(cls, user, prompt, couple):
        """
        Get the partner's entry for this prompt.
        Uses the provided Couple (vault) to find the correct partner.
        """
        if not couple or not couple.includes_user(user):
            return None

        partner = couple.get_partner(user)
        if not partner:
            return None
        
        return cls.objects.filter(user=partner, prompt=prompt, couple=couple).first()


# =========================================================
# WRAPPED ANALYTICS HELPER QUERIES
# =========================================================
# 
# These query patterns will power the year-end "Wrapped" feature:
#
# 1. Total Words Written (per user, per year):
#    Entry.objects.filter(
#        user=user, 
#        created_at__year=year
#    ).aggregate(total_words=Sum('word_count'))
#
# 2. Category Distribution ("Top Vibe"):
#    Entry.objects.filter(
#        user=user, 
#        created_at__year=year
#    ).values('prompt__category').annotate(
#        count=Count('id')
#    ).order_by('-count')
#
# 3. Monthly Activity Heatmap:
#    Entry.objects.filter(
#        user=user, 
#        created_at__year=year
#    ).annotate(
#        month=TruncMonth('created_at')
#    ).values('month').annotate(count=Count('id'))
#
# 4. Longest Entry:
#    Entry.objects.filter(
#        user=user, 
#        created_at__year=year
#    ).order_by('-word_count').first()
#
# 5. Response Rate (days answered / total days):
#    total_prompts = Prompt.objects.filter(active_date__year=year).count()
#    answered = Entry.objects.filter(user=user, created_at__year=year).count()
#    rate = answered / total_prompts
#
# 6. Places We Connected:
#    Entry.objects.filter(
#        user=user, 
#        created_at__year=year,
#        location_tag__isnull=False
#    ).exclude(location_tag='').values('location_tag').annotate(
#        count=Count('id')
#    ).order_by('-count')


# =========================================================
# SPARK - Ideas for couples to explore together
# =========================================================

class SparkCategory(models.TextChoices):
    """
    Categories for Spark content - activities and ideas for couples.
    """
    DATE = 'date', 'Date Idea'           # Activities to do together
    CONVO = 'convo', 'Conversation'       # Deeper questions for in-person moments
    WYR = 'wyr', 'Would You Rather'       # Quick fun decisions to debate
    GAME = 'game', 'Quick Game'           # Mini-games, challenges, activities


class Spark(models.Model):
    """
    Ideas and activities for couples to explore together in-person.
    
    Unlike daily prompts (async, reflective), Sparks are meant for
    live moments when you're together - date nights, car rides,
    waiting for food, lazy Sundays.
    """
    text = models.TextField(
        help_text="The main content/question/idea"
    )
    category = models.CharField(
        max_length=20,
        choices=SparkCategory.choices,
        db_index=True,
        help_text="Type of spark"
    )
    
    # For "Would You Rather" - the second option
    option_b = models.TextField(
        blank=True,
        default='',
        help_text="For WYR: the second option (leave blank for other categories)"
    )
    
    # Reuse the same vibe system as prompts for filtering by mood
    vibe = models.CharField(
        max_length=20,
        choices=PromptCategory.choices,
        default=PromptCategory.WILDCARD,
        db_index=True,
        help_text="Mood/tone of this spark (wholesome, spicy, chaos, etc.)"
    )
    
    # Optional: extra context or instructions
    subtitle = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text="Optional brief subtitle or instruction"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Spark'
        verbose_name_plural = 'Sparks'
    
    def __str__(self):
        return f"[{self.get_category_display()}] {self.text[:50]}..."
    
    @classmethod
    def get_random(cls, category=None, vibe=None):
        """Get a random spark, optionally filtered by category and/or vibe."""
        qs = cls.objects.all()
        if category:
            qs = qs.filter(category=category)
        if vibe:
            qs = qs.filter(vibe=vibe)
        return qs.order_by('?').first()
    
    @classmethod
    def get_category_counts(cls):
        """Get count of sparks per category for display."""
        from django.db.models import Count
        return dict(
            cls.objects.values('category').annotate(
                count=Count('id')
            ).values_list('category', 'count')
        )

