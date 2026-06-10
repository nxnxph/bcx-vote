import streamlit as st
from pyairtable import Api
import uuid

# --- SECURE CONFIGURATION ---
AIRTABLE_TOKEN = st.secrets["AIRTABLE_TOKEN"]
AIRTABLE_BASE_ID = st.secrets["AIRTABLE_BASE_ID"]
COACH_SECRET = "bcx26coach"  
RESULTS_SECRET = "bcx26results"  

st.set_page_config(page_title="BCX Voting", page_icon="🚀", layout="centered")

try:
    api = Api(AIRTABLE_TOKEN)
    users_table = api.table(AIRTABLE_BASE_ID, 'Users')
    votes_table = api.table(AIRTABLE_BASE_ID, 'Votes')
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.stop()

st.title("🚀 BCX Hackathon Public Vote")
st.write("Please enter your **GitHub handle** OR the **secret code**.")

@st.cache_data(ttl=10)
def get_users_data():
    return users_table.all()

all_users = get_users_data()
TEAMS = sorted(list(set([u['fields'].get('Team') for u in all_users if u['fields'].get('Team')])))

user_id = st.text_input("GitHub Handle, Coach Code, or Admin Code:").strip()

if user_id:
    # -----------------------------------------
    # SCENARIO A: LIVE RESULTS DASHBOARD (WITH REVEAL)
    # -----------------------------------------
    if user_id == RESULTS_SECRET:
        st.success("Admin Dashboard Unlocked!")
        st.header("🏆 Hackathon Results")
        
        # Fetch all votes and calculate the 3-2-1 scores
        all_votes = votes_table.all()
        scores = {}
        total_ballots = len(all_votes)
        
        for v in all_votes:
            fields = v.get('fields', {})
            first = fields.get('First')
            second = fields.get('Second')
            third = fields.get('Third')
            
            if first: scores[first] = scores.get(first, 0) + 3
            if second: scores[second] = scores.get(second, 0) + 2
            if third: scores[third] = scores.get(third, 0) + 1
            
        if scores:
            # Show this immediately to build suspense!
            st.metric(label="Total Ballots Cast", value=total_ballots)
            st.write("The votes have been tallied. Are you ready?")
            
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            
            # --- THE BIG REVEAL BOX ---
            with st.expander("🎉 CLICK HERE TO REVEAL WINNERS! 🎉", expanded=False):
                st.balloons() # Triggers the balloon animation!
                
                # Show the top 3 Winners prominently
                st.subheader(f"🥇 1st Place: {sorted_scores[0][0]} ({sorted_scores[0][1]} pts)")
                if len(sorted_scores) > 1:
                    st.subheader(f"🥈 2nd Place: {sorted_scores[1][0]} ({sorted_scores[1][1]} pts)")
                if len(sorted_scores) > 2:
                    st.subheader(f"🥉 3rd Place: {sorted_scores[2][0]} ({sorted_scores[2][1]} pts)")
                
                # Draw the bar chart
                st.divider()
                st.bar_chart(scores)
            
            # Refresh button (just in case)
            st.write("")
            if st.button("🔄 Refresh Data"):
                st.rerun()
        else:
            st.info("No votes have been cast yet. Waiting for data...")

    # -----------------------------------------
    # SCENARIO B: COACH / GUEST
    # -----------------------------------------
    elif user_id == COACH_SECRET:
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

    # -----------------------------------------
    # SCENARIO C: PARTICIPANT
    # -----------------------------------------
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
