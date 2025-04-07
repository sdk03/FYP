# --- Imports: Flask app, pandas for data handling, and datetime tools ---
from flask import Flask, jsonify, render_template, request
import pandas as pd
import os
from datetime import datetime

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Base directory for merged CSV file ---
MERGED_DIR = os.path.join(os.path.dirname(__file__), "")

# --- Route: Platform-based conversation aggregation view ---

@app.route('/platform-view', methods=['GET'])
def platform_view():
    # Load the merged CSV file into a DataFrame
    merged_file_path = os.path.join(MERGED_DIR, "merged_conversations.csv")
    try:
        df = pd.read_csv(merged_file_path)
    except FileNotFoundError:
        return "Error: Merged file not found.", 404

    # Convert 'Date/Time' column to datetime format
    df['Date/Time'] = pd.to_datetime(df['Date/Time'])

    # Extract unique platforms from the 'Message Type' column
    platforms = df['Message Type'].unique().tolist()

    # Get selected platforms from query parameters (checkboxes)
    selected_platforms = request.args.getlist('platforms')

    # Filter the DataFrame based on selected platforms
    if selected_platforms:
        filtered_df = df[df['Message Type'].isin(selected_platforms)]
    else:
        filtered_df = df  # Show all platforms by default

    # Group conversations by Conversation_ID and Platform
    grouped_data = {}
    for platform, group in filtered_df.groupby('Message Type'):
        # Aggregate data for each Conversation_ID
        aggregated = group.groupby('Conversation_ID').agg({
            'summary': 'first',  # Take the first summary (assuming all summaries are the same for a Convo_ID)
            'Date/Time': ['min', 'max'],  # Get the earliest and latest timestamps
        }).reset_index()

        # Rename columns for clarity
        aggregated.columns = ['Convo_ID', 'Summary', 'Time_From', 'Time_To']

        # Calculate Duration (in seconds)
        aggregated['Duration'] = (aggregated['Time_To'] - aggregated['Time_From']).dt.total_seconds()

        # Convert timestamps to string format for display
        aggregated['Time_From'] = aggregated['Time_From'].dt.strftime('%A, %d %b %Y, %I:%M %p')
        aggregated['Time_To'] = aggregated['Time_To'].dt.strftime('%A, %d %b %Y, %I:%M %p')

        # Add individual messages for each Conversation_ID
        aggregated['Messages'] = aggregated['Convo_ID'].apply(
            lambda convo_id: group[group['Conversation_ID'] == convo_id][[
                'Date/Time', 'From Phone Number', 'To Phone Number', 'Text'
            ]].rename(
                columns={'Date/Time': 'Date_Time'}  # Replace '/' with '_'
            ).to_dict(orient='records')
        )

        # Store the aggregated data for the platform
        grouped_data[platform] = aggregated.to_dict(orient='records')

    return render_template(
        'index.html',
        platforms=platforms,
        grouped_data=grouped_data,
        selected_platforms=selected_platforms
    )

