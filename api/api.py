from operator import truediv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from assets.db import get_position_all, apply_buy, apply_sell
from api.tg_auth import verify_init_data, TelegramAuthError
from config_reader import config


BOT_TOKEN = config.bot_token

app = FastAPI()


# ------------------------------------ API Helpers --------------------------------------

def get_user_id_from_init_data(init_data: str) -> int:
    try:
        user = verify_init_data(init_data, BOT_TOKEN)
        return int(user['id'])
    except (TelegramAuthError, KeyError, ValueError) as e:
        raise HTTPException(satus_code=401, detail=str(e))


class BuyRequest(BaseModel):
    symbol: str
    price: float
    qty: float


class SellRequest(BaseModel):
    symbol: str
    price: float
    qty: float


# ----------------------------------- API Endpoints --------------------------------------

@app.get('/api/positions')
def positions(
    x_tg_init_data: str | None = Header(default=None, alias='X-TG-INIT-DATA'
)):
    user_id = get_user_id_from_init_data(x_tg_init_data or '')
    rows = get_position_all(user_id=user_id)

    return [
        {
            'symbol': f['symbol'],
            'qty': float(r['qty']),
            'avg_cost': float(r['avg_cost'])
        }
        for r in rowsś
    ]


@app.post('/api/buy')
def buy(
    req: BuyRequest, 
    x_tg_init_data: str | None = Header(default=None, alias='X-TG-INIT-DATA')
):
    user_id = get_user_id_from_init_data(x_tg_init_data or '')
    apply_buy(
        user_id=user_id,
        symbol=req.symbol.upper(),
        qty=req.qty,
        price=req.price
    )

    return {'ok': True}


@app.post('/api/sell')
def sell(
    req: SellRequest,
    x_tg_init_data: str | None = Header(default=None, alias='X-TG-INIT-DATA')
):
    user_id = get_user_id_from_init_data(x_tg_init_data or '')
    apply_sell(
        user_id=user_id,
        symbol=req.symbol.upper(),
        qty=req.qty,
        price=req.price
    )

    return {'ok': True}

