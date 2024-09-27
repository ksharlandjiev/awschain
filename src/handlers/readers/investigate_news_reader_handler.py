import requests
from bs4 import BeautifulSoup
from datetime import datetime
from handlers.abstract_handler import AbstractHandler

class InvestigateNewsReaderHandler(AbstractHandler):
    # Constants for scraping and filtering
    NEWS_PER_PAGE = 10
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-GB,en;q=0.5',
    }

    NEWS_FILTER = ["half", "full", "final", "annual", "results", "financial", "trading update"]
    NEWS_EXCLUDE_FILTER = ["corporate actions", "AGM", "meeting", "board changes", "notice of", "exchange", "price monitoring", "presentation", "call", "placing"] 

    def handle(self, request):
        company_symbol = request.get('company_symbol', None)
        
        news_count = int(request.get('research', 0))
        news_items = []

        # Define base URL for scraping
        scrape_todays_news = True
        if company_symbol:
            self.NEWS_FILTER = ["half", "full", "final", "interim", "financial", "trading update"]
            if news_count: 
                self.NEWS_FILTER = []
                
            else: 
                news_count = 1 # If we are not doing research to a company, we only need the latest report.

            investegate_url = f"https://www.investegate.co.uk/company/{company_symbol}"
            scrape_todays_news = False
        else:
            investegate_url = f"https://www.investegate.co.uk/source/RNS"

        # Start pagination loop
        page = 1
        is_break = False
        while True:
            url = f"{investegate_url}?page={page}";
            print("processing", url)

            response = requests.get(url, headers=self.HEADERS)
            soup = BeautifulSoup(response.content, "html.parser")

            news_table = soup.find("table", class_="table-investegate")
            if not news_table:
                break  # Exit if no news table is found

            rows = news_table.find_all("tr")
            
            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 4:
                    continue  # Skip rows with insufficient data

                # Extract date and time
                news_date = cells[0].text.strip()
                today = datetime.now().strftime("%d %b %Y")

                # Check if the news is from today
                
                if scrape_todays_news and news_date.split(' ')[0:3] != today.split(' ')[0:3]:
                    is_break = True
                    break  # Skip if not today's news

                # Extract company symbol and headline
                company_info = cells[2].find("a")
                headline_info = cells[3].find("a")

                if company_info and headline_info:                    
                    symbol = company_info['href'].split('/')[-1]
                    if not scrape_todays_news:
                        symbol = company_symbol
                        
                    headline = headline_info.text.strip()
                    announcement_link = headline_info['href']

                    # Exclude based on NEWS_EXCLUDE_FILTER
                    if any(term in headline.lower() for term in self.NEWS_EXCLUDE_FILTER):
                        continue

                    
                    if len(self.NEWS_FILTER)>0:
                        # Include based on NEWS_FILTER
                        if any(term in headline.lower() for term in self.NEWS_FILTER):
                            news_items.append({
                                "time": news_date,
                                "company_symbol": symbol,
                                "headline": headline,
                                "announcement_link": announcement_link,
                            })
                    else:
                        news_items.append({
                            "time": news_date,
                            "company_symbol": symbol,
                            "headline": headline,
                            "announcement_link": announcement_link,
                        })                        
                    
                    if news_count>0 and len(news_items) >= news_count: 
                            break
                            

            # Increment the page for pagination
            page += 1  # Move to the next page
            if is_break or (news_count>0 and len(news_items) >= news_count): #break the While true loop
                break
        # Populate request with the filtered news
        if news_items:
            request['news'] = news_items
        else:
            request['recommendation'] = 'NO RELEVANT NEWS'
            request['reasons'] = ["No relevant financial news found"]
        
        return super().handle(request)
