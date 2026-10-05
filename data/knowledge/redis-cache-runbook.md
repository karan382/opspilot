# Redis Cache Runbook

## Normal Operating Baseline

The recommendation cache normally responds within 20 ms.

The cache hit rate should remain above 90% during normal operation.

## First-Level Investigation

When Redis latency increases:

1. Check Redis response latency.
2. Check cache hit rate.
3. Check database query volume.
4. Check recommendation API latency.
5. Check recent deployments affecting Redis configuration.

## Cache Degradation

High Redis latency can reduce cache effectiveness and increase database query volume.

A significant decrease in cache hit rate combined with increased database load can indicate degraded cache performance.

## Deployment Correlation

If Redis latency increases shortly after a deployment:

- Compare Redis configuration with the previous version.
- Check changes to request batching or compression.
- Compare Redis latency before and after deployment.
- Verify whether cache hit rate changed at the same time.

## Recovery Verification

After mitigation or rollback:

1. Confirm Redis latency returns to the normal baseline.
2. Confirm cache hit rate recovers.
3. Confirm database query volume decreases.
4. Verify recommendation API latency returns to normal.