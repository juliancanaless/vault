"""
Management command to backfill sentiment scores for entries.

Usage:
    python manage.py calculate_sentiment                    # All entries missing scores
    python manage.py calculate_sentiment --year=2025       # Only 2025 entries
    python manage.py calculate_sentiment --dry-run         # Preview without saving

Requires: pip install textblob
First run: python -m textblob.download_corpora
"""

from django.core.management.base import BaseCommand
from core.models import Entry


class Command(BaseCommand):
    help = 'Calculate sentiment scores for journal entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            help='Only process entries from this year',
        )
        parser.add_argument(
            '--recalculate',
            action='store_true',
            help='Recalculate even if score already exists',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving',
        )

    def handle(self, *args, **options):
        try:
            from textblob import TextBlob
        except ImportError:
            self.stderr.write(
                self.style.ERROR(
                    'TextBlob not installed. Run: pip install textblob && python -m textblob.download_corpora'
                )
            )
            return

        # Build queryset
        queryset = Entry.objects.all()
        
        if options['year']:
            queryset = queryset.filter(created_at__year=options['year'])
            self.stdout.write(f"Filtering to year {options['year']}")
        
        if not options['recalculate']:
            queryset = queryset.filter(sentiment_score__isnull=True)
            self.stdout.write("Processing only entries without scores")
        
        total = queryset.count()
        self.stdout.write(f"Found {total} entries to process")
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN - no changes will be saved'))
        
        processed = 0
        for entry in queryset.iterator():
            # Calculate sentiment using TextBlob
            # Returns polarity: -1.0 (negative) to 1.0 (positive)
            blob = TextBlob(entry.text_content)
            score = blob.sentiment.polarity
            
            if options['dry_run']:
                self.stdout.write(
                    f"  [{entry.user.username}] {entry.prompt.active_date}: {score:.3f}"
                )
            else:
                entry.sentiment_score = score
                entry.save(update_fields=['sentiment_score'])
            
            processed += 1
            
            if processed % 100 == 0:
                self.stdout.write(f"  Processed {processed}/{total}...")
        
        self.stdout.write(
            self.style.SUCCESS(f'Done! Processed {processed} entries.')
        )

