# Quick Start Guide - Testing with Your OpenSearch Cluster

This guide shows you how to run performance tests against your secured OpenSearch cluster.

## Your Cluster Details

- **Endpoint**: `https://search-another-c6oixcocja4yha3dtq46glguvm.us-east-1.es.amazonaws.com`
- **Username**: `admin`
- **Password**: `h7iCC<DEb73z.}O?n1H-3w!>`

## Method 1: Using Environment Variables (Recommended)

Set your credentials once, then run tests:

```bash
# Navigate to the locust-sql directory
cd opensearch-utils/locust-sql

# Set credentials (do this once per terminal session)
export OPENSEARCH_USER=admin
export OPENSEARCH_PASSWORD='h7iCC<DEb73z.}O?n1H-3w!>'

# Test VPC queries with web UI
LOG_TYPE=vpc uv run locust --host https://search-another-c6oixcocja4yha3dtq46glguvm.us-east-1.es.amazonaws.com

# Open browser to http://localhost:8089 and start test
```

## Method 2: One-Line Commands

Run everything in a single command:

```bash
cd opensearch-utils/locust-sql

# Test VPC queries (web UI)
OPENSEARCH_USER=admin OPENSEARCH_PASSWORD='h7iCC<DEb73z.}O?n1H-3w!>' \
  LOG_TYPE=vpc uv run locust \
  --host https://search-another-c6oixcocja4yha3dtq46glguvm.us-east-1.es.amazonaws.com

# Test Network Firewall queries (headless - 10 users, 2/sec spawn, 5 min)
OPENSEARCH_USER=admin OPENSEARCH_PASSWORD='h7iCC<DEb73z.}O?n1H-3w!>' \
  LOG_TYPE=nfw uv run locust --headless -u 10 -r 2 --run-time 5m \
  --host https://search-another-c6oixcocja4yha3dtq46glguvm.us-east-1.es.amazonaws.com

# Test CloudTrail queries
OPENSEARCH_USER=admin OPENSEARCH_PASSWORD='h7iCC<DEb73z.}O?n1H-3w!>' \
  LOG_TYPE=cloudtrail uv run locust --headless -u 10 -r 2 --run-time 5m \
  --host https://search-another-c6oixcocja4yha3dtq46glguvm.us-east-1.es.amazonaws.com

# Test WAF queries
OPENSEARCH_USER=admin OPENSEARCH_PASSWORD='h7iCC<DEb73z.}O?n1H-3w!>' \
  LOG_TYPE=waf uv run locust --headless -u 10 -r 2 --run-time 5m \
  --host https://search-another-c6oixcocja4yha3dtq46glguvm.us-east-1.es.amazonaws.com

# Test all log types together
OPENSEARCH_USER=admin OPENSEARCH_PASSWORD='h7iCC<DEb73z.}O?n1H-3w!>' \
  LOG_TYPE=all uv run locust --headless -u 10 -r 2 --run-time 5m \
  --host https://search-another-c6oixcocja4yha3dtq46glguvm.us-east-1.es.amazonaws.com
```

## Step-by-Step Example

1. **Navigate to directory**:
   ```bash
   cd opensearch-utils/locust-sql
   ```

2. **Set up environment** (if not already done):
   ```bash
   uv sync
   ```

3. **Set credentials**:
   ```bash
   export OPENSEARCH_USER=admin
   export OPENSEARCH_PASSWORD='h7iCC<DEb73z.}O?n1H-3w!>'
   ```

4. **Run test with web UI** (recommended for first time):
   ```bash
   LOG_TYPE=vpc uv run locust \
     --host https://search-another-c6oixcocja4yha3dtq46glguvm.us-east-1.es.amazonaws.com
   ```

5. **Open browser**: Go to http://localhost:8089

6. **Configure test**:
   - Number of users: Start with 5
   - Spawn rate: 1 user per second
   - Click "Start swarming"

7. **Monitor results**: Watch the statistics in real-time

## Testing Different Log Types

The `LOG_TYPE` environment variable controls which queries to run:

| Variable Value | Queries Loaded | Description |
|---------------|---------------|-------------|
| `vpc` | 15 queries | VPC Flow Logs only |
| `nfw` | 37 queries | Network Firewall only |
| `cloudtrail` | 16 queries | CloudTrail only |
| `waf` | 9 queries | WAF logs only |
| `all` | 77 queries | All log types (default) |

## Quick Performance Test Workflow

```bash
# 1. Start with light load to verify connectivity
OPENSEARCH_USER=admin OPENSEARCH_PASSWORD='h7iCC<DEb73z.}O?n1H-3w!>' \
  LOG_TYPE=vpc uv run locust --headless -u 1 -r 1 --run-time 30s \
  --host https://search-another-c6oixcocja4yha3dtq46glguvm.us-east-1.es.amazonaws.com

# 2. If successful, increase load
OPENSEARCH_USER=admin OPENSEARCH_PASSWORD='h7iCC<DEb73z.}O?n1H-3w!>' \
  LOG_TYPE=vpc uv run locust --headless -u 10 -r 2 --run-time 5m \
  --host https://search-another-c6oixcocja4yha3dtq46glguvm.us-east-1.es.amazonaws.com

# 3. Compare different log types
for type in vpc nfw cloudtrail waf; do
  echo "Testing $type..."
  OPENSEARCH_USER=admin OPENSEARCH_PASSWORD='h7iCC<DEb73z.}O?n1H-3w!>' \
    LOG_TYPE=$type uv run locust --headless -u 10 -r 2 --run-time 2m \
    --host https://search-another-c6oixcocja4yha3dtq46glguvm.us-east-1.es.amazonaws.com
  sleep 5
done
```

## Troubleshooting

### Authentication Errors
If you see 401/403 errors, verify:
- Username and password are correct
- Password special characters are properly quoted
- OpenSearch domain allows your IP address

### Connection Errors
If you see SSL/connection errors:
- Verify the endpoint URL is correct
- Check that the cluster is running
- Ensure your network can reach AWS OpenSearch

### No Queries Loaded
If you see "No queries found":
- Verify you're in the `locust-sql` directory
- Check that `ppl/` subdirectories exist
- Run `python3 extract_queries.py` to regenerate queries

## Next Steps

- Start with 1-5 users to establish baseline performance
- Gradually increase load using the web UI
- Monitor OpenSearch metrics (CPU, memory, query latency)
- Compare performance across different log types
- Save and analyze results for optimization

For more details, see [README.md](README.md) and [CHANGES.md](CHANGES.md).
