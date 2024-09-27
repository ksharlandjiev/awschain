from handlers.abstract_handler import AbstractHandler
import yfinance as yf
import numpy as np

class YahooFinanceFundamentalsAnalysisHandler(AbstractHandler):
    def handle(self, request):
        stock = request
        LSE_COUNTRIES = ["GB", "JE"]

        if 'company_symbol' not in stock:
            raise ValueError("Stock symbol not provided in request")
        
        country = stock.get("country", "N/A")

        symbol = stock['company_symbol']

        if country in LSE_COUNTRIES:
            symbol = f"{stock['company_symbol']}.L"

        # Fetch stock data from Yahoo Finance
        yahoo_stock = yf.Ticker(symbol)

        # Gather fundamental metrics
        revenue = self._get_financial_metric(yahoo_stock, "Total Revenue")
        gross_profit = self._get_financial_metric(yahoo_stock, "Gross Profit")
        eps = self._get_financial_metric(yahoo_stock, "Basic EPS")
        dividends = self._get_dividends(yahoo_stock)
        p_e_ratio = self._get_financial_metric(yahoo_stock, "Price to Earnings Ratio")
        closing_prices = self._get_closing_prices(yahoo_stock)

        # Ensure data is valid
        if not self._is_valid_data(revenue):
            stock['recommendation'] = 'INSUFFICIENT DATA'
            stock['reasons'] = ["Insufficient or invalid revenue data"]
            return request

        if not self._is_valid_data(gross_profit):
            stock['recommendation'] = 'INSUFFICIENT DATA'
            stock['reasons'] = ["Insufficient or invalid gross profit data"]
            return request

        if not self._is_valid_data(closing_prices):
            stock['recommendation'] = 'INSUFFICIENT DATA'
            stock['reasons'] = ["Insufficient or invalid stock price data"]
            return request

        # Analyze trends and calculate percentage differences
        revenue_trend, revenue_pct_diff = self._is_trending_up(revenue)
        gross_profit_trend, gross_profit_pct_diff = self._is_trending_up(gross_profit)
        stock_price_trend, price_pct_diff = self._is_trending_up(closing_prices)

        # Analyze the dividend trend, ensuring the list has enough elements
        dividend_trend = False
        dividend_pct_diff = 0
        if self._is_valid_data(dividends):
            if len(dividends) >= 2:
                dividend_trend, dividend_pct_diff = self._is_trending_up(dividends)


        # Determine recommendation and reasons
        recommendation = []
        reasons = []

        if not revenue_trend:
            recommendation.append("SELL")
            reasons.append(
                f"Revenue is not rising. Start: {self._format_number(revenue[-1])}, End: {self._format_number(revenue[0])}, Change: {revenue_pct_diff:.2f}%"
            )
        else:
            recommendation.append("BUY")
            reasons.append(
                f"Revenue is rising. Start: {self._format_number(revenue[-1])}, End: {self._format_number(revenue[0])}, Change: {revenue_pct_diff:.2f}%"
            )

        if not gross_profit_trend:
            recommendation.append("SELL")
            reasons.append(
                f"Gross profit is not rising. Start: {self._format_number(gross_profit[-1])}, End: {self._format_number(gross_profit[0])}, Change: {gross_profit_pct_diff:.2f}%"
            )
        else: 
            recommendation.append("BUY")
            reasons.append(
                f"Gross profit is rising. Start: {self._format_number(gross_profit[-1])}, End: {self._format_number(gross_profit[0])}, Change: {gross_profit_pct_diff:.2f}%"
            )

        slope = self._calculate_slope(closing_prices)  # Calculate slope for trend
        if stock_price_trend:
            recommendation.append("BUY")
            
            reasons.append(
                f"Stock price is in an upward trend. Slope: {slope:.2f}, Start: {self._format_number(closing_prices[-1])}, End: {self._format_number(closing_prices[0])}, Change: {price_pct_diff:.2f}%"
            )
        else:
            reasons.append(
                f"Stock price is in a downward trend. Slope: {slope:.2f}, Start: {self._format_number(closing_prices[-1])}, End: {self._format_number(closing_prices[0])}, Change: {price_pct_diff:.2f}%"
            )

        if dividend_trend:
            recommendation.append("BIG_BUY")
            reasons.append(
                f"Dividends are rising. Start: {self._format_number(dividends[-1])}, End: {self._format_number(dividends[0])}, Change: {dividend_pct_diff:.2f}%"
            )

        # Additional analysis with other metrics
        if self._is_valid_data(eps):
            if eps[0] >0:
                recommendation.append("BUY")
            else: 
                recommendation.append("SELL")
            reasons.append(f"Earnings per share (EPS): {self._format_number(eps[0])}")

        # if self._is_valid_data(dividend_yield):
        #     reasons.append(f"Dividends (latest): {self._format_number(dividend_yield[0])}")

        if self._is_valid_data(p_e_ratio):
            reasons.append(f"Price-to-earnings (P/E) ratio: {p_e_ratio[0]:,.2f}")

        # Provide a final recommendation
        if not recommendation:
            recommendation.append("HOLD")

        stock["fundamentals_recommendation"] = "-".join(recommendation)
        stock["fundamentals_reasons"] = reasons

        return super().handle(request)

    def _get_dividends(self, yahoo_stock):
        # Get dividend data and reverse it for correct chronological order
        try:
            dividends = yahoo_stock.dividends
            reversed_dividends = dividends[::-1]  # Reverse the data
            return self._convert_to_float(reversed_dividends.values)
        except Exception as e:
            print(f"Error fetching dividends: {e}")
            return None

    def _get_financial_metric(self, yahoo_stock, metric):
        # Retrieve the specified financial metric from Yahoo Finance
        try:
            financials = yahoo_stock.financials
            if metric in financials.index:
                return self._convert_to_float(financials.loc[metric].values)
        except Exception as e:
            print(f"Error fetching {metric}: {e}")
            return None

    def _get_closing_prices(self, yahoo_stock):
        # Fetch the closing prices for the past 6 months
        try:
            historical = yahoo_stock.history(period="6mo")
            # Ensure the data is reversed, with the most recent date as the first element
            reversed_historical = historical[::-1]  # Reverse the data
            return self._convert_to_float(reversed_historical['Close'].values)
        except KeyError:
            return None

    def _convert_to_float(self, values):
        # Convert to float and remove invalid values
        return [float(value) for value in values if isinstance(value, (int, float))]

    def _format_number(self, number):
        # Format large numbers with M for millions, K for thousands, and B for billions
        if number >= 1_000_000_000:
            return f"{number / 1_000_000_000:.2f}B"
        elif number >= 1_000_000:
            return f"{number / 1_000_000:.2f}M"
        elif number >= 1_000:
            return f"{number / 1_000:.2f}K"
        else:
            return f"{number:.2f}"    
        
    def _is_trending_up(self, data):
        # Determine if the trend is upward using a simple linear regression
        if not self._is_valid_data(data):
            return False, 0
        
        # Create a range of indices, treating the last element as the earliest data point
        x = np.arange(len(data))
        # Reverse the data array to maintain proper chronological order for analysis
        y = np.array(data[::-1], dtype=np.float64)  # Reverse the data order
        
        # Calculate the slope
        slope = np.polyfit(x, y, 1)[0]

        # Calculate the percentage difference between the earliest and latest data points
        start = y[0]
        end = y[-1]
        pct_diff = ((end - start) / start) * 100
        
        return slope > 0, pct_diff

    def _calculate_slope(self, data):
        # Calculate the slope of a simple linear regression
        x = np.arange(len(data))
        # Reverse the data array to ensure correct chronological order for analysis
        y = np.array(data[::-1], dtype=np.float64)  # Reverse the data order
        
        slope = np.polyfit(x, y, 1)[0]  # Calculate the slope value
        
        return slope


    def _is_valid_data(self, data):
        # Check if the data is valid and has at least two elements
        if not isinstance(data, (list, np.ndarray)):
            return False
        
        if len(data) < 2:
            return False
        
        return all(isinstance(item, (int, float)) for item in data)
