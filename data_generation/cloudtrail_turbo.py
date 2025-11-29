#!/usr/bin/env python3
import json
import random
import time
import uuid
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import requests
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class TurboCloudTrailGenerator:
    def __init__(self, endpoint, username, password):
        self.endpoint = endpoint.rstrip('/')
        self.auth = HTTPBasicAuth(username, password) if username and password else None
        self.local = threading.local()
        
        # Pre-generate high cardinality data pools
        self.base_timestamp = datetime.now().isoformat() + 'Z'
        self.account_ids = [f"{random.randint(100000000000, 999999999999)}" for _ in range(1000)]
        self.user_names = [f"user-{i}-{uuid.uuid4().hex[:8]}" for i in range(5000)]
        self.bucket_names = [f"bucket-{i}-{uuid.uuid4().hex[:8]}" for i in range(10000)]
        self.source_ips = [f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}" for _ in range(50000)]
        
        self.event_sources = ["s3.amazonaws.com", "dynamodb.amazonaws.com", "lambda.amazonaws.com", "ec2.amazonaws.com", "iam.amazonaws.com"]
        self.s3_events = ["GetObject", "PutObject", "DeleteObject", "HeadObject", "CopyObject"]
        self.regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-northeast-1", "ap-southeast-1"]
        self.user_agents = ["aws-cli/2.13.0", "aws-sdk-java/1.12.529", "Boto3/1.28.25", "S3Console/0.4"]
        
    def get_session(self):
        if not hasattr(self.local, 'session'):
            self.local.session = requests.Session()
            if self.auth:
                self.local.session.auth = self.auth
            
            retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
            adapter = HTTPAdapter(pool_connections=50, pool_maxsize=100, max_retries=retry_strategy)
            self.local.session.mount('https://', adapter)
            self.local.session.mount('http://', adapter)
        return self.local.session

    def generate_doc(self):
        event_source = random.choice(self.event_sources)
        account_id = random.choice(self.account_ids)
        region = random.choice(self.regions)
        
        if event_source == "s3.amazonaws.com":
            event_name = random.choice(self.s3_events)
        else:
            event_name = random.choice(["RunInstances", "TerminateInstances", "CreateUser", "DeleteUser"])

        return {
            "@timestamp": self.base_timestamp,
            "event": {
                "result": random.choice(["ACCEPT", "REJECT"]),
                "name": "cloud_trail",
                "domain": "cloudtrail"
            },
            "cloud": {
                "provider": "aws",
                "account": {"id": account_id},
                "region": region,
                "resource_id": f"i-{random.randint(100000000000, 999999999999):x}",
                "platform": "aws_ec2"
            },
            "aws": {
                "cloudtrail": {
                    "eventVersion": "1.08",
                    "eventName": event_name,
                    "eventSource": event_source,
                    "eventTime": self.base_timestamp,
                    "eventType": "AwsApiCall",
                    "eventCategory": random.choice(["Data", "Management"]),
                    "sourceIPAddress": random.choice(self.source_ips),
                    "userAgent": random.choice(self.user_agents),
                    "requestID": f"req-{random.randint(100000000,999999999)}-{random.choice(['abcd','efgh','ijkl'])}",
                    "eventID": f"evt-{random.randint(100000000,999999999)}-{random.choice(['wxyz','mnop','qrst'])}",
                    "awsRegion": region,
                    "recipientAccountId": account_id,
                    "apiVersion": random.choice(["2006-03-01", "2012-08-10", "2015-03-31"]),
                    "readOnly": random.choice([True, False]),
                    "userIdentity": {
                        "type": random.choice(["IAMUser", "AssumedRole", "Root"]),
                        "principalId": f"AIDA{random.randint(100000000000, 999999999999)}",
                        "arn": f"arn:aws:iam::{account_id}:user/{random.choice(self.user_names)}",
                        "accountId": account_id,
                        "accessKeyId": f"AKIA{random.randint(100000000000, 999999999999)}"
                    },
                    "resources": [{
                        "accountId": account_id,
                        "type": f"AWS::{event_source.split('.')[0].upper()}::Object",
                        "ARN": f"arn:aws:{event_source.split('.')[0]}:{region}:{account_id}:resource/{random.randint(100000,999999)}"
                    }]
                }
            }
        }

    def bulk_index(self, index_name, docs):
        lines = []
        for doc in docs:
            lines.append('{"index":{"_index":"' + index_name + '"}}')
            lines.append(json.dumps(doc, separators=(',', ':')))
        
        bulk_data = '\n'.join(lines) + '\n'
        session = self.get_session()
        
        try:
            response = session.post(
                f"{self.endpoint}/_bulk?refresh=false",
                data=bulk_data,
                headers={'Content-Type': 'application/x-ndjson', 'Connection': 'keep-alive'},
                timeout=30
            )
            
            if response.status_code not in [200, 201]:
                print(f"HTTP {response.status_code}: {response.text[:200]}")
                return False
            
            result = response.json()
            if result.get('errors', False):
                # Print first error for debugging
                for item in result.get('items', []):
                    if 'index' in item and 'error' in item['index']:
                        print(f"Index error: {item['index']['error']}")
                        break
                return False
            
            return True
            
        except requests.exceptions.Timeout:
            print("Request timeout")
            return False
        except requests.exceptions.ConnectionError:
            print("Connection error")
            return False
        except Exception as e:
            print(f"Bulk error: {str(e)[:100]}")
            return False

