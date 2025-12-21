"""
Management command to seed the database with initial Prompt content.

Usage:
    python manage.py seed_prompts
    python manage.py seed_prompts --clear  # Clear existing prompts first
"""

from datetime import date, timedelta
from django.core.management.base import BaseCommand
from core.models import Prompt, PromptCategory


class Command(BaseCommand):
    help = 'Seeds the database with initial daily prompts for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing prompts before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted_count = Prompt.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing prompts'))

        prompts_data = self.get_prompt_data()
        
        created_count = 0
        for prompt_data in prompts_data:
            prompt, created = Prompt.objects.get_or_create(
                active_date=prompt_data['active_date'],
                defaults={
                    'text': prompt_data['text'],
                    'category': prompt_data.get('category', PromptCategory.WILDCARD),
                }
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Successfully seeded {created_count} new prompts (total: {Prompt.objects.count()})'
        ))

    def get_prompt_data(self):
        """Return list of prompt data dictionaries."""
        # Start from today and create prompts for the next 30 days
        today = date.today()
        
        prompts = [
            # Wholesome
            {
                'text': 'What\'s one small thing I did recently that made you smile?',
                'category': PromptCategory.WHOLESOME,
            },
            {
                'text': 'Describe your perfect lazy Sunday with me.',
                'category': PromptCategory.WHOLESOME,
            },
            {
                'text': 'What\'s a song that reminds you of us?',
                'category': PromptCategory.WHOLESOME,
            },
            {
                'text': 'What comfort food should we make together this week?',
                'category': PromptCategory.WHOLESOME,
            },
            # Lore
            {
                'text': 'What\'s your favorite inside joke of ours and how did it start?',
                'category': PromptCategory.LORE,
            },
            {
                'text': 'What moment made you realize we were going to work?',
                'category': PromptCategory.LORE,
            },
            {
                'text': 'What\'s a childhood memory you haven\'t told me yet?',
                'category': PromptCategory.LORE,
            },
            # Chaos
            {
                'text': 'If we had to go on a spontaneous road trip right now, where would we go?',
                'category': PromptCategory.CHAOS,
            },
            {
                'text': 'What\'s the most unhinged purchase you\'d make if you won the lottery?',
                'category': PromptCategory.CHAOS,
            },
            {
                'text': 'If we were in a heist movie, what would our roles be?',
                'category': PromptCategory.CHAOS,
            },
            # Spicy
            {
                'text': 'What outfit of mine drives you crazy (in a good way)?',
                'category': PromptCategory.SPICY,
            },
            {
                'text': 'Describe a perfect date night — no budget, no limits.',
                'category': PromptCategory.SPICY,
            },
            # Grind
            {
                'text': 'What\'s one goal you\'re working toward that I could support better?',
                'category': PromptCategory.GRIND,
            },
            {
                'text': 'Where do you want to be career-wise in 5 years?',
                'category': PromptCategory.GRIND,
            },
            # Plot
            {
                'text': 'What\'s somewhere you\'ve always wanted to travel together?',
                'category': PromptCategory.PLOT,
            },
            {
                'text': 'What\'s a tradition you\'d like us to start?',
                'category': PromptCategory.PLOT,
            },
            {
                'text': 'If we could live anywhere in the world, where would it be?',
                'category': PromptCategory.PLOT,
            },
            # Intellectual
            {
                'text': 'What\'s a belief you\'ve completely changed your mind about over the years?',
                'category': PromptCategory.INTELLECTUAL,
            },
            {
                'text': 'If you could have dinner with anyone in history, who and why?',
                'category': PromptCategory.INTELLECTUAL,
            },
            # Wildcard
            {
                'text': 'What made you laugh out loud this week?',
                'category': PromptCategory.WILDCARD,
            },
            {
                'text': 'What\'s something random you thought about today?',
                'category': PromptCategory.WILDCARD,
            },
            {
                'text': 'If you could learn any skill instantly, what would it be?',
                'category': PromptCategory.WILDCARD,
            },
            {
                'text': 'What\'s the best meal you\'ve had recently?',
                'category': PromptCategory.WILDCARD,
            },
            {
                'text': 'What show or movie are you obsessed with right now?',
                'category': PromptCategory.WILDCARD,
            },
            {
                'text': 'What\'s something you\'re looking forward to this month?',
                'category': PromptCategory.WILDCARD,
            },
            {
                'text': 'Describe your ideal morning routine.',
                'category': PromptCategory.WHOLESOME,
            },
            {
                'text': 'What\'s a hidden talent of yours I might not know about?',
                'category': PromptCategory.LORE,
            },
            {
                'text': 'What would your superhero name and power be?',
                'category': PromptCategory.CHAOS,
            },
            {
                'text': 'What\'s a fear you\'d like to overcome together?',
                'category': PromptCategory.PLOT,
            },
            {
                'text': 'What does "home" mean to you?',
                'category': PromptCategory.INTELLECTUAL,
            },
        ]
        
        # Assign dates starting from today
        result = []
        for i, prompt in enumerate(prompts):
            prompt_date = today + timedelta(days=i)
            result.append({
                'text': prompt['text'],
                'category': prompt['category'],
                'active_date': prompt_date,
            })
        
        return result

