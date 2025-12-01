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

- OpenSearch cluster (version 3.3 or later recommended for best Calcite performance)
- Calcite is available starting from OpenSearch 3.1
  - Disabled by default in versions 3.1
  - Will be enabled by default starting from version 3.3
- For best results, resource-constrain OpenSearch to a handful of CPUs to observe performance characteristics

## Generating Test Data

To generate test data for performance testing, you can use the data generation scripts provided in the `data_generation/` directory. These scripts simulate realistic sample AWS log data for each log type:

- **`vpc_flow_turbo.py`** - Generate simulated VPC Flow Logs
- **`networkfirewall_turbo.py`** - Generate simulated AWS Network Firewall logs
- **`cloudtrail_turbo.py`** - Generate simulated CloudTrail logs
- **`waf_turbo.py`** - Generate simulated WAF logs

Each script creates high-volume, realistic sample data that mimics real AWS log structures and patterns. You can ingest this generated data into your OpenSearch cluster for testing. For meaningful performance results, we recommend generating at least 100 GB of data per log type.

### Required Configuration

All data generation scripts require the following environment variables:

```sh
export OPENSEARCH_ENDPOINT=https://your-cluster.region.es.amazonaws.com
export OPENSEARCH_USER=admin
export OPENSEARCH_PASSWORD='your-password'
export INDEX_NAME=my_index_name
```

**Environment Variables:**
- `OPENSEARCH_ENDPOINT` - Your OpenSearch cluster endpoint URL
- `OPENSEARCH_USER` - Username for authentication  
- `OPENSEARCH_PASSWORD` - Password for authentication
- `INDEX_NAME` - Target index name where data will be ingested

### Example Usage

```sh
# Set environment variables
export OPENSEARCH_ENDPOINT=https://search-my-cluster.us-west-2.es.amazonaws.com
export OPENSEARCH_USER=admin
export OPENSEARCH_PASSWORD='mySecurePassword123'
export INDEX_NAME=vpc_flow_logs_test

# Run the VPC Flow Logs generator
python3 data_generation/vpc_flow_turbo.py
```

## Connecting to a Secured OpenSearch Cluster

To connect to an OpenSearch cluster with authentication (like AWS OpenSearch Service with Fine-Grained Access Control), use environment variables for credentials.

### Setting Up Authentication

The `locustfile.py` should be configured to read credentials from environment variables. Add this at the top of the file:

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

### Running Tests with Authentication

Set your credentials as environment variables:

```sh
export OPENSEARCH_USER=your-username
export OPENSEARCH_PASSWORD='your-password'
```

Then run Locust:

```sh
LOG_TYPE=vpc uv run locust --host https://your-opensearch-endpoint.region.es.amazonaws.com
```

Open http://localhost:8089 in your browser to access the Locust web UI.

### Running Headless Tests with Authentication

For automated/headless testing:

```sh
# Set credentials
export OPENSEARCH_USER=your-username
export OPENSEARCH_PASSWORD='your-password'

# Run headless test
LOG_TYPE=vpc uv run locust --headless \
  -u 10 -r 2 --run-time 5m \
  --host https://your-opensearch-endpoint.region.es.amazonaws.com
```

Or in a single command:

```sh
OPENSEARCH_USER=your-username OPENSEARCH_PASSWORD='your-password' \
  LOG_TYPE=vpc uv run locust --headless \
  -u 10 -r 2 --run-time 5m \
  --host https://your-opensearch-endpoint.region.es.amazonaws.com
```

## Query File Format

Each `.ppl` file contains a single PPL query that starts with `SOURCE`. Example:

```sql
SOURCE = flint_new_data_source_default_amazon_vpc_flow_v1__live_mview | STATS count() as Count by aws.vpc.action | SORT - Count | HEAD 5
```

## Architecture

- **locustfile.py** - Main Locust user class that loads and executes PPL queries
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

The `compare_performance.py` script helps you compare performance test results between Calcite-enabled and non-Calcite configurations on the same OpenSearch cluster.

### Prerequisites

- A single OpenSearch cluster where you can toggle the Calcite setting
- Two CSV files exported from Locust performance tests on the same cluster:
  1. Results from testing with Calcite enabled
  2. Results from testing with Calcite disabled

**Note**: Both tests should be run on the same cluster with identical configuration, changing only the Calcite enabled/disabled setting between tests.

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

### Test Environment Specifications

The performance testing documented here was conducted on the following Amazon OpenSearch Service domain configuration:

