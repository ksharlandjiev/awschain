import requests
import json
from handlers.abstract_handler import AbstractHandler
import random
import time
from handlers.abstract_handler import AbstractHandler

class LSEStockInfoReaderHandler(AbstractHandler):
    def handle(self, request):
        
        stock_symbol = request['company_symbol']       
        HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
        }

        updated_stocks = []


        print(f"Processing: {stock_symbol}")

        # Random timeout for human-like behavior
        TIMEOUT_MIN = 1
        TIMEOUT_MAX = 5
        time.sleep(random.uniform(TIMEOUT_MIN, TIMEOUT_MAX))

        # Fetch additional stock information from the LSE API
        url = f"https://api.londonstockexchange.com/api/gw/lse/instruments/alldata/{stock_symbol}"
        response = requests.get(url, headers=HEADERS)

        if response.status_code == 200:
            stock_info = response.json()  # Parse JSON data from the response
            request.update(stock_info)

        return super().handle(request)
