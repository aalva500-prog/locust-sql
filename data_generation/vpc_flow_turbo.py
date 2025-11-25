#!/usr/bin/env python3
import json
import random
import time
import os
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class TurboVPCGenerator:
    def __init__(self, endpoint, username, password):
        self.endpoint = endpoint.rstrip('/')
        self.auth = HTTPBasicAuth(username, password)
        self.local = threading.local()
        
        # Pre-generate data pools for maximum speed
        self.base_timestamp = datetime.now().isoformat() + 'Z'
        self.account_ids = [f"{random.randint(100000000000, 999999999999)}" for _ in range(50)]
        self.regions = ["us-east-1", "us-west-2"]
        self.actions = ["ACCEPT", "REJECT"]
        self.statuses = ["OK", "NODATA"]
        self.directions = ["ingress", "egress"]
        self.services = ["S3", "EC2"]
        self.ports = [22, 80, 443]
        self.ip_bases = ["172.31", "10.0"]
        
    def get_session(self):
        if not hasattr(self.local, 'session'):
            self.local.session = requests.Session()
            self.local.session.auth = self.auth
            
            # Add retry strategy
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504]
            )
            
            adapter = HTTPAdapter(
                pool_connections=20, 
                pool_maxsize=50,
                max_retries=retry_strategy
            )
            self.local.session.mount('https://', adapter)
            self.local.session.mount('http://', adapter)
        return self.local.session
    
    def generate_doc(self):
        return {
            "@timestamp": self.base_timestamp,
            "start_time": self.base_timestamp,
            "end_time": self.base_timestamp,
            "interval_start_time": self.base_timestamp,
            "aws": {
                "vpc": {
                    "account-id": random.choice(self.account_ids),
                    "action": random.choice(self.actions),
                    "bytes": random.randint(64, 10000),
                    "dstaddr": f"{random.choice(self.ip_bases)}.{random.randint(1,255)}.{random.randint(1,255)}",
                    "srcaddr": f"{random.choice(self.ip_bases)}.{random.randint(1,255)}.{random.randint(1,255)}",
                    "dstport": random.choice(self.ports),
                    "srcport": random.randint(1024, 65535),
                    "packets": random.randint(1, 100),
                    "region": random.choice(self.regions),
                    "status_code": random.choice(self.statuses),
                    "flow-direction": random.choice(self.directions),
                    "pkt-dst-aws-service": random.choice(self.services),
                    "version": 2
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
                headers={
                    'Content-Type': 'application/x-ndjson',
                    'Connection': 'keep-alive'
                },
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
    
    for batch_num in range(num_batches):
        docs = [generator.generate_doc() for _ in range(batch_size)]
        
        if generator.bulk_index(index_name, docs):
            success_count += batch_size
        else:
            failed_count += 1
            if failed_count > 10:  # Stop if too many failures
                print(f"Worker {worker_id}: Too many failures, stopping")
                break
        
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
    
    if not all([endpoint, username, password, index_name]):
        print("Error: Missing required environment variables:")
        print("  OPENSEARCH_ENDPOINT - OpenSearch cluster endpoint URL")
        print("  OPENSEARCH_USER - Username for authentication")
        print("  OPENSEARCH_PASSWORD - Password for authentication")
        print("  INDEX_NAME - Target index name for data ingestion")
        print("\nExample:")
        print("  export OPENSEARCH_ENDPOINT=https://your-cluster.region.es.amazonaws.com")
        print("  export OPENSEARCH_USER=admin")
        print("  export OPENSEARCH_PASSWORD='your-password'")
        print("  export INDEX_NAME=my_vpc_flow_logs_index")
        return
    
    # Test connection first
    generator = TurboVPCGenerator(endpoint, username, password)
    
    # Test with a small batch first
    print("Testing connection...")
    test_docs = [generator.generate_doc() for _ in range(10)]
    if not generator.bulk_index('test-index', test_docs):
        print("Connection test failed. Check credentials and endpoint.")
        return
    print("Connection test successful!")
    target_docs = 100000000
    batch_size = 2000   # Smaller batches
    num_threads = 4     # Fewer threads
    
    batches_per_thread = target_docs // (batch_size * num_threads)
    
    print(f"Turbo mode: {target_docs:,} docs, {num_threads} threads, {batch_size:,} batch size")
    print(f"Each thread will process {batches_per_thread:,} batches")
    
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

if __name__ == "__main__":
    main()