def worker(generator, index_name, batch_size, num_batches, worker_id):
    """Worker function for each thread"""
    success_count = 0
    failed_count = 0
    consecutive_failures = 0
    
    for batch_num in range(num_batches):
        docs = [generator.generate_doc() for _ in range(batch_size)]
        
        # Retry logic with exponential backoff
        max_retries = 3
        success = False
        for retry in range(max_retries):
            if generator.bulk_index(index_name, docs):
                success_count += batch_size
                consecutive_failures = 0
                success = True
                break
            else:
                # Exponential backoff: 0.2s, 0.4s, 0.8s
                backoff_time = 0.2 * (2 ** retry)
                time.sleep(backoff_time)
                
                if retry == max_retries - 1:
                    failed_count += 1
                    consecutive_failures += 1
        
        # Stop if too many consecutive failures
        if consecutive_failures > 5:
            print(f"Worker {worker_id}: Too many consecutive failures, stopping")
            break
        
        # Moderate delay between batches to balance speed and stability
        time.sleep(0.02)
        
        # Progress update every 10 batches
        if (batch_num + 1) % 10 == 0:
            print(f"Worker {worker_id}: {batch_num + 1}/{num_batches} batches, {success_count:,} docs")
    
    return success_count, failed_count

def main():
    # Read configuration from environment variables
    endpoint = os.getenv('OPENSEARCH_ENDPOINT')
    username = os.getenv('OPENSEARCH_USER')
    password = os.getenv('OPENSEARCH_PASSWORD')
    index_name = os.getenv('INDEX_NAME')
    
    if not endpoint or not index_name:
        print("Error: Missing required environment variables:")
        print("  OPENSEARCH_ENDPOINT - OpenSearch cluster endpoint URL (REQUIRED)")
        print("  INDEX_NAME - Target index name for data ingestion (REQUIRED)")
        print("  OPENSEARCH_USER - Username for authentication (optional)")
        print("  OPENSEARCH_PASSWORD - Password for authentication (optional)")
        print("\nExample:")
        print("  export OPENSEARCH_ENDPOINT=http://localhost:9200")
        print("  export INDEX_NAME=my_cloudtrail_logs_index")
        return
    
    # Test connection first
    generator = TurboCloudTrailGenerator(endpoint, username, password)
    
    # Test with a small batch first
    print("Testing connection...")
    test_docs = [generator.generate_doc() for _ in range(10)]
    if not generator.bulk_index('test-index', test_docs):
        print("Connection test failed. Check credentials and endpoint.")
        return
    print("Connection test successful!")
    target_docs = 100_000_000
    batch_size = 1500
    num_threads = 8
    
    batches_per_thread = target_docs // (batch_size * num_threads)
    
    print(f"CloudTrail Turbo: {target_docs:,} docs, {num_threads} threads, {batch_size:,} batch size")
    print(f"Each thread processes {batches_per_thread:,} batches")
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(worker, generator, index_name, batch_size, batches_per_thread, i+1)
            for i in range(num_threads)
        ]
        
        total_indexed = 0
        total_failed = 0
        
        for i, future in enumerate(as_completed(futures)):
            indexed, failed = future.result()
            total_indexed += indexed
            total_failed += failed
            elapsed = time.time() - start_time
            rate = total_indexed / elapsed if elapsed > 0 else 0
            
            print(f"Thread {i+1} completed: {indexed:,} docs, {failed} failures | Total: {total_indexed:,} | Rate: {rate:.0f} docs/sec")
    
    elapsed = time.time() - start_time
    final_rate = total_indexed / elapsed
    print(f"\nFinal: {total_indexed:,} docs in {elapsed:.1f}s | Rate: {final_rate:.0f} docs/sec | Failures: {total_failed}")
    
    # Refresh index to make data searchable
    print(f"\nRefreshing index '{index_name}' to make data searchable...")
    try:
        session = generator.get_session()
        refresh_response = session.post(f"{endpoint}/{index_name}/_refresh")
        if refresh_response.status_code == 200:
            print("Index refreshed successfully!")
        else:
            print(f"Refresh warning: HTTP {refresh_response.status_code}")
    except Exception as e:
        print(f"Refresh error: {str(e)}")

if __name__ == "__main__":
    main()
