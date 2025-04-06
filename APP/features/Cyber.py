from textblob import TextBlob
from detoxify import Detoxify
from typing import Union

class Cyber:
    def __init__(self, detoxifier_model: Union['original', 'unbiased', 'multilingual', 'original-small', 'unbiased-small']='multilingual', device='cpu'):
        """
        Cyber is a object which contains both hate detector and sentiment analyzer
        """
        self.hate_speech_detector = Detoxify("multilingual", device=device)

    def detect_hate_speech(self, text: str) -> bool:
        results = self.hate_speech_detector.predict(text)
        if any(score > 0.8 for score in results.values()):
            return True
        return False

    def analyze_sentiment(self, text: str) -> Union['positive', 'negative', 'neutral']:
        analysis = TextBlob(text)
        polarity = analysis.sentiment.polarity

        if polarity > 0:
            return "positive"
        elif polarity < 0:
            return "negative"
        else:
            return "neutral"
