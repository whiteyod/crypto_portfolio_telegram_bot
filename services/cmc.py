from email.errors import NoBoundaryInMultipartDefect
from requests import Session
from typing import Collection, Iterable, Optional
from loguru import logger as log


CMC_QUOTES_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
CMC_INFO_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/info"



class CmcClient:
    def __init__(self, api_key: str):
        # Create one HTTP session fro CMC API
        self.session = Session()
        self.session.headers.update({
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': api_key,
        })

    def get_quotes_usd(self, symbols: Iterable[str]) -> dict[str, float]:
        ''' 
        Fetch prices for many symbols in ONE request.
        Returns mapping: {"BTC": 43000.12, "ETH": 2300.55, ...}
        '''
        # Normalize user input: change case, trim, remove empty items
        symbols = [s.upper().strip() for s in symbols if s and s.strip()]
        if not symbols:
            return {}
        # CMC support multiple symbols in one request
        params = {
            'symbol': ','.join(symbols),
            'convert': 'USD',
        }
        # Set timeout to prevent infinite hanging
        resp = self.session.get(CMC_QUOTES_URL, params=params, timeout=10)
        # Raise exception if status is 4xx/5xx
        resp.raise_for_status()

        payload = resp.json()
        data = payload.get('data', {})

        out: dict[str, float] = {}
        for s in symbols:
            # Skip sybmols that not exists to avoid errors
            try:
                out[s] = float(data[s]['quote']['USD']['price'])
            except Exception as e:
                log.info(f'We have an error: {e}')

        return out


    def get_assets_info(
        self,
        symbols: Iterable[str],
        *,
        fields: Optional[Collection[str]] = None,
        name: bool = True,
        symbol: bool = True,
        description: bool = False,
        market_cap: bool = True,
        change_24h: bool = True,
        volume_24h: bool = True,
        circulating_supply: bool = True,
        convert: str = 'USD'
    ) -> dict[str, dict]:
        '''
        Returns mapping like:
        {
          'BTC': {
            'name': 'Bitcoin',
            'symbol': 'BTC',
            'description': '...',
            'market_cap': 123,
            'change_24h': 1.23,
            'volume_24h': 456,
            'circulating_supply': 19_000_000
          }
        }
 
        Request selection:
        - Either pass fields={'name','description','market_cap'} ...
        - Or use booleans (description=True, etc.)
        '''

        # Normalize user input
        normalized = [s.upper().strip() for s in symbols if s and s.strip()]
        if not normalized:
            return {}

        # If fields list is provided, it overrides the boolean switches
        if fields is not None:
            wanted = set(fields)
        else:
            wanted = set()
            if name:
                wanted.add('name')
            if symbol:
                wanted.add('symbol')
            if description:
                wanted.add('description')
            if market_cap:
                wanted.add('market_cap')
            if change_24h:
                wanted.add('change_24h')
            if volume_24h:
                wanted.add('volume_24h')
            if circulating_supply:
                wanted.add('circulating_supply')

        # Metadata endpoint only when needed
        need_info = 'description' in wanted

        # Market data from quotes/latest
        quotes_params = {'symbol': ','.join(normalized), 'convert': convert}
        quotes_resp = self.session.get(
            CMC_QUOTES_URL, params=quotes_params, timeout=10
        )
        quotes_resp.raise_for_status()
        quotes_payload = quotes_resp.json()
        quotes_data = quotes_payload.get('data', {})

        # Metadata from info
        info_data = {}
        if need_info:
            info_params = {'symbol': ','.join(normalized)}
            info_resp = self.session.get(CMC_INFO_URL, params=info_params, timeout=10)
            info_resp.raise_for_status()
            info_payload = info_resp.json()
            info_data = info_payload.get('data', {})
        
        out: dict[str, dict] = {}

        for sym in normalized:
            q = quotes_data.get(sym)
            if not q:
                continue
            
            # Build only requsted keys
            row: dict[str, object] = {}

            if 'name' in wanted:
                row['name'] = q.get('name')
            if 'symbol' in wanted:
                row['symbol'] = q.get('symbol')

            quote = (q.get('quote') or {}).get(convert) or {}

            if 'market_cap' in wanted:
                row['market_cap'] = quote.get('market_cap')
            if 'change_24h' in wanted:
                row['change_24h'] = quote.get('percent_change_24h')
            if 'volume_24h' in wanted:
                row['volume_24h'] = quote.get('volume_24h')
            if 'circullating_supply' in wanted:
                row['circullating_supply'] = quote.get('circullating_supply')
            if 'decription' in wanted:
                meta = info_data.get(sym) or {}
                row['description'] = meta.get('description')
            
            out[sym] = row

        return out
                


