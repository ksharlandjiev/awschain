import requests
from bs4 import BeautifulSoup
from handlers.abstract_handler import AbstractHandler

class TrafficLightAnalyzerHandler(AbstractHandler):
    def handle(self, request):
        
        stock = request

        # Keywords for analysis
        SELL_KEYWORDS = ["challenging", "difficult", "down by", "unpredictable", "lower", "poor", "tough", "below expectations", "deficit"]
        BUY_KEYWORDS = ["exceeding expectations", "positive", "successful", "favorable", "profit up", "excellent", "transformational", "strong", "demand"]
        HOLD_KEYWORDS = ["in line with expectations", "stability"]

        # Analyze the financial report
        report_text = stock['text'] 
        
        sell_count = sum(1 for kw in SELL_KEYWORDS if kw in report_text)
        buy_count = sum(1 for kw in BUY_KEYWORDS if kw in report_text)
        hold_count = sum(1 for kw in HOLD_KEYWORDS if kw in report_text)

        # Create a recommendation order based on the keyword counts
        recommendation_order = [
            ("SELL", sell_count),
            ("BUY", buy_count),
            ("HOLD", hold_count),
        ]
        # Sort the recommendations in descending order of keyword counts
        recommendation_order.sort(key=lambda x: x[1], reverse=True)

        # Build the recommendation string
        stock["recommendation"] = "-".join([rec for rec, count in recommendation_order if count > 0])

        # Update reasons with counts for each category
        stock["reasons"] = [
            f"SELL: {sell_count}, BUY: {buy_count}, HOLD: {hold_count}"
        ]

        return super().handle(request)
