from flask import Flask, render_template, request, jsonify
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from datetime import datetime

app = Flask(__name__)

# --- SPOTIFY API SETUP ---
CLIENT_ID = "bb4ecfcf3a3d4a2294342d5da5a5f43d"
CLIENT_SECRET = "60e7a1f95c5241ce91a099223b480a72"

try:
    auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    print("Spotify API Connected!")
except:
    print("Spotify API Error!")

# Load Data 
df = pd.read_csv('master_music_data.csv', low_memory=False, dtype={'genre': str, 'lyrics': str})

features = ["valence", "danceability", "energy", "tempo", 
            "acousticness", "instrumentalness", "speechiness", "popularity"]

df[features] = df[features].fillna(0.5)
scaler = MinMaxScaler()
df_scaled = scaler.fit_transform(df[features])

def get_spotify_info(song_name, artist_name):
    try:
        clean_artist = str(artist_name).replace("[", "").replace("]", "").replace("'", "").split(",")[0]
        query = f"track:{song_name} artist:{clean_artist}"
        results = sp.search(q=query, type='track', limit=1)
        
        if not results['tracks']['items']:
            results = sp.search(q=song_name, type='track', limit=1)

        if results['tracks']['items']:
            track = results['tracks']['items'][0]
            album_art = track['album']['images'][0]['url'] if track['album']['images'] else None
            preview = track.get('preview_url')
            return album_art, preview
    except:
        pass
    return None, None

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('q', '').lower()
    if not query: return jsonify([])
    
    song_matches = df[df['name'].str.lower().str.contains(query, na=False)]['name'].dropna().unique().tolist()
    artist_matches_raw = df[df['artists'].str.lower().str.contains(query, na=False)]['artists'].dropna().unique().tolist()
    
    cleaned_artists = []
    for a in artist_matches_raw:
        clean_a = str(a).replace("[", "").replace("]", "").replace("'", "").replace('"', "").split(",")[0].strip()
        if query in clean_a.lower(): cleaned_artists.append(clean_a)
            
    suggestions = list(set(song_matches[:10] + cleaned_artists[:10]))
    return jsonify(sorted(suggestions)[:10])

# --- RETRO MODE ADDED HERE ---
def recommend_songs(search_query, retro_mode=False, num_recs=10):
    query = search_query.strip().lower()
    
    song_selection = df[df['name'].str.lower() == query]
    if song_selection.empty: song_selection = df[df['name'].str.lower().str.contains(query, na=False)]
    if song_selection.empty: song_selection = df[df['artists'].str.lower().str.contains(query, na=False)]
    if song_selection.empty: return None
    
    idx = song_selection.index[0]
    target_lang = song_selection.iloc[0].get('language', 'English')
    
    song_vector = df_scaled[idx].reshape(1, -1)
    similarities = cosine_similarity(song_vector, df_scaled).flatten()
    
    current_year = datetime.now().year
    rec_scores = 1 / (current_year - df['year'].fillna(2010) + 1)
    rec_scores = (rec_scores - rec_scores.min()) / (rec_scores.max() - rec_scores.min())
    pop_scores = df['popularity'] / 100
    
    df['hybrid_score'] = (similarities * 0.6) + (rec_scores * 0.2) + (pop_scores * 0.2)
    
    if 'language' in df.columns:
        df.loc[df['language'] == target_lang, 'hybrid_score'] += 0.2
    df.loc[df['artists'].str.lower().str.contains(query, na=False), 'hybrid_score'] += 1.0
    
    # MAGIC: THE TIME MACHINE FILTER
    if retro_mode:
        # 1990 se 2005 ke beech ke gaane filter karo
        valid_indices = df[(df['year'] >= 1990) & (df['year'] <= 2005)].index
        valid_indices = valid_indices[valid_indices != idx] # Remove searched song
        indices = df.loc[valid_indices].sort_values(by='hybrid_score', ascending=False).head(num_recs).index
    else:
        indices = df[df.index != idx].sort_values(by='hybrid_score', ascending=False).head(num_recs).index
        
    recommendations = df.loc[indices, ["name", "year", "artists", "language"]].to_dict(orient='records')
    
    for rec in recommendations:
        img, preview = get_spotify_info(rec['name'], rec['artists'])
        rec['image_url'], rec['preview_url'] = img, preview
        
    return recommendations

@app.route("/")
def index():
    return render_template('index.html', retro_mode=False)

@app.route("/recommend", methods=["POST"])
def recommend():
    song_name = request.form.get("song_name")
    retro_mode = request.form.get("retro_mode") == "true" # Check toggle status
    
    results = recommend_songs(song_name, retro_mode)
    
    if results is None:
        return render_template('index.html', error=f"'{song_name}' not found.", retro_mode=retro_mode)
    
    # Agar retro mode ON hai aur list khali aati hai
    if len(results) == 0 and retro_mode:
        return render_template('index.html', error=f"'{song_name}' ke vibe ke 90s ke gaane nahi mile!", retro_mode=retro_mode)

    return render_template('index.html', recommendations=results, searched_song=song_name, retro_mode=retro_mode)

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)