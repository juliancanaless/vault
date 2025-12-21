"""
The Vault - Views
=================

Core journal functionality with three states:
1. Unanswered - Clean input form
2. Waiting - User answered, partner hasn't (blurred partner card)
3. Unlocked - Both answered, full reveal

Plus: Couple pairing via invite codes
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods

from .models import Prompt, Entry, Couple, Spark, SparkCategory
from .forms import EntryForm, ProfileForm, CoupleSettingsForm
from .analytics import CoupleAnalytics


# =============================================================================
# HOME / DASHBOARD
# =============================================================================

def home(request):
    """
    Public landing page for logged-out users and a simple dashboard for logged-in users.
    This prevents the app from feeling "hidden behind URLs" and gives clear navigation.
    """
    if not request.user.is_authenticated:
        return render(request, 'home.html')

    user = request.user
    couples = Couple.get_couples_for_user(user)

    active = getattr(user, 'profile', None) and user.profile.active_couple
    if active and not active.includes_user(user):
        active = None

    # Determine whether the user can journal right now
    can_journal = bool(active and active.user2 and not getattr(active, 'is_ended', False))

    context = {
        'couples': couples,
        'active_couple': active,
        'can_journal': can_journal,
        'needs_vault': not bool(active),
        'needs_partner': bool(active and not active.user2),
        'vault_read_only': bool(active and getattr(active, 'is_ended', False)),
        'is_staff': bool(getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False)),
        'active_tab': 'home',
    }
    return render(request, 'home.html', context)


# =============================================================================
# AUTHENTICATION
# =============================================================================

def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect('daily_journal')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('daily_journal')
    else:
        form = AuthenticationForm()
    
    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    """Handle user logout."""
    logout(request)
    return redirect('login')


def register_view(request):
    """Handle user registration, then redirect to couple setup."""
    if request.user.is_authenticated:
        return redirect('daily_journal')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome to The Vault!')
            # Redirect to couple setup instead of journal
            return redirect('couple_setup')
    else:
        form = UserCreationForm()
    
    return render(request, 'auth/register.html', {'form': form})


# =============================================================================
# COUPLE PAIRING
# =============================================================================

@login_required
def couple_setup(request):
    """
    Setup page for pairing with a partner (and managing vaults).
    
    Options:
    1. Pick an existing vault (if you have multiple)
    2. Create a new vault (get invite code to share)
    3. Join existing vault (enter partner's invite code)
    """
    user = request.user
    couples = Couple.get_couples_for_user(user)

    # Resolve active vault selection
    active = user.profile.active_couple
    if active and not active.includes_user(user):
        active = None

    if active and not active.user2:
        # Active vault exists, waiting for partner
        return render(
            request,
            'couple/waiting.html',
            {'couple': active, 'couples': couples, 'active_couple': active, 'active_tab': 'home'}
        )

    return render(
        request,
        'couple/setup.html',
        {'couples': couples, 'active_couple': active, 'needs_vault_selection': couples.exists() and not active, 'active_tab': 'home'}
    )


@login_required
def create_vault(request):
    """Create a new vault (couple) and set it as active."""
    # Create new couple
    couple = Couple.objects.create(user1=request.user)
    request.user.profile.active_couple = couple
    request.user.profile.save(update_fields=['active_couple'])
    messages.success(request, 'Couple created! Share your invite code with your partner.')
    
    return redirect('couple_setup')


@login_required
def join_vault(request):
    """Join an existing vault (couple) using an invite code, and set it as active."""
    if request.method != 'POST':
        return redirect('couple_setup')
    
    invite_code = request.POST.get('invite_code', '').strip()
    
    if not invite_code:
        messages.error(request, 'Please enter an invite code.')
        return redirect('couple_setup')
    
    # Try to join
    couple, error = Couple.join_with_code(request.user, invite_code)
    
    if error:
        messages.error(request, error)
        return redirect('couple_setup')
    
    request.user.profile.active_couple = couple
    request.user.profile.save(update_fields=['active_couple'])
    messages.success(request, f'You are now connected with {couple.user1.username}! 💕')
    return redirect('daily_journal')


@login_required
@require_http_methods(['POST'])
def select_vault(request, couple_id):
    """Switch the currently active vault/couple for the user."""
    user = request.user
    couple = Couple.objects.filter(id=couple_id).first()

    if not couple or not couple.includes_user(user):
        messages.error(request, "That vault doesn't exist or you don't have access to it.")
        return redirect('couple_setup')

    user.profile.active_couple = couple
    user.profile.save(update_fields=['active_couple'])
    messages.success(request, 'Vault switched.')
    return redirect('daily_journal')

# =============================================================================
# DAILY JOURNAL
# =============================================================================

@login_required
def daily_journal(request):
    """
    The main journal view with three states:
    
    State 1 (Unanswered): 
        - User hasn't answered today's prompt
        - Show clean, spacious input form
    
    State 2 (Waiting):
        - User answered, partner hasn't
        - Show user's entry
        - Show partner's card with blur effect and lock icon
    
    State 3 (Unlocked):
        - Both answered
        - Show both entries revealed
    """
    couple = request.user.profile.active_couple

    if not couple or not couple.includes_user(request.user):
        return redirect('couple_setup')

    if getattr(couple, 'is_ended', False):
        messages.info(request, 'This vault is read-only because the relationship is marked as ended.')
        return redirect('entry_history')

    if not couple.user2:
        return redirect('couple_setup')
    
    # Get partner for display
    partner = couple.get_partner(request.user)
    
    # Get today's prompt
    prompt = Prompt.get_todays_prompt()
    
    if not prompt:
        # No prompt for today - show empty state
        return render(request, 'journal/no_prompt.html', {'partner': partner, 'active_tab': 'journal'})
    
    # Get user's entry for this prompt (if exists)
    user_entry = Entry.get_user_entry_for_prompt(request.user, prompt, couple)
    
    # Get partner's entry (if exists)
    partner_entry = Entry.get_partner_entry_for_prompt(request.user, prompt, couple)
    
    # Determine state
    if not user_entry:
        state = 'unanswered'
        form = EntryForm()
    elif user_entry and not partner_entry:
        state = 'waiting'
        form = None
    else:
        state = 'unlocked'
        form = None
    
    context = {
        'prompt': prompt,
        'state': state,
        'user_entry': user_entry,
        'partner_entry': partner_entry,
        'partner': partner,
        'couple': couple,
        'form': form,
        'active_tab': 'journal',
    }
    
    return render(request, 'journal/daily.html', context)


@login_required
@require_http_methods(['POST'])
def submit_entry(request):
    """
    Handle journal entry submission via HTMX.
    Returns updated journal state partial.
    """
    prompt = Prompt.get_todays_prompt()
    
    couple = request.user.profile.active_couple
    if not couple or not couple.includes_user(request.user) or not couple.user2:
        return HttpResponse('<p class="text-red-500">Please connect to a partner first.</p>')
    if getattr(couple, 'is_ended', False):
        return HttpResponse('<p class="text-amber-500">This vault is read-only.</p>')

    if not prompt:
        return HttpResponse('<p class="text-red-500">No prompt available today.</p>')
    
    # Check if user already answered
    existing_entry = Entry.get_user_entry_for_prompt(request.user, prompt, couple)
    if existing_entry:
        return HttpResponse('<p class="text-amber-500">You already answered today!</p>')
    
    form = EntryForm(request.POST, request.FILES)
    
    if form.is_valid():
        entry = form.save(commit=False)
        entry.user = request.user
        entry.prompt = prompt
        entry.couple = couple
        entry.save()
        
        # Get partner's entry to determine new state
        partner_entry = Entry.get_partner_entry_for_prompt(request.user, prompt, couple)
        
        if partner_entry:
            state = 'unlocked'
        else:
            state = 'waiting'
        
        context = {
            'prompt': prompt,
            'state': state,
            'user_entry': entry,
            'partner_entry': partner_entry,
            'couple': couple,
        }
        
        return render(request, 'journal/partials/entry_state.html', context)
    
    # Form invalid - return form with errors
    context = {
        'prompt': prompt,
        'form': form,
        'state': 'unanswered',
    }
    return render(request, 'journal/partials/entry_form.html', context)


@login_required
def check_partner_status(request):
    """
    HTMX endpoint to check if partner has answered.
    Used for polling to auto-unlock when partner responds.
    """
    prompt = Prompt.get_todays_prompt()
    
    if not prompt:
        return HttpResponse('')

    couple = request.user.profile.active_couple
    if not couple or not couple.includes_user(request.user):
        return HttpResponse('')
    if getattr(couple, 'is_ended', False):
        return HttpResponse('')
    
    user_entry = Entry.get_user_entry_for_prompt(request.user, prompt, couple)
    partner_entry = Entry.get_partner_entry_for_prompt(request.user, prompt, couple)
    
    if user_entry and partner_entry:
        # Both answered - return unlocked state
        context = {
            'prompt': prompt,
            'state': 'unlocked',
            'user_entry': user_entry,
            'partner_entry': partner_entry,
            'couple': couple,
        }
        return render(request, 'journal/partials/entry_state.html', context)
    
    # Partner hasn't answered yet - return empty (no update needed)
    return HttpResponse('')


# =============================================================================
# PROFILE & SETTINGS
# =============================================================================

@login_required
def settings_view(request):
    """User settings page - profile and couple settings."""
    couples = Couple.get_couples_for_user(request.user)
    couple = request.user.profile.active_couple
    if couple and not couple.includes_user(request.user):
        couple = None
    partner = couple.get_partner(request.user) if couple else None
    
    # Profile form
    if request.method == 'POST' and 'profile_submit' in request.POST:
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if profile_form.is_valid():
            try:
                profile_form.save()
                messages.success(request, 'Profile updated!')
                return redirect('settings')
            except Exception as e:
                # Cloudinary upload errors occur during model save (CloudinaryField.pre_save)
                messages.error(request, 'Profile update failed. Please try again.')
        else:
            messages.error(request, 'Could not update profile. Please fix the highlighted fields and try again.')
    else:
        profile_form = ProfileForm(instance=request.user.profile)
    
    # Couple settings form
    if request.method == 'POST' and 'couple_submit' in request.POST:
        couple_form = CoupleSettingsForm(request.POST, instance=couple)
        if couple_form.is_valid():
            couple_form.save()
            messages.success(request, 'Couple settings updated!')
            return redirect('settings')
        else:
            messages.error(request, 'Could not update relationship settings. Please fix the highlighted fields and try again.')
    else:
        couple_form = CoupleSettingsForm(instance=couple) if couple else None
    
    context = {
        'profile_form': profile_form,
        'couple_form': couple_form,
        'couple': couple,
        'partner': partner,
        'couples': couples,
        'active_couple': couple,
        'active_tab': 'settings',
    }
    
    return render(request, 'settings/index.html', context)


# =============================================================================
# ENTRY HISTORY
# =============================================================================

@login_required
def entry_history(request):
    """View past journal entries."""
    couple = request.user.profile.active_couple
    
    if not couple or not couple.includes_user(request.user):
        return redirect('couple_setup')
    
    partner = couple.get_partner(request.user)
    
    # Get all entries for this user, with related prompt data
    user_entries = Entry.objects.filter(
        user=request.user,
        couple=couple
    ).select_related('prompt').order_by('-prompt__active_date')
    
    # Build list of entries with partner's entry (if unlocked)
    entries_with_partner = []
    for entry in user_entries:
        partner_entry = Entry.objects.filter(
            user=partner,
            prompt=entry.prompt,
            couple=couple
        ).first()
        
        entries_with_partner.append({
            'prompt': entry.prompt,
            'user_entry': entry,
            'partner_entry': partner_entry,
            'unlocked': partner_entry is not None,
        })
    
    # Group by month for display
    from collections import defaultdict
    entries_by_month = defaultdict(list)
    for item in entries_with_partner:
        month_key = item['prompt'].active_date.strftime('%B %Y')
        entries_by_month[month_key].append(item)
    
    context = {
        'entries_by_month': dict(entries_by_month),
        'partner': partner,
        'total_entries': len(entries_with_partner),
        'active_tab': 'history',
    }
    
    return render(request, 'history/index.html', context)


@login_required
def entry_detail(request, entry_id):
    """View a single past entry in detail."""
    couple = request.user.profile.active_couple
    
    if not couple or not couple.includes_user(request.user):
        return redirect('couple_setup')
    
    partner = couple.get_partner(request.user)
    
    # Get user's entry
    try:
        user_entry = Entry.objects.select_related('prompt').get(
            id=entry_id,
            user=request.user,
            couple=couple
        )
    except Entry.DoesNotExist:
        messages.error(request, 'Entry not found.')
        return redirect('entry_history')
    
    # Get partner's entry for same prompt
    partner_entry = Entry.objects.filter(
        user=partner,
        prompt=user_entry.prompt,
        couple=couple
    ).first()
    
    context = {
        'prompt': user_entry.prompt,
        'user_entry': user_entry,
        'partner_entry': partner_entry,
        'partner': partner,
        'unlocked': partner_entry is not None,
        'active_tab': 'history',
    }
    
    return render(request, 'history/detail.html', context)


# =============================================================================
# WRAPPED - YEAR IN REVIEW
# =============================================================================

@login_required
def wrapped_view(request, year=None):
    """
    The Vault Wrapped - Year in Review.
    Shows couple analytics for the specified year.
    """
    from django.utils import timezone
    
    couple = request.user.profile.active_couple
    
    if not couple or not couple.includes_user(request.user) or not couple.user2:
        return redirect('couple_setup')
    
    partner = couple.get_partner(request.user)
    
    # Default to current year
    if year is None:
        year = timezone.now().year
    
    # Generate analytics
    analytics = CoupleAnalytics(couple, year)
    wrapped_data = analytics.generate_wrapped_data()
    
    # Add couple info
    wrapped_data['couple'] = couple
    wrapped_data['partner'] = partner
    wrapped_data['user'] = request.user
    
    # Calculate relationship duration if anniversary is set
    if couple.anniversary_date:
        from datetime import date
        delta = date(year, 12, 31) - couple.anniversary_date
        wrapped_data['years_together'] = delta.days // 365
        wrapped_data['days_together'] = delta.days
    
    context = {
        'wrapped': wrapped_data,
        'year': year,
        'active_tab': 'home',
    }
    
    return render(request, 'wrapped/index.html', context)


# =============================================================================
# SPARK - Ideas for couples to explore together
# =============================================================================

@login_required
def spark_index(request):
    """
    Spark landing page - shows category cards to choose from.
    This is the 'together mode' counterpart to the async daily journal.
    """
    # Get counts per category for display
    category_counts = Spark.get_category_counts()
    
    categories = [
        {
            'id': SparkCategory.DATE,
            'name': 'Date Ideas',
            'description': 'Activities to do together',
            'icon': 'heart',
            'count': category_counts.get(SparkCategory.DATE, 0),
            'color': 'rose',
        },
        {
            'id': SparkCategory.CONVO,
            'name': 'Conversation',
            'description': 'Questions for deeper talks',
            'icon': 'chat',
            'count': category_counts.get(SparkCategory.CONVO, 0),
            'color': 'violet',
        },
        {
            'id': SparkCategory.WYR,
            'name': 'Would You Rather',
            'description': 'Quick fun decisions',
            'icon': 'scale',
            'count': category_counts.get(SparkCategory.WYR, 0),
            'color': 'amber',
        },
        {
            'id': SparkCategory.GAME,
            'name': 'Quick Games',
            'description': 'Mini activities & challenges',
            'icon': 'puzzle',
            'count': category_counts.get(SparkCategory.GAME, 0),
            'color': 'emerald',
        },
    ]
    
    context = {
        'categories': categories,
        'total_sparks': sum(category_counts.values()),
        'active_tab': 'spark',
    }
    
    return render(request, 'spark/index.html', context)


@login_required
def spark_card(request, category):
    """
    Show a random spark card from the given category.
    Used both for initial page load and HTMX refreshes.
    """
    # Validate category
    valid_categories = [c[0] for c in SparkCategory.choices]
    if category not in valid_categories:
        return redirect('spark_index')
    
    # Get optional vibe filter from query params
    vibe = request.GET.get('vibe')
    
    # Get a random spark
    spark = Spark.get_random(category=category, vibe=vibe)
    
    # Category display info
    category_info = {
        SparkCategory.DATE: {'name': 'Date Ideas', 'color': 'rose'},
        SparkCategory.CONVO: {'name': 'Conversation', 'color': 'violet'},
        SparkCategory.WYR: {'name': 'Would You Rather', 'color': 'amber'},
        SparkCategory.GAME: {'name': 'Quick Games', 'color': 'emerald'},
    }
    
    context = {
        'spark': spark,
        'category': category,
        'category_info': category_info.get(category, {}),
        'vibe': vibe,
        'active_tab': 'spark',
    }
    
    # If HTMX request, return just the card partial
    if request.headers.get('HX-Request'):
        return render(request, 'spark/partials/card.html', context)
    
    return render(request, 'spark/card.html', context)


@login_required
def spark_next(request, category):
    """
    HTMX endpoint to get the next random spark card.
    Returns just the card partial for swapping.
    """
    vibe = request.GET.get('vibe')
    spark = Spark.get_random(category=category, vibe=vibe)
    
    category_info = {
        SparkCategory.DATE: {'name': 'Date Ideas', 'color': 'rose'},
        SparkCategory.CONVO: {'name': 'Conversation', 'color': 'violet'},
        SparkCategory.WYR: {'name': 'Would You Rather', 'color': 'amber'},
        SparkCategory.GAME: {'name': 'Quick Games', 'color': 'emerald'},
    }
    
    context = {
        'spark': spark,
        'category': category,
        'category_info': category_info.get(category, {}),
        'vibe': vibe,
    }
    
    return render(request, 'spark/partials/card.html', context)