# --- Route: Timeline-based conversation grouping view ---
@app.route('/timeline-view', methods=['GET'])
def timeline_view():
    # Load the merged CSV file into a DataFrame
    merged_file_path = os.path.join(MERGED_DIR, "merged_conversations.csv")
    try:
        df = pd.read_csv(merged_file_path)
    except FileNotFoundError:
        return "Error: Merged file not found.", 404

    # Convert 'Date/Time' column to datetime format
    df['Date/Time'] = pd.to_datetime(df['Date/Time'])

    # Get user input for time duration and unit
    time_duration = request.args.get('time_duration', default=1, type=int)  # Default to 1
    time_unit = request.args.get('time_unit', default='days')  # Default to 'days'

    # Define time deltas based on user input
    if time_unit == 'seconds':
        time_delta = pd.Timedelta(seconds=time_duration)
    elif time_unit == 'minutes':
        time_delta = pd.Timedelta(minutes=time_duration)
    elif time_unit == 'hours':
        time_delta = pd.Timedelta(hours=time_duration)
    elif time_unit == 'days':
        time_delta = pd.Timedelta(days=time_duration)
    elif time_unit == 'weeks':
        time_delta = pd.Timedelta(weeks=time_duration)
    elif time_unit == 'months':
        time_delta = pd.Timedelta(days=30 * time_duration)  # Approximation
    elif time_unit == 'years':
        time_delta = pd.Timedelta(days=365 * time_duration)  # Approximation
    else:
        time_delta = pd.Timedelta(days=1)  # Default to 1 day

    # Sort the DataFrame by Date/Time
    df = df.sort_values(by='Date/Time')

    # Group conversations by time slots
    grouped_data = []
    start_time = df['Date/Time'].min()
    end_time = start_time + time_delta

    # Generate all time slots, including empty ones
    while start_time < df['Date/Time'].max():
        # Filter conversations within the current time slot
        time_slot_df = df[(df['Date/Time'] >= start_time) & (df['Date/Time'] < end_time)]

        if not time_slot_df.empty:
            # Aggregate data for the time slot
            aggregated = time_slot_df.groupby('Conversation_ID').agg({
                'summary': 'first',  # Take the first summary (assuming all summaries are the same for a Convo_ID)
                'Message Type': 'first',  # Platform
                'Date/Time': ['min', 'max'],  # Get the earliest and latest timestamps
            }).reset_index()

            # Rename columns for clarity
            aggregated.columns = ['Conversation_ID', 'Summary', 'Message_Type', 'Time_From', 'Time_To']

            # Calculate conversation duration (in seconds)
            aggregated['Duration'] = (aggregated['Time_To'] - aggregated['Time_From']).dt.total_seconds()

            # Check if the conversation spans multiple time slots
            aggregated['Spans_Multiple_Slots'] = aggregated.apply(
                lambda row: any(
                    (df['Conversation_ID'] == row['Conversation_ID']) &
                    ((df['Date/Time'] < start_time) | (df['Date/Time'] >= end_time))
                ),
                axis=1
            )

            # Count how many additional time slots the conversation spans
            aggregated['Additional_Slots'] = aggregated.apply(
                lambda row: len(set(
                    pd.date_range(start=df[df['Conversation_ID'] == row['Conversation_ID']]['Date/Time'].min(),
                                  end=df[df['Conversation_ID'] == row['Conversation_ID']]['Date/Time'].max(),
                                  freq=time_delta)
                )) - 1,
                axis=1
            )

            # Add individual messages for each Conversation_ID
            aggregated['Messages'] = aggregated['Conversation_ID'].apply(
                lambda convo_id: time_slot_df[time_slot_df['Conversation_ID'] == convo_id][[
                    'Date/Time', 'From Phone Number', 'To Phone Number', 'Text'
                ]].rename(
                    columns={'Date/Time': 'Date_Time'}  # Replace '/' with '_'
                ).to_dict(orient='records')
            )

            # Store the aggregated data for the time slot
            grouped_data.append({
                'Time_From': start_time.strftime('%A, %d %b %Y, %I:%M %p'),
                'Time_To': end_time.strftime('%A, %d %b %Y, %I:%M %p'),
                'Conversations': aggregated.to_dict(orient='records')
            })
        else:
            # Add an empty slot with a placeholder message
            grouped_data.append({
                'Time_From': start_time.strftime('%A, %d %b %Y, %I:%M %p'),
                'Time_To': end_time.strftime('%A, %d %b %Y, %I:%M %p'),
                'Conversations': []  # Empty list indicates no conversations
            })

        # Move to the next time slot
        start_time = end_time
        end_time += time_delta

    return render_template(
        'timeline-view.html',
        grouped_data=grouped_data,
        time_duration=time_duration,
        time_unit=time_unit
    )


# --- Run the Flask app ---
if __name__ == '__main__':
    # Run the Flask app on localhost and port 5000
    app.run(debug=True, host='0.0.0.0', port=5000)