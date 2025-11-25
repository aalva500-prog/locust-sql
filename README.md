# OpenSearch PPL in Locust

Load testing tool for OpenSearch PPL queries supporting multiple AWS log types (VPC Flow Logs, Network Firewall, CloudTrail, and WAF).

## Overview

This tool allows you to performance test OpenSearch PPL queries against different AWS log types. Queries are organized in subdirectories by log type, and you can choose to test all log types or focus on a specific one.

## Supported Log Types

- **VPC** - VPC Flow Logs (15 queries)
- **NFW** - AWS Network Firewall logs (37 queries)
- **CloudTrail** - AWS CloudTrail logs (16 queries)
- **WAF** - AWS WAF logs (9 queries)

Total: 77 performance test queries

## Query Organization

Queries are stored in the `ppl/` directory, organized by log type:

```
ppl/
├── vpc/          # VPC Flow Logs queries
├── nfw/          # Network Firewall queries
├── cloudtrail/   # CloudTrail queries
└── waf/          # WAF queries
```

## Setup

Set up the `uv` environment:

```sh
uv sync
```

## Usage

### Test All Log Types (Default)

Run Locust with queries from all log types:

```sh
uv run locust
```

### Test Specific Log Type

Use the `LOG_TYPE` environment variable to test a specific log type:

```sh
# Test only VPC queries
LOG_TYPE=vpc uv run locust

# Test only Network Firewall queries
LOG_TYPE=nfw uv run locust

# Test only CloudTrail queries
LOG_TYPE=cloudtrail uv run locust

# Test only WAF queries
LOG_TYPE=waf uv run locust
```

### Locust Web Interface

After starting Locust, open your browser to http://localhost:8089 to:
- Configure the number of users and spawn rate
- Monitor request statistics in real-time
- View response times and failure rates
- Download test results

### Command-line Options

You can also run headless tests with command-line options:

```sh
# Run with 10 users, 2 users/sec spawn rate, for 5 minutes
LOG_TYPE=vpc uv run locust --headless -u 10 -r 2 --run-time 5m --host http://localhost:9200
```

## Prerequisites

- OpenSearch cluster with Calcite plugin enabled
- For best results, resource-constrain OpenSearch to a handful of CPUs to observe performance characteristics

## Connecting to a Secured OpenSearch Cluster

To connect to an OpenSearch cluster with authentication (like AWS OpenSearch Service), you have two options:

### Option 1: Using Locust Web UI (Recommended)

1. Start Locust without specifying a host:
```sh
LOG_TYPE=vpc uv run locust
```

2. Open http://localhost:8089 in your browser

3. Enter your OpenSearch endpoint URL in the "Host" field:
```
https://search-another-c6oixcocja4yha3dtq46glguvm.us-east-1.es.amazonaws.com
```

4. Locust will prompt for credentials if needed, or you can modify the URL to include them:
```
https://admin:h7iCC<DEb73z.}O?n1H-3w!>@search-another-c6oixcocja4yha3dtq46glguvm.us-east-1.es.amazonaws.com
```

### Option 2: Environment Variables with Modified locustfile.py

Update the `locustfile.py` to support authentication from environment variables. Add this at the top of the file:

```python
from requests.auth import HTTPBasicAuth
import urllib.parse
```

Then modify the `on_start` method to include:

```python
def on_start(self):
    # Add authentication if credentials are provided
    username = os.getenv("OPENSEARCH_USER")
    password = os.getenv("OPENSEARCH_PASSWORD")
    
    if username and password:
        self.client.auth = HTTPBasicAuth(username, password)
    
    # ... rest of existing code ...
```

Run with environment variables:

```sh
export OPENSEARCH_USER=admin
export OPENSEARCH_PASSWORD='h7iCC<DEb73z.}O?n1H-3w!>'

LOG_TYPE=vpc uv run locust --host https://search-another-c6oixcocja4yha3dtq46glguvm.us-east-1.es.amazonaws.com
```

