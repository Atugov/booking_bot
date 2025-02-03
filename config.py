import os
from dotenv import load_dotenv
from typing import Final

# Load environment variables from .env file
load_dotenv()

TOKEN: Final = os.getenv("BOT_TOKEN")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME")
SUPABASE_URL: Final = os.getenv("SUPABASE_URL")
SUPABASE_KEY: Final = os.getenv("SUPABASE_KEY")
# Test6