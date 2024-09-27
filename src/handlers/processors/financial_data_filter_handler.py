from handlers.abstract_handler import AbstractHandler

class FinancialDataFilterHandler(AbstractHandler):
    # Keywords that suggest the presence of financial data
    FINANCIAL_KEYWORDS = ["revenue", "profit", "ebitda", "dividends", "net income", "gross profit", "increase", "dividend", "net inflows"]

    def handle(self, request):
        # Check if the request contains the necessary data
        if 'text' not in request:
            request['recommendation'] = 'SKIP'
            request['reasons'] = ["No financial data in the report"]
            return request  # Return early to halt the chain

        report_text = request['text'].lower()

        # Check if the report contains any of the financial keywords
        if not any(keyword in report_text for keyword in self.FINANCIAL_KEYWORDS):
            request['recommendation'] = 'SKIP'
            request['reasons'] = ["The report does not contain meaningful financial data"]
            return request  # Return early to halt the chain

        # If the report contains financial data, proceed with the chain
        return super().handle(request)
