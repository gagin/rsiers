#!/usr/bin/env python
"""
Script to generate historical COS and BSI metrics for Bitcoin time machine feature.
This script reads the historical_data.json file and calculates the COS and BSI
metrics for each time point, then updates the JSON file with these metrics.
"""

import json
import os
import sys

def calculate_composite_metrics(indicators):
    """Calculate composite metrics from indicators."""
    # Weights for Composite Overbought Score
    weights = {
        "stochRsi": 0.30,
        "crsi": 0.20,
        "mfi": 0.20,
        "rsi": 0.15,
        "williamsR": 0.10,
        "rvi": 0.03,
        "adaptiveRsi": 0.02
    }

    # Overbought thresholds
    thresholds = {
        "rsi": 70,
        "stochRsi": 80,
        "mfi": 70,
        "crsi": 90,
        "williamsR": -20,  # Note: Williams %R is inverted
        "rvi": 0.7,
        "adaptiveRsi": 70
    }

    # Calculate normalized values and COS for monthly
    monthly_normalized = {}
    monthly_overbought = 0
    for key in indicators:
        value = indicators[key]["monthly"]
        threshold = thresholds[key]

        # Special case for Williams %R (inverted)
        if key == "williamsR":
            monthly_normalized[key] = 100 if value <= threshold else (abs(value) / abs(threshold)) * 100
            if value >= threshold:
                monthly_overbought += 1
        else:
            monthly_normalized[key] = (value / threshold) * 100
            if value >= threshold:
                monthly_overbought += 1

    # Calculate COS for monthly
    monthly_cos = 0
    for key in weights:
        monthly_cos += weights[key] * monthly_normalized[key]

    # Calculate normalized values and COS for weekly
    weekly_normalized = {}
    weekly_overbought = 0
    for key in indicators:
        value = indicators[key]["weekly"]
        threshold = thresholds[key]

        # Special case for Williams %R (inverted)
        if key == "williamsR":
            weekly_normalized[key] = 100 if value <= threshold else (abs(value) / abs(threshold)) * 100
            if value >= threshold:
                weekly_overbought += 1
        else:
            weekly_normalized[key] = (value / threshold) * 100
            if value >= threshold:
                weekly_overbought += 1

    # Calculate COS for weekly
    weekly_cos = 0
    for key in weights:
        weekly_cos += weights[key] * weekly_normalized[key]

    # Calculate BSI (Bull Strength Index)
    # Instead of just counting overbought indicators, we'll calculate a weighted average
    # of how far each indicator is from its neutral value (50% of threshold)
    monthly_bsi = 0
    weekly_bsi = 0

    for key in indicators:
        monthly_value = indicators[key]["monthly"]
        weekly_value = indicators[key]["weekly"]
        threshold = thresholds[key]

        # Calculate distance from neutral (50% of threshold)
        # For Williams %R (which is inverted), we need special handling
        if key == "williamsR":
            # For Williams %R, neutral is around -50, overbought is > -20
            neutral_value = -50
            # Calculate how far the value is from neutral, normalized to 0-100
            monthly_distance = min(100, max(0, (neutral_value - monthly_value) / (neutral_value - threshold) * 100))
            weekly_distance = min(100, max(0, (neutral_value - weekly_value) / (neutral_value - threshold) * 100))

            monthly_bsi += monthly_distance * weights[key]
            weekly_bsi += weekly_distance * weights[key]
        else:
            # For regular indicators, neutral is 50% of threshold
            neutral_value = threshold * 0.5
            # Calculate how far the value is from neutral, normalized to 0-100
            monthly_distance = min(100, max(0, (monthly_value - neutral_value) / (threshold - neutral_value) * 100))
            weekly_distance = min(100, max(0, (weekly_value - neutral_value) / (threshold - neutral_value) * 100))

            monthly_bsi += monthly_distance * weights[key]
            weekly_bsi += weekly_distance * weights[key]

    # Scale to 0-100%
    monthly_bsi = min(100, max(0, monthly_bsi))
    weekly_bsi = min(100, max(0, weekly_bsi))

    return {
        "cos": {"monthly": monthly_cos, "weekly": weekly_cos},
        "tsi": {"monthly": monthly_bsi, "weekly": weekly_bsi}
    }

def main():
    """Main function to update historical data with composite metrics."""
    # Check if historical_data.json exists
    if not os.path.exists('historical_data.json'):
        print("Error: historical_data.json not found")
        sys.exit(1)

    # Load historical data
    try:
        with open('historical_data.json', 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("Error: Invalid JSON in historical_data.json")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading historical_data.json: {e}")
        sys.exit(1)

    # Check if data has the expected structure
    if 'timePoints' not in data:
        print("Error: historical_data.json does not have 'timePoints' key")
        sys.exit(1)

    # Calculate composite metrics for each time point
    for i, time_point in enumerate(data['timePoints']):
        if 'indicators' not in time_point:
            print(f"Warning: Time point {time_point.get('name', i)} does not have indicators")
            continue

        # Calculate composite metrics
        metrics = calculate_composite_metrics(time_point['indicators'])

        # Add metrics to time point
        data['timePoints'][i]['compositeMetrics'] = metrics

        # Print progress
        print(f"Added metrics for {time_point.get('name', i)}: COS Weekly = {metrics['cos']['weekly']:.1f}, BSI Weekly = {metrics['tsi']['weekly']:.1f}%")

    # Save updated data
    try:
        with open('historical_data.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Successfully updated {len(data['timePoints'])} time points in historical_data.json")
    except Exception as e:
        print(f"Error writing to historical_data.json: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