Or in a single command:

```sh
OPENSEARCH_USER=admin OPENSEARCH_PASSWORD='h7iCC<DEb73z.}O?n1H-3w!>' LOG_TYPE=vpc uv run locust --host https://search-another-c6oixcocja4yha3dtq46glguvm.us-east-1.es.amazonaws.com
```

### Example: Running Headless Test with Authentication

```sh
# Set credentials
export OPENSEARCH_USER=admin
export OPENSEARCH_PASSWORD='h7iCC<DEb73z.}O?n1H-3w!>'

# Run headless test
LOG_TYPE=vpc uv run locust --headless \
  -u 10 -r 2 --run-time 5m \
  --host https://search-another-c6oixcocja4yha3dtq46glguvm.us-east-1.es.amazonaws.com
```

**Note**: Make sure to modify `locustfile.py` to include the authentication code shown in Option 2 before running with environment variables.

## Extracting Queries

If you need to re-extract queries from the performance test JSON files:

```sh
python3 extract_queries.py
```

This will read queries from `../../performance_tests/{vpc,nfw,cloudtrail,waf}/*_ppl_queries.json` and generate individual `.ppl` files in the corresponding `ppl/` subdirectories.

## Query File Format

Each `.ppl` file contains a single PPL query that starts with `SOURCE`. Example:

```sql
SOURCE = flint_new_data_source_default_amazon_vpc_flow_v1__live_mview | STATS count() as Count by aws.vpc.action | SORT - Count | HEAD 5
```

## Architecture

- **locustfile.py** - Main Locust user class that loads and executes PPL queries
- **extract_queries.py** - Utility script to extract queries from JSON files
- **ppl/** - Directory containing organized PPL query files
- **pyproject.toml** - Python dependencies managed by `uv`

## Performance Testing Tips

1. **Start small**: Begin with 1-5 users to establish baseline performance
2. **Gradually increase load**: Use Locust's web UI to incrementally add users
3. **Monitor OpenSearch**: Watch CPU, memory, and query latency in OpenSearch
4. **Focus testing**: Use `LOG_TYPE` to isolate specific workload patterns
5. **Resource constraints**: Consider limiting OpenSearch resources to identify bottlenecks

## Results Interpretation

Locust provides several key metrics:
- **Request rate**: Requests per second (RPS)
- **Response times**: Min, median, 95th percentile, max
- **Failure rate**: Percentage of failed requests
- **Users**: Current number of simulated users

Use these metrics to understand:
- Query performance across different log types
- System behavior under increasing load
- Comparative performance between log types

Each `.ppl` file contains a single PPL query that starts with `SOURCE`. Example:

```sql
SOURCE = flint_new_data_source_default_amazon_vpc_flow_v1__live_mview | STATS count() as Count by aws.vpc.action | SORT - Count | HEAD 5
```

## Architecture

- **locustfile.py** - Main Locust user class that loads and executes PPL queries
- **extract_queries.py** - Utility script to extract queries from JSON files
- **ppl/** - Directory containing organized PPL query files
- **pyproject.toml** - Python dependencies managed by `uv`

## Performance Testing Tips

1. **Start small**: Begin with 1-5 users to establish baseline performance
2. **Gradually increase load**: Use Locust's web UI to incrementally add users
3. **Monitor OpenSearch**: Watch CPU, memory, and query latency in OpenSearch
4. **Focus testing**: Use `LOG_TYPE` to isolate specific workload patterns
5. **Resource constraints**: Consider limiting OpenSearch resources to identify bottlenecks

## Results Interpretation

Locust provides several key metrics:
- **Request rate**: Requests per second (RPS)
- **Response times**: Min, median, 95th percentile, max
- **Failure rate**: Percentage of failed requests
- **Users**: Current number of simulated users

Use these metrics to understand:
- Query performance across different log types
- System behavior under increasing load
- Comparative performance between log types
