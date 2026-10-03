# Event Consumer Kafka Runbook

## Normal Operating Baseline

The event consumer processes messages from Kafka partitions continuously.

Consumer lag should remain stable under normal traffic.

A sustained increase in consumer lag should be investigated.

## First-Level Investigation

When consumer lag increases:

1. Check consumer lag across affected partitions.
2. Check consumer processing latency and throughput.
3. Check whether all expected consumers are healthy.
4. Check for consumer errors or repeated processing failures.
5. Check recent deployments and configuration changes.
6. Check downstream dependencies used during message processing.

## Partition and Consumer Health

When investigating Kafka lag:

- Determine whether lag is isolated to specific partitions or affects multiple partitions.
- Check whether consumers are actively processing messages.
- Compare message production rate with consumer processing rate.
- Check for consumer restarts or rebalancing events.

## Root Cause Analysis

Do not attribute consumer lag to Kafka itself without supporting evidence.

Correlate lag with consumer processing latency, throughput, errors, deployment changes, and downstream dependency health.

If the available evidence is insufficient, mark the root cause as uncertain and identify the additional evidence required.

## Recovery Verification

After mitigation:

- Consumer lag should trend back toward normal.
- Consumer processing should remain healthy.
- Processing errors should stop.
- Monitor the consumer before declaring the incident resolved.