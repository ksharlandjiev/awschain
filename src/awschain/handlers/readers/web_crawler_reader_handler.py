from ..abstract_handler import AbstractHandler
from ...utils.web_utils import fetch_webpage, clean_html
import requests
from bs4 import BeautifulSoup

class WebCrawlerReaderHandler(AbstractHandler):

    def handle(self, request: dict) -> dict:
        print("[WebCrawlerReaderHandler][handle]")
        # Assuming request.search is a dict with 'category' and 'terms'
        search_info = request.get('search', {})
        category = search_info.get('category')
        terms = search_info.get('terms', [])
        
        # Generate search query and perform the search
        search_query = f"{category}%20{'%20'.join(terms)}"
        urls = self.google_page_search(search_query)

        all_text = []
        # Fetch and sanitize the web pages from the search results
        for url in urls:
            print(f"Fetching data from: {url}")
            html_content = fetch_webpage(url)
            if html_content:
                clean_text = clean_html(html_content)
                all_text.append(clean_text)
                print("Web page content fetched and cleaned successfully.")
            else:
                print("Failed to fetch web page content.")

        # Update the request object with the consolidated text from all fetched web pages
        request.update({"text": ' '.join(all_text)})
        
        return super().handle(request)

    def google_page_search(self, query: str) -> list:
        # Assuming usage of Google Search, adjust query for API or scraping
        # For the purpose of this example, let's pretend to scrape Google, which you should replace with an API usage
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'}
        response = fetch_webpage(f"https://www.google.com/search?q={query}")
        print(response)
        soup = BeautifulSoup(response.text, 'html.parser')
        print(clean_html(soup))
        # Find all non-promoted search results; this depends on Google's markup, usually class 'g'
        search_results = []
        for g in soup.find_all('div', class_='g'):
            rc = g.find('div', class_='rc')
            if rc:
                link = rc.find('a', href=True)
                if link and link['href'].startswith('http'):
                    search_results.append(link['auth'])
        return search_results
