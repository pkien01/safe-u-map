from ipywidgets.embed import embed_minimal_html
import gmaps
from scraper import load_old_df

import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
GMAP_API_KEY = os.environ['GMAP_API_KEY']

def export_html(coords):
    gmaps.configure(api_key=GMAP_API_KEY)
    fig = gmaps.figure()
    heatmap_layer = gmaps.heatmap_layer(coords, point_radius=15, opacity=0.75)
    fig.add_layer(heatmap_layer)
    embed_minimal_html('safeumap.github.io/export.html', views=[fig])

if __name__ == "__main__":
    df = load_old_df()
    export_html(sum((df['Location'].apply(lambda lst: [x[1:] for x in lst]).tolist()), []))