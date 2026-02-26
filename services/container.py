from config_reader import config
from services.cmc import CmcClient
from services.quote_cache import QuoteCache

from typing import Iterable


# One common CMC client for bot
cmc = CmcClient(config.api_key.get_secret_value())

# One shared cache for bot
quotes_cache = QuoteCache(ttl_seconds=45)

# Helper function to get quotes from cache or CMC
async def get_quotes(symbols: Iterable[str]):
    '''
    Try to get quotes data from cache.
     If no cache get quotes from CMC instead and add it to the cache
    '''
    cache_key = 'quotes:' + ','.join(sorted(symbols))
    quotes = quotes_cache.get(cache_key)
    if quotes is None:
        quotes = cmc.get_quotes_usd(symbols)
        quotes_cache.set(cache_key, quotes)

        return quotes
    else:
        return quotes

