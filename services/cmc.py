import json
from requests import Session
from typing import Iterable
from loguru import logger as log


CMC_QUOTES_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"


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
                log.info(f'We have an error: {e} >>> Add proper logging here!!!!')

        return out

