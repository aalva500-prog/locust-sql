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

class TurboNetworkFirewallGenerator:
    def __init__(self, endpoint, username, password):
        self.endpoint = endpoint.rstrip('/')
        self.auth = HTTPBasicAuth(username, password)
        self.local = threading.local()
        
        # Pre-generate high cardinality data pools
        self.base_timestamp = datetime.now().isoformat()
        self.firewall_names = [f"fw-{i}-{uuid.uuid4().hex[:8]}" for i in range(5000)]
        self.src_ips = [f"{random.randint(10,192)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}" for _ in range(50000)]
        self.dest_ips = [f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}" for _ in range(50000)]
        self.interface_ids = [f"eni-{uuid.uuid4().hex[:16]}" for _ in range(10000)]
        self.vpc_ids = [f"vpc-{uuid.uuid4().hex[:16]}" for _ in range(2000)]
        self.subnet_ids = [f"subnet-{uuid.uuid4().hex[:16]}" for _ in range(5000)]
        
        self.protocols = ["TCP", "UDP", "ICMP"]
        self.app_protocols = ["http", "https", "ssh", "ftp", "dns", "smtp", "unknown"]
        self.dest_ports = [80, 443, 22, 21, 53, 25, 3389, 8080, 8443, 9200]
        self.actions = ["ALLOW", "DROP", "REJECT", "ALERT"]
        
    def get_session(self):
        if not hasattr(self.local, 'session'):
            self.local.session = requests.Session()
            self.local.session.auth = self.auth
            
            retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
            adapter = HTTPAdapter(pool_connections=20, pool_maxsize=50, max_retries=retry_strategy)
            self.local.session.mount('https://', adapter)
            self.local.session.mount('http://', adapter)
        return self.local.session

    def generate_doc(self):
        return {
            "aws.networkfirewall.firewall_name": random.choice(self.firewall_names),
            "aws.networkfirewall.event.timestamp": self.base_timestamp,
            "aws.networkfirewall.event.src_ip": random.choice(self.src_ips),
            "aws.networkfirewall.event.dest_ip": random.choice(self.dest_ips),
            "aws.networkfirewall.event.src_port": random.randint(1024, 65535),
            "aws.networkfirewall.event.dest_port": random.choice(self.dest_ports),
            "aws.networkfirewall.event.proto": random.choice(self.protocols),
            "aws.networkfirewall.event.app_proto": random.choice(self.app_protocols),
            "aws.networkfirewall.event.tcp.tcp_flags": str(random.randint(0, 255)),
            "aws.networkfirewall.event.tcp.syn": random.choice([True, False]),
            "aws.networkfirewall.event.tcp.ack": random.choice([True, False]),
            "aws.networkfirewall.event.tcp.fin": random.choice([True, False]),
            "aws.networkfirewall.event.tcp.rst": random.choice([True, False]),
            "aws.networkfirewall.event.netflow.pkts": random.randint(1, 10000),
            "aws.networkfirewall.event.netflow.bytes": random.randint(64, 1048576),
            "aws.networkfirewall.event.netflow.age": random.randint(1, 3600),
            "aws.networkfirewall.event.netflow.start": self.base_timestamp,
            "aws.networkfirewall.event.netflow.end": self.base_timestamp,
            "aws.networkfirewall.event.action": random.choice(self.actions),
            "aws.networkfirewall.event.rule_group_name": f"rulegroup-{random.randint(1000, 9999)}",
            "aws.networkfirewall.event.rule_name": f"rule-{random.randint(10000, 99999)}",
            "aws.networkfirewall.event.rule_priority": random.randint(1, 65535),
            "aws.networkfirewall.event.signature_id": random.randint(1000000, 9999999),
            "aws.networkfirewall.event.signature_rev": random.randint(1, 100),
            "aws.networkfirewall.event.category": random.choice(["Malware", "Trojan", "Policy Violation", "Suspicious Activity"]),
            "aws.networkfirewall.event.severity": random.randint(1, 4),
            "aws.networkfirewall.interface_id": random.choice(self.interface_ids),
            "aws.networkfirewall.vpc_id": random.choice(self.vpc_ids),
            "aws.networkfirewall.subnet_id": random.choice(self.subnet_ids),
            "aws.networkfirewall.availability_zone": random.choice(["us-east-1a", "us-east-1b", "us-west-2a", "us-west-2b"]),
            "aws.networkfirewall.account_id": f"{random.randint(100000000000, 999999999999)}",
            "aws.networkfirewall.region": random.choice(["us-east-1", "us-west-2", "eu-west-1", "ap-northeast-1"]),
            "aws.networkfirewall.event.flow_id": f"flow-{random.randint(100000000, 999999999)}",
            "aws.networkfirewall.event.event_id": f"event-{random.randint(100000000, 999999999)}",
            "aws.networkfirewall.event.classification": random.choice(["Attempted Information Leak", "Web Application Attack", "Trojan Activity"]),
            "aws.networkfirewall.event.reference": f"http://www.emergingthreats.net/sid/{random.randint(2000000, 2999999)}",
            "aws.networkfirewall.event.geoip.src_country": random.choice(["US", "CN", "RU", "DE", "GB", "FR", "JP"]),
            "aws.networkfirewall.event.geoip.dest_country": random.choice(["US", "CA", "GB", "DE", "FR"]),
            "aws.networkfirewall.event.http.hostname": f"host-{random.randint(1000, 9999)}.example.com",
            "aws.networkfirewall.event.http.url": f"/api/v{random.randint(1,3)}/{random.choice(['users', 'data', 'files'])}/{uuid.uuid4().hex[:16]}",
            "aws.networkfirewall.event.http.user_agent": random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "curl/7.68.0",
                "Python-urllib/3.9",
                "Go-http-client/1.1"
            ]),
            "aws.networkfirewall.event.http.method": random.choice(["GET", "POST", "PUT", "DELETE"]),
            "aws.networkfirewall.event.http.status": random.choice([200, 404, 403, 500, 502]),
            "aws.networkfirewall.event.dns.query": f"{random.choice(['api', 'www', 'mail', 'ftp'])}.{random.choice(['example', 'test', 'demo'])}.{random.choice(['com', 'org', 'net'])}",
            "aws.networkfirewall.event.dns.type": random.choice(["A", "AAAA", "CNAME", "MX", "TXT"]),
            "aws.networkfirewall.event.tls.sni": f"secure-{random.randint(1000, 9999)}.example.com",
            "aws.networkfirewall.event.tls.version": random.choice(["TLSv1.2", "TLSv1.3"]),
            "aws.networkfirewall.event.tls.cipher": random.choice([
                "TLS_AES_256_GCM_SHA384",
                "TLS_CHACHA20_POLY1305_SHA256",
                "ECDHE-RSA-AES256-GCM-SHA384"
            ])
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
                return False
            
            return True
            
        except Exception as e:
            print(f"Bulk error: {str(e)[:100]}")
            return False

