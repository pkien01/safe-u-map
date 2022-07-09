from dotenv import load_dotenv
import os
import gmaps
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
BOT_TOKEN = os.environ['BOT_TOKEN']
API_KEY_LOCAL = os.environ['API_KEY_LOCAL']
API_KEY_WEB = os.environ['API_KEY_WEB']
USER_ID = os.environ['USER_ID']

gmaps.configure(api_key=API_KEY_WEB)