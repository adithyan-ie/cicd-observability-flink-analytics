"""
Sample Data Generator for DORA Metrics
======================================
This script populates the database with realistic CI/CD pipeline events
to demonstrate the DORA metrics dashboard.

Run: python sample_data.py
"""

from datetime import datetime, timedelta
from app import app, db
from models.pipeline_event import PipelineEvent
from models.incident import Incident

# Sample pipeline configurations
PIPELINES = [
    {'id': 'auth-service', 'runs': 12},
    {'id': 'api-gateway', 'runs': 8},
    {'id': 'web-frontend', 'runs': 15},
    {'id': 'data-processor', 'runs': 5},
]


def create_sample_events():
    """Generate realistic CI/CD pipeline events."""
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        now = datetime.utcnow()
        events_created = 0
        
        for pipeline in PIPELINES:
            pipeline_id = pipeline['id']
            
            for run_num in range(1, pipeline['runs'] + 1):
                run_id = f"{pipeline_id}-run-{run_num}"
                commit_hash = f"abc{run_num:05d}".encode().hex()[:40]
                
                # Vary event times across the last 30 days
                days_ago = (run_num % 30)
                base_time = now - timedelta(days=days_ago, hours=run_num % 24)
                
                # Build sequence: build_start → build_success → test_pass → deploy_success
                # Some runs fail, some have retries
                
                events = [
                    {
                        'event_type': 'build_start',
                        'event_time': base_time,
                        'commit_hash': commit_hash
                    },
                ]
                
                build_success_time = base_time + timedelta(minutes=2 + run_num % 5)
                events.append({
                    'event_type': 'build_success',
                    'event_time': build_success_time,
                    'commit_hash': commit_hash
                })
                
                # 90% pass tests
                if run_num % 10 != 0:
                    test_pass_time = build_success_time + timedelta(minutes=3 + run_num % 4)
                    events.append({
                        'event_type': 'test_pass',
                        'event_time': test_pass_time,
                        'commit_hash': commit_hash
                    })
                    
                    deploy_success_time = test_pass_time + timedelta(minutes=2 + run_num % 3)
                    events.append({
                        'event_type': 'deploy_success',
                        'event_time': deploy_success_time,
                        'commit_hash': commit_hash
                    })
                else:
                    # Test failure case
                    test_fail_time = build_success_time + timedelta(minutes=3)
                    events.append({
                        'event_type': 'test_fail',
                        'event_time': test_fail_time,
                        'commit_hash': commit_hash
                    })
                
                # Some deployments get rolled back
                if run_num % 15 == 0 and 'deploy_success' in [e['event_type'] for e in events]:
                    rollback_time = deploy_success_time + timedelta(hours=1, minutes=30)
                    events.append({
                        'event_type': 'rollback',
                        'event_time': rollback_time,
                        'commit_hash': commit_hash
                    })
                
                # Create PipelineEvent records
                for event_data in events:
                    event = PipelineEvent(
                        pipeline_id=pipeline_id,
                        run_id=run_id,
                        event_type=event_data['event_type'],
                        commit_hash=event_data['commit_hash'],
                        event_time=event_data['event_time'],
                    )
                    db.session.add(event)
                    events_created += 1
        
        db.session.commit()
        print(f"✅ Created {events_created} sample pipeline events across {len(PIPELINES)} pipelines")

        # ----------------------------------------------------------------
        # Extra events to demonstrate all DORA rating bands
        # ----------------------------------------------------------------

        # --- More deploy_failures + rollbacks → pushes CFR to Medium/Low ---
        failures = [
            # pipeline_id,        run_id,              fail_time (days ago)
            ('auth-service',   'auth-fail-1',   4),
            ('auth-service',   'auth-fail-2',   8),
            ('auth-service',   'auth-fail-3',  12),
            ('api-gateway',    'gw-fail-1',     6),
            ('api-gateway',    'gw-fail-2',    10),
            ('web-frontend',   'fe-fail-1',     3),
            ('web-frontend',   'fe-fail-2',    14),
            ('data-processor', 'dp-fail-1',     7),
        ]
        for pipeline_id, run_id, days_ago in failures:
            fail_base = now - timedelta(days=days_ago, hours=3)
            # build → deploy_failure
            for evt, offset in [('build_start', 0), ('build_success', 3),
                                 ('test_pass', 7), ('deploy_failure', 10)]:
                db.session.add(PipelineEvent(
                    pipeline_id=pipeline_id, run_id=run_id,
                    event_type=evt, commit_hash=f"fail{run_id[-1]}abc123",
                    event_time=fail_base + timedelta(minutes=offset),
                ))
        db.session.commit()

        # --- Extra rollbacks ---
        rollbacks = [
            ('auth-service',   'auth-rb-1',  2),
            ('api-gateway',    'gw-rb-1',    5),
            ('web-frontend',   'fe-rb-1',   11),
        ]
        for pipeline_id, run_id, days_ago in rollbacks:
            rb_base = now - timedelta(days=days_ago, hours=5)
            for evt, offset in [('build_start', 0), ('build_success', 4),
                                 ('test_pass', 9), ('deploy_success', 12),
                                 ('rollback', 90)]:
                db.session.add(PipelineEvent(
                    pipeline_id=pipeline_id, run_id=run_id,
                    event_type=evt, commit_hash=f"rb{run_id[-1]}def456",
                    event_time=rb_base + timedelta(minutes=offset),
                ))
        db.session.commit()

        # --- Long recovery times → MTTR Medium (days) and Low (week+) ---
        # Each tuple: pipeline, fail_run, fail_days_ago, recovery_days_after_fail
        slow_recoveries = [
            # ~2-day recovery → High band boundary
            ('auth-service',   'auth-slow-1', 20, 2),
            # ~3-day recovery → Medium band
            ('api-gateway',    'gw-slow-1',   18, 3),
            # ~5-day recovery → Medium band
            ('web-frontend',   'fe-slow-1',   16, 5),
            # ~9-day recovery → Low band
            ('data-processor', 'dp-slow-1',   25, 9),
        ]
        for pipeline_id, run_id, fail_days_ago, recovery_days in slow_recoveries:
            fail_time     = now - timedelta(days=fail_days_ago)
            recovery_time = fail_time + timedelta(days=recovery_days)
            # failure event
            db.session.add(PipelineEvent(
                pipeline_id=pipeline_id, run_id=f"{run_id}-fail",
                event_type='deploy_failure', commit_hash='slow123abc',
                event_time=fail_time,
            ))
            # recovery deploy_success
            db.session.add(PipelineEvent(
                pipeline_id=pipeline_id, run_id=f"{run_id}-fix",
                event_type='deploy_success', commit_hash='fix456def',
                event_time=recovery_time,
            ))
        db.session.commit()
        print("✅ Created extra failure / rollback / slow-recovery events")

        # ----------------------------------------------------------------
        # Sample Incidents
        # ----------------------------------------------------------------
        sample_incidents = [
            {'title': 'API Gateway 500 Errors Spike', 'description': 'API gateway returning 500 errors for 15% of requests after latest deploy.', 'severity': 'Critical', 'status': 'Open'},
            {'title': 'Database Connection Pool Exhausted', 'description': 'Connection pool maxed out causing timeouts in auth-service.', 'severity': 'Critical', 'status': 'Closed'},
            {'title': 'Slow Build Times on Web Frontend', 'description': 'Build pipeline for web-frontend taking over 25 minutes due to large bundle size.', 'severity': 'High', 'status': 'Open'},
            {'title': 'Flaky Integration Tests in Data Processor', 'description': 'Test suite failing intermittently (~10%) causing false build failures.', 'severity': 'High', 'status': 'Open'},
            {'title': 'Memory Leak in Auth Service Pod', 'description': 'Auth service pods restarting every 6 hours due to OOMKilled.', 'severity': 'Critical', 'status': 'Closed'},
            {'title': 'Deployment Rollback - v2.4.1', 'description': 'Rollback triggered after v2.4.1 introduced a regression in checkout flow.', 'severity': 'High', 'status': 'Closed'},
            {'title': 'Missing Feature Flags in Staging', 'description': 'Feature flag service not syncing properly to staging environment.', 'severity': 'Medium', 'status': 'Open'},
            {'title': 'CDN Cache Invalidation Failure', 'description': 'Static assets not being invalidated on deploy causing stale content.', 'severity': 'Medium', 'status': 'Closed'},
            {'title': 'Queue Backlog in Data Processor', 'description': 'Processing queue backing up, events delayed by up to 45 minutes.', 'severity': 'High', 'status': 'Open'},
            {'title': 'SSL Certificate Expiry Warning', 'description': 'SSL certificate for api.internal expires in 14 days. Renewal needed.', 'severity': 'Low', 'status': 'Open'},
        ]

        for idx, inc in enumerate(sample_incidents):
            created_offset = timedelta(days=idx * 2, hours=idx % 10)
            incident = Incident(
                title=inc['title'],
                description=inc['description'],
                severity=inc['severity'],
                status=inc['status'],
                created_at=now - created_offset,
            )
            db.session.add(incident)

        db.session.commit()
        print(f"✅ Created {len(sample_incidents)} sample incidents")
        print("\nSample events:")
        recent = PipelineEvent.query.order_by(PipelineEvent.event_time.desc()).limit(10).all()
        for ev in recent:
            print(f"  {ev.pipeline_id:20s} {ev.event_type:15s} {ev.event_time.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    create_sample_events()
    print("\n💡 Now visit http://localhost:5000/dora to see DORA metrics!")
