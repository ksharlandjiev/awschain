from handlers.abstract_handler import AbstractHandler

class FilterStocksHandler(AbstractHandler):
    # Constants for filtering
    MARKET_CAP_THRESHOLD = 35_000_000  # £35
    MARKET_SIZE_THRESHOLD = 2_000  # £2k

    # Sectors to exclude
    SECTOR_EXCLUDE_LIST = ["601010"]  #Excluding oil and gas sector

    def handle(self, request):
        # Stock data from the request
        stock = request
        stock['recommendation'] = ""

        # Ensure stock has the necessary information
        if 'marketcapitalization' not in stock or 'marketsize' not in stock or 'lastprice' not in stock:
            stock['recommendation'] = 'SKIP'
            stock['reasons'] = ["Missing necessary stock information"]
            return request  # Return early to halt the chain

        # Check sector code for exclusion
        if 'sectorcode' in stock and stock['sectorcode'] in self.SECTOR_EXCLUDE_LIST:
            stock["recommendation"] = "SKIP"
            stock["reasons"] = [f"Stock is in excluded sector: {stock['sectorcode']}"]
            return request  # Return early to halt the chain

        # Check market capitalization
        market_cap = stock.get("marketcapitalization", 0)
        if market_cap > 0 and market_cap < self.MARKET_CAP_THRESHOLD:
            stock["recommendation"] = "SKIP"
            stock["reasons"] = [f"Market Cap ({market_cap}) is less than {self.MARKET_CAP_THRESHOLD}"]
            return request  # Return early to halt the chain

        # Calculate the exchange market size
        market_size = stock.get("marketsize", 0)
        last_price = stock.get("lastprice", 0)
        exchange_market_size = 0
        if market_size and last_price:
            exchange_market_size = (market_size * last_price)/100

        # Check if the calculated market size is below the threshold
        if exchange_market_size < self.MARKET_SIZE_THRESHOLD:
            stock["recommendation"] = "SKIP"
            stock["reasons"] = [f"Exchange Market Size (EMS) is less than {self.MARKET_SIZE_THRESHOLD}. Calculated EMS: {exchange_market_size}"]
            return request  # Return early to halt the chain

        # If stock meets all criteria, proceed with the chain
        return super().handle(request)
