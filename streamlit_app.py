import streamlit as st
import pandas as pd
import io

# ---------- Helper Functions ----------
def validate_and_prepare_data(call_logs, agent_roster, disposition_summary):
    # Define required columns per file
    required_cols_dict = {
        'Call Logs': ['agent_id', 'org_id', 'call_date'],
        'Agent Roster': ['agent_id', 'org_id'],
        'Disposition': ['agent_id', 'org_id', 'call_date']
    }

    dataframes = {
        'Call Logs': call_logs,
        'Agent Roster': agent_roster,
        'Disposition': disposition_summary
    }

    for name, df in dataframes.items():
        required_cols = required_cols_dict[name]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"{name} is missing columns: {missing_cols}")
            return None, None, None

    # Convert call_date to datetime
    call_logs['call_date'] = pd.to_datetime(call_logs['call_date'], errors='coerce')
    disposition_summary['call_date'] = pd.to_datetime(disposition_summary['call_date'], errors='coerce')

    # Validate duration column
    if 'duration' in call_logs.columns:
        call_logs['duration'] = pd.to_numeric(call_logs['duration'], errors='coerce')

    return call_logs, agent_roster, disposition_summary


def process_data(call_logs, agent_roster, disposition_summary):
    # Merge disposition with call logs
    merged = pd.merge(call_logs, disposition_summary, on=['agent_id', 'org_id', 'call_date'], how='left')
    merged = pd.merge(merged, agent_roster, on=['agent_id', 'org_id'], how='left')

    # Feature Engineering
    merged['presence'] = merged['login_time'].notna().astype(int)
    merged['completed'] = merged['status'].str.lower() == 'completed'

    grouped = merged.groupby(['agent_id', 'call_date', 'users_first_name', 'users_last_name']).agg(
        total_calls=('call_id', 'count'),
        unique_loans=('installment_id', pd.Series.nunique),
        completed_calls=('completed', 'sum'),
        avg_duration_min=('duration', lambda x: round(x.mean()/60, 2) if not x.isna().all() else 0),
        presence=('presence', 'max')
    ).reset_index()

    grouped['connect_rate'] = (grouped['completed_calls'] / grouped['total_calls'] * 100).round(2)

    return grouped


def generate_summary(df):
    if df.empty:
        return pd.DataFrame([{
            "Note": "No data available for summary."
        }])

    top_row = df.sort_values(by='connect_rate', ascending=False).iloc[0]
    report_date = df['call_date'].max().date()

    summary_data = {
        "Report Date": [report_date],
        "Top Performer": [f"{top_row['users_first_name']} {top_row['users_last_name']}"],
        "Connect Rate (%)": [top_row['connect_rate']],
        "Total Calls": [top_row['total_calls']],
        "Completed Calls": [top_row['completed_calls']],
        "Avg Duration (min)": [top_row['avg_duration_min']],
        "Present": ["Yes" if top_row['presence'] == 1 else "No"]
    }

    return pd.DataFrame(summary_data)



# ---------- Streamlit UI ----------
# ---------- Streamlit UI ----------
st.set_page_config(page_title="Agent Performance Summary", layout="wide")
st.title("📞 Agent Performance Summary Generator")
st.markdown("Upload the **Call Logs**, **Agent Roster**, and **Disposition Summary** CSV files below:")

# Upload section
with st.expander("📂 Upload CSV Files"):
    col1, col2, col3 = st.columns(3)
    with col1:
        call_file = st.file_uploader("📁 Upload call_logs.csv", type="csv")
    with col2:
        roster_file = st.file_uploader("📁 Upload agent_roster.csv", type="csv")
    with col3:
        dispo_file = st.file_uploader("📁 Upload disposition_summary.csv", type="csv")

# When all files are uploaded
if call_file and roster_file and dispo_file:
    call_logs = pd.read_csv(call_file)
    agent_roster = pd.read_csv(roster_file)
    disposition_summary = pd.read_csv(dispo_file)

    # Validate
    call_logs, agent_roster, disposition_summary = validate_and_prepare_data(
        call_logs, agent_roster, disposition_summary
    )

    if call_logs is not None:
        st.success("✅ Files validated and read successfully!")

        # Process
        result = process_data(call_logs, agent_roster, disposition_summary)
        
        st.markdown("### 📋 Full Agent Performance Table")
        st.dataframe(result, use_container_width=True)

        # Download button
        st.download_button(
            label="📥 Download agent_performance_summary.csv",
            data=result.to_csv(index=False),
            file_name="agent_performance_summary.csv",
            mime="text/csv"
        )

        st.markdown("---")
        st.markdown("## 🏅 Summary Section")

        # Buttons to show top performer or top 3
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("📊 Show Top Performer"):
                summary_df = generate_summary(result)
                st.table(summary_df)

        with col2:
            if st.button("🏅 Show Top 3 Performers"):
                top3 = result.sort_values(by='connect_rate', ascending=False).head(3).copy()
                top3['Agent Name'] = top3['users_first_name'] + " " + top3['users_last_name']
                top3_summary = top3[['call_date', 'Agent Name', 'connect_rate', 'total_calls', 'completed_calls', 'avg_duration_min']]
                st.markdown("### 🥇 Top 3 Agents by Connect Rate")
                st.table(top3_summary.reset_index(drop=True))
