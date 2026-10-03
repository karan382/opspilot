# Database Connection Pooling

## Overview

The recommendation service uses a database connection pool to avoid creating a new database connection for every request.

The pool has a configurable maximum number of connections. When all connections are occupied, new requests must wait until a connection becomes available.

## Symptoms of Pool Exhaustion

Common symptoms include:

- Increased API latency
- Requests waiting for a database connection
- Database connection acquisition timeouts
- Increased request timeout rates
- High connection pool utilization

## Investigation

When investigating possible pool exhaustion:

1. Check active versus maximum database connections.
2. Check connection acquisition latency.
3. Check whether API latency increased at the same time.
4. Compare the connection pool configuration with the previous deployment.
5. Check application logs for connection acquisition timeouts.

## Mitigation

If a deployment introduced an unsafe connection pool configuration:

1. Roll back the configuration or deployment.
2. Confirm that active connections return to normal.
3. Verify that API latency and timeout rates recover.
4. Review the new pool configuration before redeployment.
