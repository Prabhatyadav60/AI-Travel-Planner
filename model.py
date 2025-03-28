import streamlit as st
import requests
import json
import os
import toml  # Missing import
import re
import time

if "api" in st.secrets:
    API_KEY = st.secrets["api"]["key"]  
else:
    secrets_path = ".streamlit/secrets.toml"
    if os.path.exists(secrets_path):
        secrets = toml.load(secrets_path)
        API_KEY = secrets["api"]["key"]
    else:
        st.error("🚨 No API key found! Add it to Streamlit Secrets or a local secrets.toml file.")
        st.stop()


URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
headers = {"Content-Type": "application/json"}


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "step" not in st.session_state:
    st.session_state.step = 0
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "itinerary_generated" not in st.session_state:
    st.session_state.itinerary_generated = False  # Ensure it generates only once

def generate_itinerary():
    """Sends request to Gemini API and returns a generated itinerary."""
    user_data = st.session_state.user_data
    prompt = (
        f"Plan a detailed {user_data['duration']}-day itinerary for {user_data['destination']}. "
        f"The traveler has a {user_data['budget']} budget, prefers {user_data['accommodation']} accommodation, "
        f"and is interested in {user_data['interests']}. Their dietary preference is {user_data['dietary']}. "
        f"They are specifically interested in {user_data['specific_interests']}. "
        f"They have mobility concerns: {user_data['mobility']}. "
        f"Additional requirements: {user_data['additional_reqs']}. "
        f"Include morning, afternoon, and evening activities for each day."
    )

    data = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(URL, json=data, headers=headers)

    if response.status_code == 200:
        output = response.json()
        try:
            return output["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return "Error: Unexpected response format."
    else:
        return f"Error {response.status_code}: {response.text}"

st.title("🗺️ AI Travel Chatbot")
st.write("Plan your trip through a friendly chatbot! Answer step-by-step questions.")
st.write("Hello! I'm your friendly travel assistant. Ready to plan your next adventure? Let's get started by exploring where you'd like to go!")

# Display previous chat messages
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Questions for user input
questions = [
    "📍 Where are you traveling to?",
    "📅 How many days will you stay?",
    "💰 What is your budget? (low, moderate, luxury)",
    "🎭 What are your interests? (e.g., sightseeing, adventure, food)",
    "🏨 What type of accommodation do you prefer? (luxury, budget, central location, etc.)",
    "🍽️ Any dietary preferences or restrictions? (e.g., vegetarian, halal, none)",
    "🔍 Do you have any specific interests within your preferences? (e.g., art, local cuisine, historical sites)",
    "🚶‍♂️ Do you have any walking tolerance or mobility concerns? (e.g., limited walking, wheelchair accessible, none)",
    "✏️ Do you have any additional specific requirements?"
]

# Process user responses step by step
if st.session_state.step < len(questions):
    user_input = st.chat_input(questions[st.session_state.step])
    
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Store user responses
        if st.session_state.step == 0:
            st.session_state.user_data["destination"] = user_input
        elif st.session_state.step == 1:
            duration = ''.join(filter(str.isdigit, user_input)) or "1"
            st.session_state.user_data["duration"] = int(duration)
        elif st.session_state.step == 2:
            st.session_state.user_data["budget"] = user_input.lower()
        elif st.session_state.step == 3:
            st.session_state.user_data["interests"] = user_input
        elif st.session_state.step == 4:
            st.session_state.user_data["accommodation"] = user_input.lower()
        elif st.session_state.step == 5:
            st.session_state.user_data["dietary"] = user_input.lower()
        elif st.session_state.step == 6:
            st.session_state.user_data["specific_interests"] = user_input
        elif st.session_state.step == 7:
            st.session_state.user_data["mobility"] = user_input
        elif st.session_state.step == 8:
            st.session_state.user_data["additional_reqs"] = user_input
        
        st.session_state.chat_history.append({"role": "assistant", "content": questions[st.session_state.step]})
        st.session_state.step += 1
        st.rerun()

# Generate itinerary after collecting all inputs
elif not st.session_state.itinerary_generated:
    with st.spinner("🔍 Generating your itinerary..."):
        itinerary = generate_itinerary()
    
    st.session_state.chat_history.append({"role": "assistant", "content": "🎉 Here is your personalized travel itinerary:"})
    st.session_state.chat_history.append({"role": "assistant", "content": itinerary})
    
    st.session_state.itinerary_generated = True
    st.rerun()

# Reset app
if st.sidebar.button("🔄 Start Over"):
    st.session_state.clear()
