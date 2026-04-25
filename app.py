import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# --- CONFIG ---
st.set_page_config(page_title="AV Field Log", page_icon="📱", layout="centered")

# --- GOOGLE SHEETS CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)


# --- APP UI ---
st.title("🎙️ AV Field Log")

# 1. ROOM CODE INPUT
raw_code = st.text_input("Enter Room Code", placeholder="e.g., PARLOR, VISTA")
room_code = raw_code.strip().upper()

if room_code:
    # --- PHASE 1: PREP & NORMALIZATION ---
    with st.expander(f"🛠️ Prep & Constraints: {room_code}", expanded=True):
        st.info("Engineering constraints sync across all devices.")
        
        # Pull existing constraints to populate the field
        try:
            existing_data = conn.read(worksheet="logs", ttl="0s")
            if not existing_data.empty:
                # Get the most recent constraints for this specific room
                match = existing_data[existing_data['RoomCode'] == room_code]
                room_constraints = match.iloc[-1]['Constraints'] if not match.empty else ""
            else:
                room_constraints = ""
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
            new_entry = pd.DataFrame([{
                "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "RoomCode": room_code,
                "Category": "SYNC",
                "Note": "System Normalized",
                "InfrastructureStatus": "STABLE" if infra else "PENDING",
                "Constraints": safety_notes,
                "EventLeadHandshake": "YES" if handshake else "NO"
            }])
            
            # The "Read-Append-Update" Method
            # This avoids the 'UnsupportedOperation' error by not trying to 'create' anything
            df = conn.read(worksheet="logs", ttl="0s")
            updated_df = pd.concat([df, new_entry], ignore_index=True).dropna(how='all')
            conn.update(worksheet="logs", data=updated_df)
                
            st.success(f"Synced {room_code} to the cloud.")

    st.divider()

    # --- PHASE 2: LIVE ACTION BUTTONS ---
    st.subheader("⚡ Live Action Log")
    
    c1, c2 = st.columns(2)
    
    def log_event(category):
        log_entry = pd.DataFrame([{
            "Timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "RoomCode": room_code,
            "Category": category,
            "Note": "Action Button Pressed",
            "InfrastructureStatus": "",
            "Constraints": safety_notes,
            "EventLeadHandshake": ""
        }])
        
        try:
            df = conn.read(worksheet="logs", ttl="0s")
            updated_df = pd.concat([df, log_entry], ignore_index=True).dropna(how='all')
            conn.update(worksheet="logs", data=updated_df)
            st.toast(f"Logged {category}")
        except Exception as e:
            st.error(f"Sync Error: {e}")

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
    st.warning("Please enter a Room Code to sync data.")
