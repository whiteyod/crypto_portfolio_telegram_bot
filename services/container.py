from config_reader import config
from services.cmc import CmcClient
from services.quote_cache import QuoteCache


# One common CMC client for bot
cmc = CmcClient(config.api_key.get_secret_value())

# One shared cache for bot
quotes_cache = QuoteCache(ttl_seconds=45)
