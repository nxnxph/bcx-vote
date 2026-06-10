import streamlit as st
from pyairtable import Api
import uuid

# --- SECURE CONFIGURATION ---
# We now pull the secrets securely from Streamlit, not the public code!
AIRTABLE_TOKEN = st.secrets["AIRTABLE_TOKEN"]
AIRTABLE_BASE_ID = st.secrets["AIRTABLE_BASE_ID"]
COACH_SECRET = "bcx26coach"  

st.set_page_config(page_title="BCX Voting", page_icon="🚀", layout="centered")

try:
    api = Api(AIRTABLE_TOKEN)
    users_table = api.table(AIRTABLE_BASE_ID, 'Users')
    votes_table = api.table(AIRTABLE_BASE_ID, 'Votes')
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.stop()

st.title("🚀 BCX Hackathon Public Vote")
st.write("Please enter your **GitHub handle** (participants) OR the **secret code** (coaches/guests).")

@st.cache_data(ttl=10)
def get_users_data():
    return users_table.all()

all_users = get_users_data()
TEAMS = sorted(list(set([u['fields'].get('Team') for u in all_users if u['fields'].get('Team')])))

user_id = st.text_input("GitHub Handle OR Coach Code:").strip()

if user_id:
    # --- COACH SCENARIO ---
    if user_id == COACH_SECRET:
        st.success("Coach Access Granted! You may vote for any team.")
        with st.form("coach_vote_form"):
            first = st.selectbox("🥇 1st Place (3 Points)", [""] + TEAMS)
            second = st.selectbox("🥈 2nd Place (2 Points)", [""] + TEAMS)
            third = st.selectbox("🥉 3rd Place (1 Point)", [""] + TEAMS)
            submit = st.form_submit_button("Submit Coach Vote")
            
            if submit:
                if len(set([first, second, third])) == 3 and "" not in [first, second, third]:
                    votes_table.create({"ID": str(uuid.uuid4()), "Role": "Coach", "First": first, "Second": second, "Third": third})
                    st.balloons()
                    st.success("Coach vote recorded successfully!")
                else:
                    st.error("Please select 3 DIFFERENT teams.")

    # --- PARTICIPANT SCENARIO ---
    else:
        user_record = next((u for u in all_users if u['fields'].get('GitHub_Handle', '').lower() == user_id.lower()), None)
        
        if not user_record:
            st.error("GitHub Handle not found. Please check for typos.")
        else:
            if user_record['fields'].get('Has_Voted', False):
                st.warning("You have already voted! One vote per participant.")
            else:
                user_team = user_record['fields'].get('Team')
                record_id = user_record['id']
                st.success(f"Welcome! Recognized as a member of **{user_team}**.")
                
                available_teams = [t for t in TEAMS if t != user_team]
                
                with st.form("participant_vote_form"):
                    first = st.selectbox("🥇 1st Place (3 Points)", [""] + available_teams)
                    second = st.selectbox("🥈 2nd Place (2 Points)", [""] + available_teams)
                    third = st.selectbox("🥉 3rd Place (1 Point)", [""] + available_teams)
                    submit = st.form_submit_button("Submit Vote")
                    
                    if submit:
                        if len(set([first, second, third])) == 3 and "" not in [first, second, third]:
                            votes_table.create({"ID": str(uuid.uuid4()), "Role": "Participant", "First": first, "Second": second, "Third": third})
                            users_table.update(record_id, {"Has_Voted": True})
                            get_users_data.clear()
                            st.balloons()
                            st.success("Your vote has been recorded! Thank you.")
                        else:
                            st.error("Please select 3 DIFFERENT teams.")
