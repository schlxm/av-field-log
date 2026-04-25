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

# 1. ROOM NAME INPUT
# UI updated to "Room Name", backend uses "room_code" to maintain API stability
raw_code = st.text_input("Enter Room Name") 
room_code = raw_code.strip().upper()

if room_code:
    # --- TABS ARCHITECTURE ---
    tab1, tab2, tab3 = st.tabs(["🛠️ Setup", "⚡ Live Event", "📝 Debrief"])

    # --- TAB 1: SETUP ---
    with tab1:
        st.info("Engineering constraints sync across all devices.")
        
        # Pull existing constraints to populate the field
        try:
            existing_data = conn.read(worksheet="logs", ttl="0s")
            if not existing_data.empty and 'RoomCode' in existing_data.columns:
                match = existing_data[existing_data['RoomCode'] == room_code]
                room_constraints = match.iloc[-1]['Constraints'] if not match.empty else ""
            else:
                room_constraints = ""
        except:
            room_constraints = ""
            existing_data = pd.DataFrame() # fallback

        safety_notes = st.text_area("Constraints", 
                                    value=room_constraints,
                                    placeholder="Type constraints here during prep...")
        
        col1, col2 = st.columns(2)
        with col1:
            infra = st.toggle("Infrastructure Stable")
            final_touches = st.toggle("Final Touches")
            orientation = st.toggle("Orientation")
        with col2:
            handshake = st.toggle("Lead Handshake")
            partner_handshake = st.toggle("Partner Handshake")

        if st.button("Sync Devices", use_container_width=True):
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
                df = conn.read(worksheet="logs", ttl="0s")
                updated_df = pd.concat([df, new_entry], ignore_index=True).dropna(how='all')
                conn.update(worksheet="logs", data=updated_df)
                st.success(f"Synced {room_code} to the cloud.")
            except Exception as e:
                st.error(f"Sync Error: {e}")

    # --- TAB 2: LIVE EVENT ---
    with tab2:
        def log_event(category):
            log_entry = pd.DataFrame([{
                "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "RoomCode": room_code,
                "Category": category,
                "Note": "Action Button Pressed",
                "InfrastructureStatus": "",
                "Constraints": safety_notes,
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
            if st.button("🔴 SENIOR LEADER OVERRIDE", use_container_width=True):
                log_event("Senior Leader Override")
            if st.button("🟡 MISSED DEADLINE", use_container_width=True):
                log_event("Missed Deadline")

        with c2:
            if st.button("🟠 SCOPE CREEP", use_container_width=True):
                log_event("Scope Creep")
            if st.button("🔵 TECHNICAL EVENT", use_container_width=True):
                log_event("Technical Event")

    # --- TAB 3: DEBRIEF ---
    with tab3:
        # 1. Fetch recent events to link notes to
        action_events = []
        try:
            if not existing_data.empty and 'RoomCode' in existing_data.columns and 'Timestamp' in existing_data.columns and 'Category' in existing_data.columns:
                today_str = datetime.datetime.now().strftime("%Y-%m-%d")
                recent_logs = existing_data[
                    (existing_data['RoomCode'] == room_code) & 
                    (existing_data['Timestamp'].astype(str).str.contains(today_str)) &
                    (existing_data['Category'].isin(["Senior Leader Override", "Missed Deadline", "Scope Creep", "Technical Event"]))
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

        if st.button("Submit Debrief", use_container_width=True):
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

            debrief_entry = pd.DataFrame([{
                "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "RoomCode": room_code,
                "Category": "DEBRIEF",
                "Note": "Post-Event Breakdown",
                "InfrastructureStatus": "",
                "Constraints": safety_notes,
                "EventLeadHandshake": "",
                "FinalTouches": "",
                "Orientation": "",
                "PartnerHandshake": "",
                "Linked_Event": linked_event_str,
                "Debrief_General": final_general_str,
                "Debrief_Consumables": consumables_str,
                "Degraded_Gear": degraded_gear
            }])
            
            try:
                df = conn.read(worksheet="logs", ttl="0s")
                updated_df = pd.concat([df, debrief_entry], ignore_index=True).dropna(how='all')
                conn.update(worksheet="logs", data=updated_df)
                st.success("Debrief and gear log saved successfully.")
            except Exception as e:
                st.error(f"Sync Error: {e}")

else:
    st.warning("Please enter a Room Name to begin logging.")
