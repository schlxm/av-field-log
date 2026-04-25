import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# --- CONFIG ---
st.set_page_config(page_title="AV Field Log", page_icon="📱", layout="centered")

# --- GOOGLE SHEETS CONNECTION ---
# This uses the secrets you already saved in the Streamlit Dashboard
conn = st.connection("gsheets", type=GSheetsConnection)

# --- APP UI ---
st.title("🎙️ AV Field Log")

# 1. ROOM CODE INPUT (Case Insensitive & Stripped of Spaces)
raw_code = st.text_input("Enter Room Code", placeholder="e.g., PARLOR, VISTA")
room_code = raw_code.strip().upper()

if room_code:
    # --- PHASE 1: PREP & NORMALIZATION ---
    with st.expander(f"🛠️ Prep: {room_code}", expanded=True):
        st.info("Engineering Constraints sync across all devices.")
        
        # We wrap this in a try/except in case the sheet is totally empty
        try:
            existing_data = conn.read(worksheet="logs", ttl="0s") # ttl=0 means no cache, live data
            match = existing_data[existing_data['RoomCode'] == room_code]
            room_constraints = match.iloc[-1]['Constraints'] if not match.empty else ""
        except:
            room_constraints = ""

        safety_notes = st.text_area("Engineering/Safety Constraints", 
                                    value=room_constraints,
                                    placeholder="Type constraints here during prep...")
        
        col1, col2 = st.columns(2)
        with col1:
            infra = st.toggle("Infrastructure Stable")
        with col2:
            handshake = st.toggle("Lead Handshake")

        if st.button("Save Prep / Sync All Devices"):
            launch_entry = pd.DataFrame([{
                "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "RoomCode": room_code,
                "Category": "SYNC",
                "Note": "System Normalized",
                "InfrastructureStatus": "STABLE" if infra else "PENDING",
                "Constraints": safety_notes,
                "EventLeadHandshake": "YES" if handshake else "NO"
            }])
            # Append the new data to the sheet
            conn.create(worksheet="logs", data=launch_entry)
            st.success(f"Successfully synced {room_code} to the cloud.")

    st.divider()

    # --- PHASE 2: LIVE LOG (THE TRUMP CARD) ---
    st.subheader("⚡ Live Action Buttons")
    
    c1, c2 = st.columns(2)
    
    def log_event(category):
        log_entry = pd.DataFrame([{
            "Timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "RoomCode": room_code,
            "Category": category,
            "Note": "Logged via Action Button",
            "InfrastructureStatus": "",
            "Constraints": safety_notes,
            "EventLeadHandshake": ""
        }])
        conn.create(worksheet="logs", data=log_entry)
        st.toast(f"Logged {category} to Sheet")

    with c1:
        if st.button("🔴 SENIOR LEADER OVERRIDE", use_container_width=True):
            log_event("Senior Leader Override")
        if st.button("🟡 MISSED DEADLINE", use_container_width=True):
            log_event("Missed Deadline")

    with c2:
        if st.button("🟠 SCOPE CREEP", use_container_width=True):
            log_event("Scope Creep")
        if st.button("🔵 TECHNICAL EVENT", use_container_width=True):
            log_event("Technical Event")

else:
    st.warning("Enter a Room Code to sync with your contractor.")
