# 📞 Agent Performance Summary App

A Streamlit web application to generate agent performance summaries from uploaded call log, agent roster, and disposition data.

---

## 🚀 Features

- 📁 Upload and validate 3 CSV files:
  - `call_logs.csv`
  - `agent_roster.csv`
  - `disposition_summary.csv`
- 🔍 Automatically processes data to:
  - Merge and clean datasets
  - Calculate call metrics (connect rate, average duration, presence, etc.)
- 📊 Displays:
  - Full agent performance table
  - Top performer summary in a table
  - Top 3 performers
- 📥 Download processed summary as CSV

---

## 🗂️ Required CSV File Structures

### `call_logs.csv`
Must contain:
- `agent_id`
- `org_id`
- `call_date`
- `call_id`
- `duration` (optional but recommended)
- `status`

### `agent_roster.csv`
Must contain:
- `agent_id`
- `org_id`
- `users_first_name`
- `users_last_name`
- `login_time` (optional)

### `disposition_summary.csv`
Must contain:
- `agent_id`
- `org_id`
- `call_date`
- `installment_id` (optional but helps calculate unique loans)




