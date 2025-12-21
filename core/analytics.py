"""
The Vault - Couple Analytics Engine

Analytics designed for couples as a unit, not just individuals.
Powers the year-end "Wrapped" experience.
"""

from django.db.models import Avg, Count, Sum, F, Q
from django.db.models.functions import TruncMonth, Abs
from django.contrib.auth import get_user_model
from .models import Entry, Prompt, PromptCategory

User = get_user_model()


class CoupleAnalytics:
    """
    Analytics engine for a couple's shared journal.
    
    All metrics are computed for the PAIR, considering both partners'
    responses to the same prompts.
    """
    
    def __init__(self, couple, year):
        """
        Analytics are scoped to a specific Couple (vault).
        This prevents mixing entries across multiple relationships.
        """
        self.couple = couple
        self.user1 = couple.user1
        self.user2 = couple.user2
        self.year = year
        self.users = [u for u in [self.user1, self.user2] if u is not None]
    
    def get_paired_entries(self):
        """
        Get prompts where BOTH partners answered.
        Returns list of (prompt, entry1, entry2) tuples.
        """
        # Get prompts both answered in this year
        prompts_user1 = set(
            Entry.objects.filter(
                user=self.user1,
                couple=self.couple,
                created_at__year=self.year
            ).values_list('prompt_id', flat=True)
        )
        prompts_user2 = set(
            Entry.objects.filter(
                user=self.user2,
                couple=self.couple,
                created_at__year=self.year
            ).values_list('prompt_id', flat=True)
        )
        
        shared_prompt_ids = prompts_user1 & prompts_user2
        
        paired = []
        for prompt_id in shared_prompt_ids:
            prompt = Prompt.objects.get(id=prompt_id)
            entry1 = Entry.objects.get(user=self.user1, prompt_id=prompt_id, couple=self.couple)
            entry2 = Entry.objects.get(user=self.user2, prompt_id=prompt_id, couple=self.couple)
            paired.append((prompt, entry1, entry2))
        
        return paired
    
    # =========================================================================
    # COMBINED SENTIMENT METRICS
    # =========================================================================
    
    def couple_average_sentiment(self):
        """
        The couple's overall emotional tone for the year.
        Averages BOTH partners' sentiment scores together.
        
        Returns: float (-1.0 to 1.0) or None
        """
        result = Entry.objects.filter(
            user__in=self.users,
            couple=self.couple,
            created_at__year=self.year,
            sentiment_score__isnull=False
        ).aggregate(avg=Avg('sentiment_score'))
        
        return result['avg']
    
    def couple_monthly_sentiment(self):
        """
        Monthly sentiment for the couple as a unit.
        
        Returns: list of {'month': datetime, 'avg_score': float}
        """
        return list(
            Entry.objects.filter(
                user__in=self.users,
                couple=self.couple,
                created_at__year=self.year,
                sentiment_score__isnull=False
            ).annotate(
                month=TruncMonth('created_at')
            ).values('month').annotate(
                avg_score=Avg('sentiment_score')
            ).order_by('month')
        )
    
    def happiest_month(self):
        """The month with highest combined sentiment."""
        monthly = self.couple_monthly_sentiment()
        if not monthly:
            return None
        return max(monthly, key=lambda x: x['avg_score'])
    
    # =========================================================================
    # SYNC & ALIGNMENT METRICS
    # =========================================================================
    
    def sentiment_sync_score(self):
        """
        How emotionally aligned is the couple?
        
        Measures: When answering the SAME prompt, how similar are their sentiments?
        
        Returns: float 0.0 (opposite vibes) to 1.0 (perfectly in sync)
        """
        paired = self.get_paired_entries()
        
        if not paired:
            return None
        
        # Filter to pairs where both have sentiment scores
        scored_pairs = [
            (e1, e2) for (_, e1, e2) in paired
            if e1.sentiment_score is not None and e2.sentiment_score is not None
        ]
        
        if not scored_pairs:
            return None
        
        # Calculate average absolute difference
        # Difference of 0 = perfect sync, difference of 2 = complete opposite
        total_diff = sum(
            abs(e1.sentiment_score - e2.sentiment_score)
            for e1, e2 in scored_pairs
        )
        avg_diff = total_diff / len(scored_pairs)
        
        # Convert to 0-1 scale where 1 = perfect sync
        # Max possible diff is 2.0 (-1 to +1)
        sync_score = 1 - (avg_diff / 2.0)
        
        return round(sync_score, 3)
    
    def shared_joy_moments(self, threshold=0.3):
        """
        Prompts where BOTH partners felt positive.
        These are your "shared joy" moments.
        
        Args:
            threshold: Minimum sentiment score to count as positive
        
        Returns: list of (prompt, entry1, entry2)
        """
        paired = self.get_paired_entries()
        
        joyful = [
            (prompt, e1, e2) for (prompt, e1, e2) in paired
            if (e1.sentiment_score or 0) >= threshold 
            and (e2.sentiment_score or 0) >= threshold
        ]
        
        # Sort by combined joy (highest first)
        joyful.sort(
            key=lambda x: (x[1].sentiment_score or 0) + (x[2].sentiment_score or 0),
            reverse=True
        )
        
        return joyful
    
    def tough_days_together(self, threshold=-0.2):
        """
        Prompts where BOTH partners felt down.
        Important for "we got through it together" narrative.
        
        Returns: list of (prompt, entry1, entry2)
        """
        paired = self.get_paired_entries()
        
        tough = [
            (prompt, e1, e2) for (prompt, e1, e2) in paired
            if (e1.sentiment_score or 0) <= threshold 
            and (e2.sentiment_score or 0) <= threshold
        ]
        
        return tough
    
    def emotional_support_moments(self, gap_threshold=0.5):
        """
        Moments where one partner was down but the other was up.
        These could represent times of emotional support.
        
        Returns: list of {'prompt': Prompt, 'supporter': User, 'supported': User}
        """
        paired = self.get_paired_entries()
        
        support_moments = []
        for prompt, e1, e2 in paired:
            s1 = e1.sentiment_score or 0
            s2 = e2.sentiment_score or 0
            
            # Check if there's a significant gap
            if abs(s1 - s2) >= gap_threshold:
                if s1 > s2:
                    supporter, supported = self.user1, self.user2
                else:
                    supporter, supported = self.user2, self.user1
                
                support_moments.append({
                    'prompt': prompt,
                    'supporter': supporter,
                    'supported': supported,
                    'gap': abs(s1 - s2)
                })
        
        return support_moments
    
    # =========================================================================
    # COMBINED ACTIVITY METRICS
    # =========================================================================
    
    def total_words_together(self):
        """Total words written by the couple combined."""
        result = Entry.objects.filter(
            user__in=self.users,
            couple=self.couple,
            created_at__year=self.year
        ).aggregate(total=Sum('word_count'))
        
        return result['total'] or 0
    
    def response_rate(self):
        """
        Percentage of prompts where BOTH partners answered.
        Measures: commitment to the shared ritual.
        
        Returns: float 0.0 to 1.0
        """
        total_prompts = Prompt.objects.filter(
            active_date__year=self.year
        ).count()
        
        if total_prompts == 0:
            return 0.0
        
        paired = self.get_paired_entries()
        both_answered = len(paired)
        
        return round(both_answered / total_prompts, 3)
    
    def top_vibe_together(self):
        """
        Which prompt category resonated most with the couple?
        Based on combined response count.
        """
        return list(
            Entry.objects.filter(
                user__in=self.users,
                couple=self.couple,
                created_at__year=self.year
            ).values('prompt__category').annotate(
                count=Count('id')
            ).order_by('-count')
        )
    
    def longest_combined_entry(self):
        """
        The prompt that got you both talking the most.
        Returns the prompt with highest combined word count.
        """
        paired = self.get_paired_entries()
        
        if not paired:
            return None
        
        # Find prompt with max combined words
        return max(
            paired,
            key=lambda x: x[1].word_count + x[2].word_count
        )
    
    # =========================================================================
    # WRAPPED SUMMARY
    # =========================================================================
    
    def generate_wrapped_data(self):
        """
        Generate all the data needed for a Wrapped presentation.
        Returns a dictionary ready for template rendering.
        """
        return {
            'year': self.year,
            'users': [self.user1.username, self.user2.username],
            
            # Sentiment
            'couple_sentiment': self.couple_average_sentiment(),
            'happiest_month': self.happiest_month(),
            'sync_score': self.sentiment_sync_score(),
            
            # Highlights
            'shared_joy_count': len(self.shared_joy_moments()),
            'top_joy_moment': self.shared_joy_moments()[:1],
            'tough_days_count': len(self.tough_days_together()),
            'support_moments': len(self.emotional_support_moments()),
            
            # Activity
            'total_words': self.total_words_together(),
            'response_rate': self.response_rate(),
            'top_vibes': self.top_vibe_together()[:3],
            'most_words_prompt': self.longest_combined_entry(),
            
            # Monthly trend
            'monthly_sentiment': self.couple_monthly_sentiment(),
        }

