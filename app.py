import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# --- CONFIG & CUSTOM CSS ---
st.set_page_config(page_title="AV Field Log", page_icon="📱", layout="centered")

# CSS to force Multiselect tags to be Yellow
st.markdown("""
<style>
span[data-baseweb="tag"] {
    background-color: #FFD700 !important;
    color: black !important;
}
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "🛠️ Setup"

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

    # --- TAB NAVIGATION (Radio Menu workaround) ---
    tabs = ["🛠️ Setup", "⚡ Live Event", "📝 Debrief"]
    st.radio("Navigation", tabs, horizontal=True, label_visibility="collapsed", key="current_tab")
    st.divider()

    # --- TAB 1: SETUP ---
    if st.session_state.current_tab == "🛠️ Setup":
        
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
                "Debrief_Consumables": "",
                "Degraded_Gear": ""
            }])
            
            try:
                if existing_data.empty:
                    updated_df = new_entry
                else:
                    updated_df = pd.concat([existing_data, new_entry], ignore_index=True).dropna(how='all')
                conn.update(worksheet="logs", data=updated_df)
                
                # Snap to Live Event tab
                st.session_state.current_tab = "⚡ Live Event"
                st.rerun()
            except Exception as e:
                st.error(f"Sync Error: {e}")
                
        # Fail-safe to wipe ghost data if someone forgot to debrief
        st.write("")
        if st.button("Force Clear Setup (Wipe Slate)", use_container_width=True):
            st.session_state[force_clear_key] = True
            st.rerun()

    # --- TAB 2: LIVE EVENT ---
    elif st.session_state.current_tab == "⚡ Live Event":
        def log_event(category):
            # Fetch constraints so we append them to the log row
            current_constraints = room_constraints if 'room_constraints' in locals() else ""
            
            log_entry = pd.DataFrame([{
                "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "RoomCode": room_code,
                "Category": category,
                "Note": "Action Button Pressed",
                "InfrastructureStatus": "",
                "Constraints": current_constraints,
                "EventLeadHandshake": "",
                "FinalTouches": "",
                "Orientation": "",
                "PartnerHandshake": "",
                "Linked_Event": "",
                "Debrief_General": "",
                "Debrief_Consumables": "",
                "Degraded_Gear": ""
            }])
            
            try:
                df = conn.read(worksheet="logs", ttl="0s")
                updated_df = pd.concat([df, log_entry], ignore_index=True).dropna(how='all')
                conn.update(worksheet="logs", data=updated_df)
                st.toast(f"Logged {category}")
            except Exception as e:
                st.error(f"Sync Error: {e}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🟡 MISSED DEADLINE", use_container_width=True):
                log_event("Missed Deadline")
            st.write("") # Spacing for touch targets
            if st.button("🔵 TECHNICAL EVENT", use_container_width=True):
                log_event("Technical Event")

        with c2:
            if st.button("🟠 SCOPE CREEP", use_container_width=True):
                log_event("Scope Creep")
            st.write("") # Spacing for touch targets
            if st.button("🔴 LEADER OVERRIDE", use_container_width=True):
                log_event("Leader Override")

    # --- TAB 3: DEBRIEF ---
    elif st.session_state.current_tab == "📝 Debrief":
        
        # 1. Fetch recent events to link notes to
        action_events = []
        try:
            if not existing_data.empty and 'RoomCode' in existing_data.columns and 'Timestamp' in existing_data.columns and 'Category' in existing_data.columns:
                today_str = datetime.datetime.now().strftime("%Y-%m-%d")
                recent_logs = existing_data[
                    (existing_data['RoomCode'] == room_code) & 
                    (existing_data['Timestamp'].astype(str).str.contains(today_str)) &
                    (existing_data['Category'].isin(["Leader Override", "Missed Deadline", "Scope Creep", "Technical Event"]))
                ]
                for idx, row in recent_logs.iterrows():
                    short_time = str(row['Timestamp']).split(" ")[-1] 
                    action_events.append(f"{short_time} - {row['Category']}")
        except:
            pass

        action_ref = st.selectbox("Link note to specific event (Optional)", ["None"] + action_events)
        
        event_note = ""
        if action_ref != "None":
            event_note = st.text_area("Event Context", placeholder=f"Notes regarding {action_ref}...")

        # 2. General Notes
        general_notes = st.text_area("General Debrief Notes", placeholder="Overall debrief information...")
        
        # 3. Gear & Consumables with Dynamic UI
        st.write("**Logistics & Gear**")
        consumables = st.multiselect("Consumables Used", ["Gaff Tape", "AA Batteries", "AAA Batteries"])
        
        consumable_data = []
        
        # Dynamic inputs based on selection
        if "Gaff Tape" in consumables:
            gaff_qty = st.text_input("Gaff Tape Quantity", placeholder="e.g. half roll")
            if gaff_qty: 
                consumable_data.append(f"Gaff Tape: {gaff_qty}")
                
        if "AA Batteries" in consumables:
            aa_qty = st.number_input("AA Batteries", min_value=1, step=1)
            consumable_data.append(f"AA Batteries: {aa_qty}")
            
        if "AAA Batteries" in consumables:
            aaa_qty = st.number_input("AAA Batteries", min_value=1, step=1)
            consumable_data.append(f"AAA Batteries: {aaa_qty}")
            
        degraded_gear = st.text_input("Flag Degraded Gear", placeholder="e.g. Frayed 25' XLR")

        st.write("")
        if st.button("Complete Event", use_container_width=True, type="primary"):
            # Format Consumables
            consumables_str = ", ".join(consumable_data)
            
            # Format Linked Event
            linked_event_str = action_ref if action_ref != "None" else ""
            
            # Format General Notes (Combine event context + general notes with carriage returns for Excel)
            combined_notes = []
            if event_note:
                combined_notes.append(f"Context for {linked_event_str}:\n{event_note}")
            if general_notes:
                combined_notes.append(general_notes)
            
            final_general_str = "\n\n".join(combined_notes)
            current_constraints = room_constraints if 'room_constraints'