#### OpenSearch Domain Details

- **OpenSearch Version**: 3.3 with latest Service Software version
- **Data Nodes**: 6 × r7g.xlarge.search instances
- **Master Nodes**: 3 × m7g.2xlarge.search instances
- **Storage Type**: EBS
- **EBS Volume Type**: General Purpose (SSD) - gp3
- **EBS Volume Size**: 250 GiB per node
- **Provisioned IOPS**: 3,000 IOPS
- **Provisioned Throughput**: 500 MiB/s

#### Index Details

For meaningful performance testing results, we recommend:
- **Minimum Index Size**: At least 100 GB per log type
- **Shard Configuration**: Adjust primary/replica shards based on your cluster size and data volume

This ensures realistic testing conditions for evaluating PPL query performance at scale.

### Recommended Testing Approach

For consistent and comparable results, we recommend the following two-phase testing approach using the Locust web interface:

**Phase 1: Initial Load (15 minutes)**
- 50 concurrent users
- 5 users/second spawn rate
- Duration: 15 minutes

**Phase 2: Increased Load (15 minutes)**
- 100 concurrent users  
- 10 users/second spawn rate
- Duration: 15 minutes

This approach allows you to:
- Establish baseline performance under moderate load
- Observe system behavior under increased load
- Identify performance degradation patterns
- Compare results consistently across different configurations

### Example Workflow

**Important Note about Calcite in OpenSearch**: 
- Calcite is available starting from OpenSearch 3.1
- **Disabled by default** in versions 3.1-3.3 (must be manually enabled)
- Will be **enabled by default** starting from version 3.4
- Version 3.3 includes the most significant Calcite performance improvements

You must explicitly enable Calcite before running Calcite performance tests on versions 3.1-3.3.

#### Enabling/Disabling Calcite

To enable Calcite for PPL queries, use the OpenSearch settings API:

```sh
# Enable Calcite
curl -X PUT "https://your-opensearch-endpoint.com/_cluster/settings" \
  -H "Content-Type: application/json" \
  -d '{
    "transient": {
      "plugins.calcite.enabled": true
    }
  }'
```

To disable Calcite (for non-Calcite testing):

```sh
# Disable Calcite
curl -X PUT "https://your-opensearch-endpoint.com/_cluster/settings" \
  -H "Content-Type: application/json" \
  -d '{
    "transient": {
      "plugins.calcite.enabled": false
    }
  }'
```

#### 1. Run performance test with Calcite enabled

**First, enable Calcite** using the command above, then start Locust with the desired log type:

```sh
LOG_TYPE=vpc uv run locust --host https://your-opensearch-endpoint.com
```

Open http://localhost:8089 and configure the test in the web UI:

**Phase 1 - Initial Load:**
- Number of users: `50`
- Spawn rate: `5`
- Run time: `15m`
- Click "Start swarming"

After 15 minutes, **do not stop** the test. Instead, update the load:

**Phase 2 - Increased Load:**
- In the web UI, enter new values:
  - Number of users: `100`
  - Spawn rate: `10`
- Click "Start swarming" again
- Let it run for another 15 minutes

After both phases complete (total 30 minutes):

1. In the Locust UI, click the **"Download Data"** tab
2. Click **"Download statistics CSV"** to download the results
3. Save the file to the appropriate performance_results directory:
   ```
   opensearch-utils/locust-sql/performance_results/vpc/vpc_calcite.csv
   ```

**Note**: The `performance_results/{vpc,nfw,cloudtrail,waf}/` directories contain the CSV files downloaded from Locust UI for each log type. Make sure to save your test results in the corresponding directory based on the log type you're testing.

#### 2. Run performance test with Calcite disabled

**Disable Calcite** using the command shown above, then repeat the same process:

```sh
LOG_TYPE=vpc uv run locust --host https://your-opensearch-endpoint.com
```

In the web UI (http://localhost:8089):

**Phase 1 - Initial Load (15 minutes):**
- Number of users: `50`
- Spawn rate: `5`
- Run time: `15m`

**Phase 2 - Increased Load (15 minutes):**
- Number of users: `100`
- Spawn rate: `10`
- Continue for another 15 minutes

After both phases complete (total 30 minutes):

1. In the Locust UI, click the **"Download Data"** tab
2. Click **"Download statistics CSV"** to download the results
3. Save the file to the same performance_results directory:
   ```
   opensearch-utils/locust-sql/performance_results/vpc/vpc_non_calcite.csv
   ```

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
