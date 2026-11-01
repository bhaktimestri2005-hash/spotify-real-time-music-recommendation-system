# Build a Music Recommendation System with Machine Learning | Recommendation System Using Spotify Dataset
import joblib
import pandas as pd
import streamlit as st

# 1. Rainfall Model Load kara
model = joblib.load('rainfall_model.joblib')

st.title('🎵 Spotify Real-time Music Recommendation System')

# 2. User Input for Weather / Region
state = st.selectbox(
    'Select State / Region', ['Maharashtra', 'Karnataka', 'Goa']
)
month = st.slider('Select Month', 1, 12, 6)

if st.button('Get Weather-Based Music'):
  # Prediction logic
  # predicted_rain = model.predict([[...]])

  # Dummy logic for demonstration
  is_raining = True  # Model output nusaar tharel

  if is_raining:
    st.success('🌧️ Weather is Rainy! Recommending Lofi & Cozy Vibes.')
    # Tumchya clustered_df madhun lofi songs filter karun dakhva
  else:
    st.success('☀️ Weather is Clear! Recommending Upbeat Party Songs.')
