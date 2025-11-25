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
https://your-opensearch-endpoint.region.es.amazonaws.com
```

4. Locust will prompt for credentials if needed, or you can modify the URL to include them:
```
https://username:password@your-opensearch-endpoint.region.es.amazonaws.com
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
export OPENSEARCH_USER=your-username
export OPENSEARCH_PASSWORD='your-password'

LOG_TYPE=vpc uv run locust --host https://your-opensearch-endpoint.region.es.amazonaws.com
```

Or in a single command:

```sh
OPENSEARCH_USER=your-username OPENSEARCH_PASSWORD='your-password' LOG_TYPE=vpc uv run locust --host https://your-opensearch-endpoint.region.es.amazonaws.com
```

### Example: Running Headless Test with Authentication

```sh
# Set credentials
export OPENSEARCH_USER=your-username
export OPENSEARCH_PASSWORD='your-password'

# Run headless test
LOG_TYPE=vpc uv run locust --headless \
  -u 10 -r 2 --run-time 5m \
  --host https://your-opensearch-endpoint.region.es.amazonaws.com
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

## Comparing Calcite vs Non-Calcite Performance

The `compare_performance.py` script helps you compare performance test results between Calcite-enabled and non-Calcite OpenSearch configurations.

### Prerequisites

You need two CSV files exported from Locust performance tests:
1. Results from testing with Calcite enabled
2. Results from testing without Calcite (or with a different configuration)

### Usage

#### Interactive Mode (Recommended)

Run the script without arguments to use interactive mode:

```sh
python3 compare_performance.py
```

The script will prompt you for:

1. **Path to CALCITE performance results CSV**
   ```
   Example: opensearch-utils/locust-sql/performance_results/vpc/vpc_calcite.csv
   ```

2. **Path to NON-CALCITE performance results CSV**
   ```
   Example: opensearch-utils/locust-sql/performance_results/vpc/vpc_non_calcite.csv
   ```

3. **Log type selection** (for including PPL queries in output):
   - `vpc` - VPC Flow Logs
   - `nfw` - Network Firewall Logs
   - `cloudtrail` - CloudTrail Logs
   - `waf` - WAF Logs
   - `skip` - Skip PPL query inclusion

The script will automatically:
- Generate the output file in the same directory as the calcite input file
- Name it `calcite_vs_non_calcite_comparison.csv`
- Include the actual PPL query text for each test (when log type is specified)

#### Command-Line Mode

You can also provide file paths as command-line arguments:

```sh
# Basic usage (output file auto-generated)
python3 compare_performance.py calcite.csv non_calcite.csv

# Specify custom output file
python3 compare_performance.py calcite.csv non_calcite.csv output.csv
```

**Note**: Command-line mode does not include PPL queries in the output.

### Example Workflow

#### 1. Run performance test with Calcite enabled

```sh
LOG_TYPE=vpc uv run locust --headless -u 10 -r 2 --run-time 5m \
  --host https://your-opensearch-endpoint.com
```

Download the results CSV from Locust UI and save as `vpc_calcite.csv`

#### 2. Run performance test with Calcite disabled

```sh
# Disable Calcite on your OpenSearch cluster first
LOG_TYPE=vpc uv run locust --headless -u 10 -r 2 --run-time 5m \
  --host https://your-opensearch-endpoint.com
```

Download the results CSV from Locust UI and save as `vpc_non_calcite.csv`

#### 3. Compare the results

```sh
python3 compare_performance.py
```

When prompted:
```
Enter path to CALCITE CSV: performance_results/vpc/vpc_calcite.csv
Enter path to NON-CALCITE CSV: performance_results/vpc/vpc_non_calcite.csv
Enter log type: vpc
```

#### 4. Analyze the output

The generated `calcite_vs_non_calcite_comparison.csv` will include:

- **Query Name** - Name of the PPL query test
- **PPL Query** - Full text of the PPL query (when log type specified)
- **Better Performance** - Which configuration performed better (Calcite/Non-Calcite)
- **Performance Improvement** - Percentage improvement
- **Request Counts** - Total requests for each configuration
- **Response Time Metrics** - Median, Average, Min, Max, 95th/99th percentiles
- **Percentage Changes** - For all metrics
- **Requests/s** - Throughput comparison
- **Failure Counts** - Failed requests for each configuration

### Comparison Output Examples

#### For each log type:

**VPC Flow Logs:**
```sh
python3 compare_performance.py
# Select log type: vpc
# Output: performance_results/vpc/calcite_vs_non_calcite_comparison.csv
```

**Network Firewall Logs:**
```sh
python3 compare_performance.py
# Select log type: nfw
# Output: performance_results/nfw/calcite_vs_non_calcite_comparison.csv
```

**CloudTrail Logs:**
```sh
python3 compare_performance.py
# Select log type: cloudtrail
# Output: performance_results/cloudtrail/calcite_vs_non_calcite_comparison.csv
```

**WAF Logs:**
```sh
python3 compare_performance.py
# Select log type: waf
# Output: performance_results/waf/calcite_vs_non_calcite_comparison.csv
```

### Summary Statistics

The script also outputs summary statistics to the console:

```
SUMMARY STATISTICS

Aggregated Results:
  Calcite Average Response Time:     87.63 ms
  Non-Calcite Average Response Time: 82.02 ms
  Change: 6.84%

  Calcite Median Response Time:      87 ms
  Non-Calcite Median Response Time:  81 ms
  Change: 7.41%

  Query Performance Summary:
    Calcite wins:     5 queries
    Non-Calcite wins: 10 queries
```

### Tips for Accurate Comparisons

1. **Use identical test parameters**: Same number of users, spawn rate, and duration
2. **Test under similar conditions**: Similar cluster load and data volume
3. **Allow warmup time**: Run a short warmup test before collecting results
4. **Multiple test runs**: Run tests multiple times and compare averages
5. **Isolate variables**: Only change one configuration (Calcite on/off) between tests

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
