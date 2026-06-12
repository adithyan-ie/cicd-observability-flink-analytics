#!/usr/bin/env python3
"""
Quick Test Client for DORA API
==============================
Send test events to the DORA metrics API to see real-time updates.

Usage:
  python test_client.py simulate_build  <pipeline> <run_id>
  python test_client.py simulate_deploy <pipeline> <run_id>
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:5000"

def send_event(pipeline_id, run_id, event_type, commit_hash=None):
    """Send a single event to the API."""
    url = f"{BASE_URL}/dora/api/events"
    
    payload = {
        "pipeline_id": pipeline_id,
        "run_id": run_id,
        "event_type": event_type,
        "commit_hash": commit_hash or f"commit-{run_id}",
        "event_time": datetime.utcnow().isoformat()
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 201:
            print(f"✅ Event sent: {event_type}")
            return True
        else:
            print(f"❌ Error: {response.json()}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def simulate_successful_build(pipeline_id, run_id):
    """Simulate a complete successful build & deploy cycle."""
    print(f"\n🚀 Simulating successful pipeline: {pipeline_id}/{run_id}")
    
    events = [
        ('build_start', 'Build started'),
        ('build_success', 'Build succeeded'),
        ('test_start', 'Tests started'),
        ('test_pass', 'All tests passed'),
        ('deploy_start', 'Deployment started'),
        ('deploy_success', 'Deployment succeeded'),
    ]
    
    for event_type, description in events:
        print(f"   → {description}...", end=" ")
        if send_event(pipeline_id, run_id, event_type):
            import time
            time.sleep(0.5)
        else:
            return False
    
    print("\n✨ Pipeline cycle complete!")
    return True

def simulate_failed_build(pipeline_id, run_id):
    """Simulate a failed build."""
    print(f"\n⚠️  Simulating failed build: {pipeline_id}/{run_id}")
    
    events = [
        ('build_start', 'Build started'),
        ('build_failure', 'Build failed'),
    ]
    
    for event_type, description in events:
        print(f"   → {description}...", end=" ")
        if send_event(pipeline_id, run_id, event_type):
            import time
            time.sleep(0.5)
        else:
            return False
    
    print("\n❌ Build failed")
    return True

def get_metrics():
    """Fetch current DORA metrics."""
    url = f"{BASE_URL}/dora/api/metrics"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            metrics = response.json()
            print("\n📊 Current DORA Metrics (last 30 days):")
            print(f"  • Deployment Frequency: {metrics['deployment_frequency']['per_day']:.2f}/day ({metrics['deployment_frequency']['rating']})")
            print(f"  • Lead Time: {metrics['lead_time_for_change'].get('avg_minutes', 'N/A')} min ({metrics['lead_time_for_change']['rating']})")
            print(f"  • Change Failure Rate: {metrics['change_failure_rate']['rate_pct']:.1f}% ({metrics['change_failure_rate']['rating']})")
            print(f"  • MTTR: {metrics['mean_time_to_restore'].get('avg_minutes', 'N/A')} min ({metrics['mean_time_to_restore']['rating']})")
        else:
            print(f"❌ Error: {response.json()}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_client.py success <pipeline> <run_id>")
        print("  python test_client.py failure <pipeline> <run_id>")
        print("  python test_client.py event <pipeline> <run_id> <event_type>")
        print("  python test_client.py metrics")
        print("\nExamples:")
        print("  python test_client.py success auth-service run-001")
        print("  python test_client.py failure api-gateway run-002")
        print("  python test_client.py metrics")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "success" and len(sys.argv) >= 4:
        pipeline = sys.argv[2]
        run_id = sys.argv[3]
        simulate_successful_build(pipeline, run_id)
        get_metrics()
    
    elif command == "failure" and len(sys.argv) >= 4:
        pipeline = sys.argv[2]
        run_id = sys.argv[3]
        simulate_failed_build(pipeline, run_id)
        get_metrics()
    
    elif command == "event" and len(sys.argv) >= 5:
        pipeline = sys.argv[2]
        run_id = sys.argv[3]
        event_type = sys.argv[4]
        send_event(pipeline, run_id, event_type)
        get_metrics()
    
    elif command == "metrics":
        get_metrics()
    
    else:
        print("❌ Invalid command")
        sys.exit(1)

if __name__ == "__main__":
    main()
