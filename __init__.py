from dotenv import load_dotenv
import os
import gmaps
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
BOT_TOKEN = os.environ['BOT_TOKEN']
GMAP_API_KEY = os.environ['GMAP_API_KEY']
USER_ID = os.environ['USER_ID']

gmaps.configure(api_key=GMAP_API_KEY)