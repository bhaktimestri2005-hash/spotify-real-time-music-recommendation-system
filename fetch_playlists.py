import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

# --- SETUP ---
CLIENT_ID = "bb4ecfcf3a3d4a2294342d5da5a5f43d"
CLIENT_SECRET = "60e7a1f95c5241ce91a099223b480a72"

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET))

# Aapki dono Playlists ki IDs
playlist_ids = [
    '37i9dQZEVXbMDoHDwVN2tF', # Pehli Playlist
    '37i9dQZEVXbLZ52XmnySJg'        # Doosri Playlist
]

def fetch_and_merge():
    file_name = 'master_music_data.csv'
    
    if os.path.exists(file_name):
        master_df = pd.read_csv(file_name)
    else:
        print("Error: master_music_data.csv nahi mili!")
        return

    new_songs = []

    for p_id in playlist_ids:
        print(f"Fetching data from playlist: {p_id}...")
        try:
            results = sp.playlist_tracks(p_id)
            tracks = results['items']
            
            for item in tracks:
                track = item['track']
                if not track: continue
                
                # Audio features (Energy, Tempo, etc.) fetch karo
                audio_feat = sp.audio_features(track['id'])[0]
                
                if audio_feat:
                    song_data = {
                        'name': track['name'],
                        'artists': str([a['name'] for a in track['artists']]), # String format like ['Artist']
                        'valence': audio_feat['valence'],
                        'danceability': audio_feat['danceability'],
                        'energy': audio_feat['energy'],
                        'tempo': audio_feat['tempo'],
                        'acousticness': audio_feat['acousticness'],
                        'liveness': audio_feat['liveness'],
                        'speechiness': audio_feat['speechiness'],
                        'instrumentalness': audio_feat['instrumentalness'],
                        'popularity': track['popularity'],
                        'year': int(track['album']['release_date'][:4]),
                        'language': 'Personal Playlist', # Category mark karne ke liye
                        'Cluster': 0 # Default cluster
                    }
                    new_songs.append(song_data)
        except Exception as e:
            print(f"Error in {p_id}: {e}")

    if new_songs:
        new_df = pd.DataFrame(new_songs)
        # Purane data ke saath merge karo
        updated_df = pd.concat([master_df, new_df], ignore_index=True)
        # Duplicates hatao
        updated_df.drop_duplicates(subset=['name', 'artists'], keep='first', inplace=True)
        
        # Save kardo
        updated_df.to_csv(file_name, index=False)
        print(f"Success! {len(new_songs)} gaane add ho gaye hain.")
        print(f"Ab total {len(updated_df)} gaane hain aapke dataset mein.")
    else:
        print("Koi naya gaana nahi mila.")

if __name__ == "__main__":
    fetch_and_merge()