import json


class Tradier(object):
    def __init__(self, httpclient, token):
        self.httpclient = httpclient
        self.token = token
        self.user = Tradier.User(self)
        self.accounts = Tradier.Accounts(self)
        self.markets = Tradier.Markets(self)
        self.fundamentals = Tradier.Fundamentals(self)
        self.options = Tradier.Options(self)
        self.watchlists = Tradier.Watchlists(self)

    def request(
            self,
            method,
            path,
            headers=None,
            params=None,
            data=None,
            callback=None):

        headers = headers or {}
        headers['Authorization'] = 'Bearer %s' % self.token
        headers['Accept'] = 'application/json'

        def base_callback(response):
            if response.code != 200:
                raise Exception(response.code, response.body)
            return json.loads(response.body)

        if callback == None:
            cb = base_callback
        else:
            cb = lambda x: callback(base_callback(x))

        return self.httpclient.request(
            cb,
            method,
            path,
            headers=headers,
            params=params,
            data=data)

    class User(object):
        def __init__(self, agent):
            self.agent = agent

        def profile(self):
            response = self.agent.request('GET', 'user/profile')
            return response

        def balances(self):
            response = self.agent.request('GET', 'user/balances')
            return response

    class Accounts(object):
        def __init__(self, agent):
            self.agent = agent

        def orders(self, account_id):
            response = self.agent.request(
                'GET', 'accounts/%s/orders' % account_id)
            return response['orders']['order']

        def order(self, account_id, order_id):
            response = self.agent.request(
                'GET', 'accounts/%s/orders/%s' % (account_id, order_id))
            return response

    class Markets(object):
        def __init__(self, agent):
            self.agent = agent

        def clock(self, year=None, month=None):
            def callback(response):
                quote = response['clock']
                return quote
            params = {}
            return self.agent.request(
                'GET',
                'markets/clock',
                params=params,
                callback=callback)

        def calendar(self, year=None, month=None):
            def callback(response):
                quote = response['calendar'].get('days', [{}]).get('day')
                if not isinstance(quote, list):
                    quote = [quote]
                return quote
            params = {}
            if year is not None:
                params['year'] = year
            if month is not None:
                params['Month'] = month
            return self.agent.request(
                'GET',
                'markets/calendar',
                params=params,
                callback=callback)         

        def lookup(self, query):
            def callback(response):
                quote = response['securities'].get('security', [])
                if not isinstance(quote, list):
                    quote = [quote]
                return quote
            return self.agent.request(
                'GET',
                'markets/lookup',
                params={'q': query},
                callback=callback)         

        def quotes(self, symbols):
            def callback(response):
                quote = response['quotes'].get('quote', [])
                if not isinstance(quote, list):
                    quote = [quote]
                return quote
            return self.agent.request(
                'GET',
                'markets/quotes',
                params={'symbols': ','.join(symbols)},
                callback=callback)

        def history(self, symbol, start=None, end=None, interval=None):
            def callback(response):
                quote = response['history'].get('day', [])
                if not isinstance(quote, list):
                    quote = [quote]
                return quote
            params={'symbol': symbol}
            if start is not None:
                params['start'] = start
            if end is not None:
                params['end'] = end
            if interval is not None:
                assert False, 'interval must be None' # TODO BUG
                params['interval'] = interval
            return self.agent.request(
                'GET',
                'markets/history',
                params=params,
                callback=callback)

    class Fundamentals(object):
        def __init__(self, agent):
            self.agent = agent

        def calendars(self, symbols):
            def callback(response):
                return response
            return self.agent.request(
                'GET',
                'markets/fundamentals/calendars',
                params={'symbols': ','.join(x.upper() for x in symbols)},
                callback=callback)

    class Options(object):
        def __init__(self, agent):
            self.agent = agent

        def expirations(self, symbol):
            return self.agent.request(
                'GET',
                'markets/options/expirations',
                params={'symbol': symbol},
                callback=(lambda x: x['expirations']['date']))
        
        def strikes(self, symbol, expiration):
            return self.agent.request(
                'GET',
                'markets/options/strikes',
                params={'symbol': symbol,
                        'expiration': expiration},
                callback=(lambda x: x['strikes']['strike']))

        def chains(self, symbol, expiration):
            def callback(response):
                if response['options']:
                    return response['options']['option']
                return []
            return self.agent.request(
                'GET',
                'markets/options/chains',
                params={'symbol': symbol, 'expiration': expiration},
                callback=callback)

    class Watchlists(object):
        def __init__(self, agent):
            self.agent = agent

        def __call__(self):
            response = self.agent.request('GET', 'watchlists')
            return response['watchlists']['watchlist']

        def get(self, watchlist_id):
            response = self.agent.request(
                'GET', 'watchlists/%s' % watchlist_id)
            return response['watchlist']

        def create(self, name, *symbols):
            response = self.agent.request(
                'POST',
                'watchlists',
                params={'name': name, 'symbols': ','.join(list(symbols))})
            return response['watchlist']

        def delete(self, watchlist_id):
            response = self.agent.request(
                'DELETE', 'watchlists/%s' % watchlist_id)
            return response['watchlists']['watchlist']
