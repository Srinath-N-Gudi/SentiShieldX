from itertools import islice
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR
from .Cyber import Cyber
from typing import Dict


class CommentAnalyzer:
    def __init__(self, cyber: Cyber):
        """Initializes the CommentAnalyzer with a given Cyber instance."""
        self.cyber = cyber
        self.downloader = YoutubeCommentDownloader()
    def analyse_comment(self, youtube_url: str, num_comments: int = 1000) -> dict:
        """Analyses comments from a given YouTube video.

        Args:
            youtube_url (str): The URL of the YouTube video.
            num_comments (int, optional): The number of comments to analyze. Defaults to 1000.
        """
        results = {
            'total_comments': 0,
            'hate_comments': 0,
            'positive_comments': 0,
            'neutral_comments': 0
        }
        self.comments = self.downloader.get_comments_from_url(youtube_url, sort_by=SORT_BY_POPULAR)
        value = islice(self.comments, num_comments)
        next(value) # Skipping the first comment ( As sometimes it might be video description )
        
        for comment in value:
            results['total_comments']+=1
            comment_text = comment.get('text')
            sentiment = self.cyber.analyze_sentiment(comment_text)
            if self.cyber.detect_hate_speech(comment_text) or sentiment == "negative":
                results['hate_comments']+=1
            elif sentiment == "positive":
                results['positive_comments']+=1
            else:
                results['neutral_comments']+=1

        return results
