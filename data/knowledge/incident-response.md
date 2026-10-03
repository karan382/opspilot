# Production Incident Response

## Incident Triage

For a production incident, first establish:

- What service is affected?
- When did the problem begin?
- What changed immediately before the problem?
- Which user-facing symptoms are occurring?
- Is the impact increasing or stable?

## Evidence Collection

Collect evidence from:

1. Application logs
2. Service metrics
3. Recent deployments
4. Configuration changes
5. Database health
6. Message queues and asynchronous workers

Avoid drawing conclusions from a single log entry. Correlate multiple independent signals whenever possible.

## Root Cause Analysis

A probable root cause should explain:

- The observed symptoms
- The timing of the incident
- Relevant configuration or code changes
- Supporting log or metric evidence

When evidence is insufficient, explicitly mark the root cause as uncertain and identify what additional evidence is required.

## Incident Resolution

After applying a mitigation:

1. Verify that the original symptoms have recovered.
2. Continue monitoring the affected service.
3. Record the mitigation performed.
4. Document the probable root cause.
5. Identify preventive actions.
