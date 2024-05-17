from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: SecretStr
    api_key: SecretStr

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

 
config = Settings()