def worker(generator, index_name, batch_size, num_batches, worker_id):
    success_count = 0
    failed_count = 0
    
    for batch_num in range(num_batches):
        docs = [generator.generate_doc() for _ in range(batch_size)]
        
        if generator.bulk_index(index_name, docs):
            success_count += batch_size
        else:
            failed_count += 1
            if failed_count > 10:
                print(f"Worker {worker_id}: Too many failures, stopping")
                break
        
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
        print("  export INDEX_NAME=my_networkfirewall_logs_index")
        return
    
    generator = TurboNetworkFirewallGenerator(endpoint, username, password)
    target_docs = 100_000_000
    batch_size = 1500
    num_threads = 8
    
    batches_per_thread = target_docs // (batch_size * num_threads)
    
    print(f"NetworkFirewall Turbo: {target_docs:,} docs, {num_threads} threads, {batch_size:,} batch size")
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
            
            print(f"Thread {i+1} done: {indexed:,} docs | Total: {total_indexed:,} | Rate: {rate:.0f} docs/sec")
    
    elapsed = time.time() - start_time
    final_rate = total_indexed / elapsed
    print(f"\nFinal: {total_indexed:,} docs in {elapsed:.1f}s | Rate: {final_rate:.0f} docs/sec")

if __name__ == "__main__":
    main()
