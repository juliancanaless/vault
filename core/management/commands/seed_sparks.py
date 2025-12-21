"""
Management command to seed the database with initial Spark content.

Usage:
    python manage.py seed_sparks
    python manage.py seed_sparks --clear  # Clear existing sparks first
"""

from django.core.management.base import BaseCommand
from core.models import Spark, SparkCategory, PromptCategory


class Command(BaseCommand):
    help = 'Seeds the database with initial Spark content for couples'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing sparks before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted_count = Spark.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing sparks'))

        sparks_data = self.get_spark_data()
        
        created_count = 0
        for spark_data in sparks_data:
            spark, created = Spark.objects.get_or_create(
                text=spark_data['text'],
                category=spark_data['category'],
                defaults={
                    'option_b': spark_data.get('option_b', ''),
                    'vibe': spark_data.get('vibe', PromptCategory.WILDCARD),
                    'subtitle': spark_data.get('subtitle', ''),
                }
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Successfully seeded {created_count} new sparks (total: {Spark.objects.count()})'
        ))

    def get_spark_data(self):
        """Return list of spark data dictionaries."""
        return [
            # =====================
            # DATE IDEAS
            # =====================
            # Wholesome
            {
                'text': 'Cook a new recipe together that neither of you has tried before',
                'category': SparkCategory.DATE,
                'vibe': PromptCategory.WHOLESOME,
                'subtitle': 'Pick something slightly ambitious!',
            },
            {
                'text': 'Build a blanket fort and watch your favorite childhood movie',
                'category': SparkCategory.DATE,
                'vibe': PromptCategory.WHOLESOME,
            },
            {
                'text': 'Have a picnic — inside or outside, your choice',
                'category': SparkCategory.DATE,
                'vibe': PromptCategory.WHOLESOME,
            },
            {
                'text': 'Take a sunset walk with no destination in mind',
                'category': SparkCategory.DATE,
                'vibe': PromptCategory.WHOLESOME,
            },
            {
                'text': 'Write love letters to each other and read them out loud',
                'category': SparkCategory.DATE,
                'vibe': PromptCategory.WHOLESOME,
            },
            {
                'text': 'Make breakfast in bed for each other on the same morning',
                'category': SparkCategory.DATE,
                'vibe': PromptCategory.WHOLESOME,
            },
            {
                'text': 'Stargaze from your backyard, balcony, or even a parking lot',
                'category': SparkCategory.DATE,
                'vibe': PromptCategory.WHOLESOME,
            },
            {
                'text': 'Create a scrapbook page together of your favorite memories',
                'category': SparkCategory.DATE,
                'vibe': PromptCategory.WHOLESOME,
            },
            # Chaos
            {
                'text': 'Go thrift shopping and pick out the most ridiculous outfit for each other — then wear them to dinner',
                'category': SparkCategory.DATE,
                'vibe': PromptCategory.CHAOS,
            },
            {
                'text': 'Have a "yes day" where you say yes to whatever the other person suggests',
                'category': SparkCategory.DATE,
                'vibe': PromptCategory.CHAOS,
            },
            {
                'text': 'Drive somewhere you\'ve never been with no GPS — just vibes',
                'category': SparkCategory.DATE,
                'vibe': PromptCategory.CHAOS,
            },
            {
                'text': 'Do karaoke at home with only songs you don\'t know the words to',
                'category': SparkCategory.DATE,
                'vibe': PromptCategory.CHAOS,
            },
            # Adventure
            {
                'text': 'Go on a sunrise hike and bring hot coffee',
                'category': SparkCategory.DATE,
                'vibe': PromptCategory.PLOT,
            },
            {
                'text': 'Take a day trip to a town neither of you has visited',
                'category': SparkCategory.DATE,
                'vibe': PromptCategory.PLOT,
            },
            {
                'text': 'Try a new activity together: rock climbing, pottery, escape room, etc.',
                'category': SparkCategory.DATE,
                'vibe': PromptCategory.PLOT,
            },
            # Spicy
            {
                'text': 'Have a fancy at-home dinner with candles, dressed up like it\'s a five-star restaurant',
                'category': SparkCategory.DATE,
                'vibe': PromptCategory.SPICY,
            },
            {
                'text': 'Take turns giving each other massages with no phones allowed',
                'category': SparkCategory.DATE,
                'vibe': PromptCategory.SPICY,
            },
            
            # =====================
            # CONVERSATION STARTERS
            # =====================
            # Wholesome
            {
                'text': 'What\'s a small thing I do that makes you feel loved?',
                'category': SparkCategory.CONVO,
                'vibe': PromptCategory.WHOLESOME,
            },
            {
                'text': 'What\'s your happiest memory of us so far?',
                'category': SparkCategory.CONVO,
                'vibe': PromptCategory.WHOLESOME,
            },
            {
                'text': 'What did you think of me the very first time we met?',
                'category': SparkCategory.CONVO,
                'vibe': PromptCategory.LORE,
            },
            {
                'text': 'If we could relive one day together, which would you pick?',
                'category': SparkCategory.CONVO,
                'vibe': PromptCategory.WHOLESOME,
            },
            {
                'text': 'What\'s something you want us to do together that we haven\'t done yet?',
                'category': SparkCategory.CONVO,
                'vibe': PromptCategory.PLOT,
            },
            # Deep / Intellectual
            {
                'text': 'What\'s something you\'ve never told anyone that you\'d trust me with?',
                'category': SparkCategory.CONVO,
                'vibe': PromptCategory.INTELLECTUAL,
            },
            {
                'text': 'What do you think is the meaning of life? Has your answer changed over time?',
                'category': SparkCategory.CONVO,
                'vibe': PromptCategory.INTELLECTUAL,
            },
            {
                'text': 'What\'s a belief you held strongly that you\'ve completely changed your mind about?',
                'category': SparkCategory.CONVO,
                'vibe': PromptCategory.INTELLECTUAL,
            },
            {
                'text': 'If you could have dinner with anyone, dead or alive, who would it be and what would you ask them?',
                'category': SparkCategory.CONVO,
                'vibe': PromptCategory.INTELLECTUAL,
            },
            # Future / Plot
            {
                'text': 'Where do you see us in five years?',
                'category': SparkCategory.CONVO,
                'vibe': PromptCategory.PLOT,
            },
            {
                'text': 'What\'s a dream you\'ve been too scared to pursue?',
                'category': SparkCategory.CONVO,
                'vibe': PromptCategory.GRIND,
            },
            {
                'text': 'What would our ideal life look like if money wasn\'t a factor?',
                'category': SparkCategory.CONVO,
                'vibe': PromptCategory.PLOT,
            },
            {
                'text': 'What\'s one thing you want to accomplish this year?',
                'category': SparkCategory.CONVO,
                'vibe': PromptCategory.GRIND,
            },
            # Lore
            {
                'text': 'What\'s an inside joke of ours that still makes you laugh?',
                'category': SparkCategory.CONVO,
                'vibe': PromptCategory.LORE,
            },
            {
                'text': 'What was the moment you knew you wanted to be with me?',
                'category': SparkCategory.CONVO,
                'vibe': PromptCategory.LORE,
            },
            {
                'text': 'What\'s a childhood story I don\'t know about you yet?',
                'category': SparkCategory.CONVO,
                'vibe': PromptCategory.LORE,
            },
            
            # =====================
            # WOULD YOU RATHER
            # =====================
            # Wholesome
            {
                'text': 'Always have to sing instead of speaking',
                'option_b': 'Always have to dance instead of walking',
                'category': SparkCategory.WYR,
                'vibe': PromptCategory.CHAOS,
            },
            {
                'text': 'Have the ability to fly',
                'option_b': 'Have the ability to read minds',
                'category': SparkCategory.WYR,
                'vibe': PromptCategory.WILDCARD,
            },
            {
                'text': 'Live in a treehouse in the forest',
                'option_b': 'Live in a houseboat on the ocean',
                'category': SparkCategory.WYR,
                'vibe': PromptCategory.WHOLESOME,
            },
            {
                'text': 'Only be able to whisper for the rest of your life',
                'option_b': 'Only be able to shout for the rest of your life',
                'category': SparkCategory.WYR,
                'vibe': PromptCategory.CHAOS,
            },
            {
                'text': 'Never use social media again',
                'option_b': 'Never watch TV/movies again',
                'category': SparkCategory.WYR,
                'vibe': PromptCategory.WILDCARD,
            },
            {
                'text': 'Have unlimited money but no love',
                'option_b': 'Have true love but struggle financially',
                'category': SparkCategory.WYR,
                'vibe': PromptCategory.GRIND,
            },
            {
                'text': 'Know when you\'re going to die',
                'option_b': 'Know how you\'re going to die',
                'category': SparkCategory.WYR,
                'vibe': PromptCategory.INTELLECTUAL,
            },
            {
                'text': 'Be famous but constantly stressed',
                'option_b': 'Be unknown but deeply content',
                'category': SparkCategory.WYR,
                'vibe': PromptCategory.GRIND,
            },
            {
                'text': 'Relive the same day forever (a good day)',
                'option_b': 'Live a normal life but forget everything each morning',
                'category': SparkCategory.WYR,
                'vibe': PromptCategory.INTELLECTUAL,
            },
            {
                'text': 'Have your partner plan every date',
                'option_b': 'Plan every date yourself',
                'category': SparkCategory.WYR,
                'vibe': PromptCategory.WHOLESOME,
            },
            # Spicy
            {
                'text': 'Give up kissing for a year',
                'option_b': 'Give up hugging for a year',
                'category': SparkCategory.WYR,
                'vibe': PromptCategory.SPICY,
            },
            {
                'text': 'Have your partner know every thought you have',
                'option_b': 'Never know what they\'re thinking ever again',
                'category': SparkCategory.WYR,
                'vibe': PromptCategory.SPICY,
            },
            
            # =====================
            # QUICK GAMES
            # =====================
            {
                'text': 'Play 20 Questions — one person thinks of something, the other has 20 yes/no questions to guess it',
                'category': SparkCategory.GAME,
                'vibe': PromptCategory.WILDCARD,
                'subtitle': 'Categories: person, place, thing, or idea',
            },
            {
                'text': 'Truth or Dare — take turns, no skipping, and be creative!',
                'category': SparkCategory.GAME,
                'vibe': PromptCategory.CHAOS,
            },
            {
                'text': 'Two Truths and a Lie — guess which statement is false',
                'category': SparkCategory.GAME,
                'vibe': PromptCategory.LORE,
            },
            {
                'text': 'The "No Laughing" Challenge — try to make each other laugh without touching. First to crack loses',
                'category': SparkCategory.GAME,
                'vibe': PromptCategory.CHAOS,
            },
            {
                'text': 'Guess the Song — hum or describe a song without saying any lyrics. See who can guess the most',
                'category': SparkCategory.GAME,
                'vibe': PromptCategory.WILDCARD,
            },
            {
                'text': 'Word Association — say a word, partner says the first word that comes to mind. No pausing!',
                'category': SparkCategory.GAME,
                'vibe': PromptCategory.WILDCARD,
            },
            {
                'text': 'Rate My Day — both rate your day 1-10, then explain why. Celebrate wins or comfort lows',
                'category': SparkCategory.GAME,
                'vibe': PromptCategory.WHOLESOME,
            },
            {
                'text': 'This or That — rapid fire preferences: morning or night? Sweet or savory? Beach or mountains?',
                'category': SparkCategory.GAME,
                'vibe': PromptCategory.WILDCARD,
            },
            {
                'text': 'Complete My Sentence — start a sentence, partner finishes it. The weirder the better',
                'category': SparkCategory.GAME,
                'vibe': PromptCategory.CHAOS,
            },
            {
                'text': 'Rose, Bud, Thorn — share a highlight (rose), something you\'re looking forward to (bud), and a challenge (thorn) from your day',
                'category': SparkCategory.GAME,
                'vibe': PromptCategory.WHOLESOME,
                'subtitle': 'Great for daily check-ins',
            },
            {
                'text': 'Compliment Battle — take turns giving genuine compliments. First to get flustered loses',
                'category': SparkCategory.GAME,
                'vibe': PromptCategory.WHOLESOME,
            },
            {
                'text': 'Hot Takes — share an unpopular opinion. Partner has to guess if it\'s real or fake',
                'category': SparkCategory.GAME,
                'vibe': PromptCategory.CHAOS,
            },
        ]

