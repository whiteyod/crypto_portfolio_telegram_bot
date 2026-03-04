import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


class TelegramAuthError(Exception):
    pass


# Check user data before login to MiniApp
def verify_init_data(
    init_data: str, bot_token: str, max_age_seconds: int = 60 * 60
) -> dict:
    '''
    Verification helper to check user and bot's data before login to MiniApp
    '''
    if not init_data:
        raise TelegramAuthError('Missing initData')
    
    data = dict(parse_qsl(init_data, strict_parsing=True))

    received_hash = data.pop('hash', None)
    if not received_hash:
        raise TelegramAuthError('Missing hash')
    
    # Check if hash is not expired
    auth_date = int(data.get('auth_date', '0'))
    if max_age_seconds and (time.time() - auth_date) > max_age_seconds:
        raise TelegramAuthError('initData epired')
    
    data_check_string = '\n'.join(f'{k}={v}' for k, v in sorted(data.items()))

    # Encode bot's auth data
    secret_key = hmac.new(
        b'WebAppData', bot_token.encode(), hashlib.sha256
    ).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    # Check hash comparisson
    if not hmac.compare_digest(computed_hash, received_hash):
        raise TelegramAuthError('Invalid initData signature')
    
    user_raw = data.get('user')
    if not user_raw:
        raise TelegramAuthError('Missing user')

    return json.loads(user_raw)