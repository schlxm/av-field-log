import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time

# --- CONFIG ---
st.set_page_config(page_title="AV Field Log", page_icon="📱", layout="centered")

# --- GOOGLE SHEETS CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- APP UI ---
st.title("🎙️ AV Field Log")

# 1. ROOM NAME INPUT
raw_code = st.text_input("Enter Room Name") 
room_code = raw_code.strip().upper()

if room_code:
    
    # --- SMART INITIALIZATION LOGIC ---
    try:
        existing_data = conn.read(worksheet="logs", ttl="0s")
    except:
        existing_data = pd.DataFrame()
        
    room_constraints = ""
    t_infra = False
    t_ft = False
    t_ori = False
    t_lh = False
    t_ph = False
    
    # Check if user manually triggered a clear slate
    force_clear_key = f"clear_{room_code}"
    if force_clear_key not in st.session_state:
        st.session_state[force_clear_key] = False

    if not existing_data.empty and 'RoomCode' in existing_data.columns and not st.session_state[force_clear_key]:
        match = existing_data[existing_data['RoomCode'] == room_code]
        if not match.empty:
            last_row = match.iloc[-1]
            # If the last event wasn't a DEBRIEF, load the active state
            if last_row.get('Category', '') != 'DEBRIEF':
                room_constraints = last_row.get('Constraints', '') if pd.notna(last_row.get('Constraints')) else ""
                t_infra = last_row.get('InfrastructureStatus', '') == 'STABLE'
                t_ft = last_row.get('FinalTouches', '') == 'YES'
                t_ori = last_row.get('Orientation', '') == 'YES'
                t_lh = last_row.get('EventLeadHandshake', '') == 'YES'
                t_ph = last_row.get('PartnerHandshake', '') == 'YES'

    # --- TAB NAVIGATION (Native) ---
    tab1, tab2, tab3 = st.tabs(["🛠️ Setup", "⚡ Live Event", "📝 Debrief"])

    # --- TAB 1: SETUP ---
    with tab1:
        safety_notes = st.text_area("Constraints", 
                                    value=room_constraints,
                                    placeholder="Type constraints here during prep...")
        
        col1, col2 = st.columns(2)
        with col1:
            infra = st.toggle("Infrastructure Stable", value=t_infra)
            final_touches = st.toggle("Final Touches", value=t_ft)
            orientation = st.toggle("Orientation", value=t_ori)
        with col2:
            handshake = st.toggle("Lead Handshake", value=t_lh)
            partner_handshake = st.toggle("Partner Handshake", value=t_ph)

        st.write("") # Spacing
        if st.button("Launch Event", use_container_width=True, type="primary"):
            st.session_state[force_clear_key] = False # Lock in the active state
            
            new_entry = pd.DataFrame([{
                "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "RoomCode": room_code,
                "Category": "SYNC",
                "Note": "System Normalized",
                "InfrastructureStatus": "STABLE" if infra else "PENDING",
                "Constraints": safety_notes,
                "EventLeadHandshake": "YES" if handshake else "NO",
                "FinalTouches": "YES" if final_touches else "NO",
                "Orientation": "YES" if orientation else "NO",
                "PartnerHandshake": "YES" if partner_handshake else "NO",
                "Linked_Event": "",
                "Debrief_General": "",
                "Debrief_Cons
