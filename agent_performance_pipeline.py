import pandas as pd
import numpy as np
import argparse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def validate_data(df, required_columns, name):
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        logging.error(f"{name}: Missing columns - {missing_cols}")
        raise ValueError(f"{name}: Missing columns - {missing_cols}")
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        logging.warning(f"{name}: {duplicates} duplicate rows found. Dropping duplicates.")
    return df.drop_duplicates()


def load_data(call_logs_path, agent_roster_path, disposition_path):
    call_logs = pd.read_csv(call_logs_path)
    agent_roster = pd.read_csv(agent_roster_path)
    disposition_summary = pd.read_csv(disposition_path)

    call_logs = validate_data(call_logs, ['call_date', 'agent_id', 'org_id'], 'Call Logs')
    agent_roster = validate_data(agent_roster, ['agent_id', 'org_id'], 'Agent Roster')
    disposition_summary = validate_data(disposition_summary, ['call_date', 'agent_id', 'org_id'], 'Disposition Summary')

    return call_logs, agent_roster, disposition_summary


def merge_data(call_logs, agent_roster, disposition_summary):
    merged = pd.merge(call_logs, disposition_summary, on=['agent_id', 'org_id', 'call_date'], how='left')
    merged = pd.merge(merged, agent_roster, on=['agent_id', 'org_id'], how='left')
    logging.info(f"Merged data shape: {merged.shape}")
    return merged


def engineer_features(merged):
    merged['presence'] = np.where(merged['login_time'].notnull(), 1, 0)
    merged['is_completed'] = np.where(merged['status'] == 'completed', 1, 0)

    grouped = merged.groupby(['agent_id', 'users_first_name', 'users_last_name', 'call_date']).agg(
        total_calls=('call_id', 'count'),
        unique_loans=('installment_id', pd.Series.nunique),
        completed_calls=('is_completed', 'sum'),
        avg_duration=('duration', 'mean'),
        presence=('presence', 'max')
    ).reset_index()

    grouped['connect_rate'] = (grouped['completed_calls'] / grouped['total_calls']).round(2)
    grouped['avg_duration'] = grouped['avg_duration'].round(2)
    return grouped


def generate_summary(df):
    summary_date = df['call_date'].iloc[0]
    top_agent = df.sort_values('connect_rate', ascending=False).iloc[0]
    message = (
        f"Agent Summary for {summary_date}\n"
        f"Top Performer: {top_agent['users_first_name']} {top_agent['users_last_name']} "
        f"({int(top_agent['connect_rate'] * 100)}% connect rate)\n"
        f"Total Active Agents: {df['agent_id'].nunique()}\n"
        f"Average Duration: {df['avg_duration'].mean().round(1)} min"
    )
    return message


def main(call_logs_path, agent_roster_path, disposition_path, output_path):
    call_logs, agent_roster, disposition_summary = load_data(call_logs_path, agent_roster_path, disposition_path)
    merged = merge_data(call_logs, agent_roster, disposition_summary)
    performance_df = engineer_features(merged)
    performance_df.to_csv(output_path, index=False)
    logging.info(f"Summary report saved to {output_path}")
    print(generate_summary(performance_df))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DPDzero Agent Performance Pipeline')
    parser.add_argument('--call_logs', required=True, help='call_logs.csv')
    parser.add_argument('--agent_roster', required=True, help='agent_roster.csv')
    parser.add_argument('--disposition', required=True, help='disposition_summary.csv')
    parser.add_argument('--output', default='agent_performance_summary.csv', help='Output CSV file path')
    args = parser.parse_args()

    main(args.call_logs, args.agent_roster, args.disposition, args.output)
