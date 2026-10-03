# Recommendation Service Runbook

## Normal Operating Baseline

The recommendation API normally responds within 2 seconds.

Sustained latency above 3 seconds should be investigated.

## First-Level Investigation

When recommendation latency increases:

1. Check application error rates.
2. Check database connection pool utilization.
3. Check CPU and memory utilization.
4. Check recent deployments.
5. Inspect database connection acquisition errors.

## Deployment Correlation

If latency increases shortly after a deployment:

- Compare the current configuration with the previous version.
- Check for changes to database connection handling.
- Check for changes to concurrency or request processing.
- Compare application metrics before and after deployment.

## Recovery Verification

After mitigation:

- API latency should return below the investigation threshold.
- Database connection utilization should stabilize.
- Request timeout errors should stop.
- Monitor the service for at least 15 minutes before declaring the incident resolved.
