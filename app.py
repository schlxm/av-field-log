import streamlit as st
import pandas as pd
import datetime
import os

# --- CONFIG ---
st.set_page_config(page_title="AV Field Log", page_icon="📱", layout="centered")
LOG_FILE = "event_log_cache.csv"

# --- HELPER FUNCTIONS ---
def save_to_cache(category, note=""):
    timestamp = datetime.datetime.now().strftime("%I:%M %p")
    new_entry = pd.DataFrame([[timestamp, category, note]], columns=["Time", "Event", "Details"])
    if not os.path.isfile(LOG_FILE):
        new_entry.to_csv(LOG_FILE, index=False)
    else:
        new_entry.to_csv(LOG_FILE, mode='a', header=False, index=False)

def load_cache():
    if os.path.isfile(LOG_FILE):
        return pd.read_csv(LOG_FILE)
    return pd.DataFrame(columns=["Time", "Event", "Details"])

def clear_cache():
    if os.path.isfile(LOG_FILE):
        os.remove(LOG_FILE)
    st.rerun()

# --- APP UI ---
st.title("🎙️ AV Field Log")
st.caption("Mobile-first defensive documentation & live event tracking.")

# --- PHASE 1: NORMALIZATION ---
with st.expander("🛠️ Normalization & Handshake", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.toggle("Audio Ready")
        st.toggle("Visual Ready")
    with col2:
        st.toggle("Infrastructure Stable")
        handshake = st.toggle("Event Lead Handshake")
    
    if handshake:
        st.success("Handshake Verified: Event Tech connected to Event Lead.")
        
    safety_notes = st.text_area("Engineering/Safety Constraints", 
                                placeholder="e.g. Speaker placement optimized for coverage; do not move.")

st.divider()

# --- PHASE 2: LIVE LOG (TAP-TO-LOG) ---
st.subheader("⚡ Live Change Log")
st.info("Tap a button to capture a timestamped event.")

# High-contrast button grid
c1, c2 = st.columns(2)
with c1:
    if st.button("🔴 SENIOR LEADER OVERRIDE", use_container_width=True):
        save_to_cache("Senior Leader Override")
    if st.button("🟡 MISSED DEADLINE", use_container_width=True):
        save_to_cache("Missed Deadline")

with c2:
    if st.button("🟠 SCOPE CREEP", use_container_width=True):
        save_to_cache("Scope Creep")
    if st.button("🔵 TECHNICAL EVENT", use_container_width=True):
        save_to_cache("Technical Event")

st.divider()

# --- PHASE 3: THE FEED ---
df = load_cache()
if not df.empty:
    st.subheader("Event Timeline")
    # Display in reverse order so newest is on top
    st.table(df.iloc[::-1])
    
    if st.button("Clear Log / New Event"):
        clear_cache()

# --- PHASE 4: POST-MORTEM ---
with st.expander("📝 Post-Mortem & Export"):
    st.subheader("End of Show Brief")
    gear_health = st.selectbox("Gear Health", ["All Good", "Minor Issues (See Notes)", "Repairs Needed"])
    final_notes = st.text_area("Strike Notes / Client Feedback")
    
    if st.button("Generate Excel Summary"):
        log_text = df.to_string(index=False)
        summary = f"""
--- EVENT SUMMARY ---
Launched: {df['Time'].iloc[0] if not df.empty else 'N/A'}
Infrastructure Constraints: {safety_notes}
Gear Status: {gear_health}

LOGGED EVENTS:
{log_text}

STRIKE NOTES:
{final_notes}
---------------------
        """
        st.code(summary, language="text")
        st.caption("Copy this block and paste into your Excel 'Notes' column.")
