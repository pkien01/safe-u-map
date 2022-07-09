from datetime import datetime
from bs4 import BeautifulSoup
from dateutil import parser
import re
import requests
import pandas as pd
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline
import os
import gmaps
from ipywidgets.embed import embed_minimal_html
from git import Repo
from safe_u import API_KEY_WEB
#import dill as pickle

def scrape_page(page_url, as_of_date):
    page = requests.get(page_url)
    if not page.ok:
        raise ValueError(f"Unable to connect to {page_url}.")

    soup = BeautifulSoup(page.content, 'html.parser')
    rows = soup.find_all("div", {"class": "views-row"})
    if len(rows) == 0: return []
    res = []
    for child in rows:
        date = child.find("span", {"class": "field-content full-blog-dateline"}).getText()
        date = parser.parse(date)
        if as_of_date is not None and date <= as_of_date: break
        content = child.find("div", {"class": "field-content full-blog-abstract"}).getText()
        content = content.replace("U of M Twin Cities: ", "")
        content = re.sub("Updates(.|\n)*umn(.|\n)*alerts\.?", "", content).strip()
        res.append([date, content])
    return res

URL = "https://publicsafety.umn.edu/alerts?block_config_key=x8u9VTODUJhI1ckCL3bmI5KfdUfetN6a_8GLt3qajbM&page=%d"

def scan_new_data(geolocator, as_of_date):
    all_rows = []
    for i in range(1000):
        page_rows = scrape_page(URL % i, as_of_date)
        if len(page_rows) == 0: 
            print("Stopped at page", i)
            break
        all_rows.extend(page_rows)
    df = pd.DataFrame(all_rows, columns=['Date', 'Content'])
    df['Location'] = retrieve_locations(df['Content'], geolocator)
    df['Checked'] = False
    print("Found %d new alerts on website" % len(df))
    return df

def load_old_df(save_name='saved_data.pkl'):
    save_dir = os.path.join(os.path.dirname(__file__), save_name)
    try:
        df = pd.read_pickle(save_dir)
        #with open(save_dir, 'rb') as f:
        #    df = pickle.load(f)
        df['Date'] = pd.to_datetime(df['Date'])
        df['Content'] = df['Content'].astype("string")
        df['Location'] = df['Location'].apply(lambda x: list(x))
        df['Checked'] = df['Checked'].astype(bool)
        print(f"Loaded old data from {save_name}.")

    except IOError:
        df = pd.DataFrame([], columns=['Date', 'Content', 'Location', 'Checked'])
        print(f"{save_name} not found. Assigned an empty dataframe.")
    
    return df

WEB_REPO_PATH = "pkien01.github.io"
def git_push():
    try:
        repo = Repo(WEB_REPO_PATH)
        repo.git.add(update=True)
        repo.index.commit(f"Update Safe-U Alerts Map (map.html) on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        origin = repo.remote(name='origin')
        origin.push()
    except:
        print('Some error occured while pushing the code')   

def save_df(df, save_name='saved_data.pkl', export_html='map.html'):
    save_dir = os.path.join(os.path.dirname(__file__), save_name)
    df.to_pickle(save_dir)
    print(f"Saved data to {save_name}.")
    #with open(save_dir, 'wb') as f:
    #    pickle.dump(df, f)
    coords = sum(df['Location'].apply(lambda lst: [x[1:] for x in lst]).tolist(), [])
    fig = gmaps.figure()
    heatmap_layer = gmaps.heatmap_layer(coords, point_radius=15, opacity=0.75)
    fig.add_layer(heatmap_layer)
    export_html_dir = os.path.join(WEB_REPO_PATH, export_html)
    embed_minimal_html(export_html_dir, views=[fig], title='Safe U Alerts Geographical Heat Map')
    print(f"Exported gmaps data to {export_html_dir}.")
    git_push()
    print("Successfully pushed to github.")

def extract_locations_bert(sentence, ner, geolocator):
    entities = ner(sentence)
    intervals = [[ent['start'], ent['end']] for ent in entities if ent['entity'].endswith('LOC')]
    if len(intervals) == 0: return []
    intervals.sort()
    merged_intervals = [intervals[0]]
    for l, r in intervals[1:]:
        prev_r = merged_intervals[-1][1]
        if prev_r + 1 < l and not all(sentence[i] == ' ' for i in range(prev_r + 1, l)):
            merged_intervals.append([l, r]) 
        else:
            merged_intervals[-1][1] = max(prev_r, r)
  
    res = []
    for l, r in merged_intervals:
        address = sentence[l:r] + ", Minneapolis MN"
        location = geolocator.geocode(address,  timeout=10)
        #print(location.address)
        #coords.append((location.latitude, location.longitude))
        res.append((location.address, location.latitude, location.longitude))
    return res

def retrieve_locations(df_content, geolocator):
    tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
    model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")

    ner = pipeline("ner", model=model, tokenizer=tokenizer)
    return df_content.apply(extract_locations_bert, ner=ner, geolocator=geolocator)