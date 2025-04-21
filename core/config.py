# -*- coding: utf-8 -*-
import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "default_key")


settings = Settings()
