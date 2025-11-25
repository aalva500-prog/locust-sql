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

class TurboWAFGenerator:
    def __init__(self, endpoint, username, password):
        self.endpoint = endpoint.rstrip('/')
        self.auth = HTTPBasicAuth(username, password)
        self.local = threading.local()
        
        # Pre-generate data pools for maximum speed
        self.base_timestamp = datetime.now().isoformat() + 'Z'
        self.account_ids = [f"{random.randint(100000000000, 999999999999)}" for _ in range(100)]
        self.actions = ["ALLOW", "BLOCK", "COUNT", "CAPTCHA", "CHALLENGE"]
        self.methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
        self.uris = ["/api/v1/users", "/api/v1/orders", "/api/v1/products", "/health", "/admin", "/login", "/search"]
        self.countries = ["US", "GB", "DE", "FR", "JP", "CA", "AU", "BR", "IN"]
        self.rule_types = ["REGULAR", "RATE_BASED", "GROUP"]
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "curl/7.68.0",
            "Python-urllib/3.9"
        ]
        self.response_codes = [200, 201, 204, 403, 503]
        
    def get_session(self):
        if not hasattr(self.local, 'session'):
            self.local.session = requests.Session()
            self.local.session.auth = self.auth
            
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
        action = random.choice(self.actions)
        method = random.choice(self.methods)
        
        # Generate rule group list with high cardinality
        rule_group_list = []
        for _ in range(random.randint(1, 3)):
            rule_group = {
                "ruleGroupId": f"rulegroup-{random.randint(100000,999999)}",
                "terminatingRule": None,
                "nonTerminatingMatchingRules": [],
                "excludedRules": []
            }
            
            if random.random() > 0.7:
                rule_group["terminatingRule"] = {
                    "ruleId": f"rule-{random.randint(10000,99999)}",
                    "action": random.choice(["BLOCK", "ALLOW", "COUNT"]),
                    "ruleMatchDetails": [{
                        "conditionType": random.choice(["SQL_INJECTION", "XSS", "SIZE_CONSTRAINT"]),
                        "location": random.choice(["HEADER", "QUERY_STRING", "URI"]),
                        "matchedData": [random.choice(["select", "script", "union", "drop"])]
                    }]
                }
            
            if random.random() > 0.5:
                for _ in range(random.randint(1, 2)):
                    rule_group["nonTerminatingMatchingRules"].append({
                        "ruleId": f"rule-{random.randint(10000,99999)}",
                        "action": "COUNT",
                        "ruleMatchDetails": []
                    })
            
            rule_group_list.append(rule_group)
        
        # Generate labels
        labels = []
        if random.random() > 0.6:
            label_names = ["awswaf:managed:aws:core-rule-set", "awswaf:managed:aws:known-bad-inputs"]
            for _ in range(random.randint(1, 2)):
                labels.append({"name": random.choice(label_names)})
        
        # Generate rate based rule list
        rate_based_rule_list = []
        if random.random() > 0.8:
            rate_based_rule_list.append({
                "rateBasedRuleId": f"rate-rule-{random.randint(10000,99999)}",
                "rateBasedRuleName": f"RateLimitRule{random.randint(1,5)}",
                "limitKey": random.choice(["IP", "FORWARDED_IP"]),
                "maxRateAllowed": random.choice([100, 500, 1000, 2000]),
                "evaluationWindowSec": random.choice([60, 120, 300]),
                "limitValue": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            })
        
        doc = {
            "@timestamp": self.base_timestamp,
            "aws": {
                "waf": {
                    "formatVersion": 1,
                    "webaclId": f"arn:aws:wafv2:us-east-1:{random.choice(self.account_ids)}:regional/webacl/waf-{random.randint(100000,999999)}/{random.randint(10000000,99999999)}",
                    "terminatingRuleId": f"rule-{random.randint(10000,99999)}" if action != "ALLOW" else "Default_Action",
                    "terminatingRuleType": random.choice(self.rule_types) if action != "ALLOW" else "REGULAR",
                    "action": action,
                    "httpSourceName": f"CF-{random.randint(1000,9999)}",
                    "httpSourceId": f"source-{random.randint(100000,999999)}",
                    "ruleGroupList": rule_group_list,
                    "rateBasedRuleList": rate_based_rule_list,
                    "responseCodeSent": random.choice(self.response_codes),
                    "httpRequest": {
                        "clientIp": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                        "country": random.choice(self.countries),
                        "headers": [
                            {"name": "Host", "value": f"api{random.randint(1,5)}.example.com"},
                            {"name": "User-Agent", "value": random.choice(self.user_agents)},
                            {"name": "Accept", "value": "application/json"}
                        ],
                        "uri": random.choice(self.uris),
                        "args": f"page={random.randint(1,10)}&limit={random.choice([10,20,50,100])}",
                        "httpVersion": "HTTP/1.1",
                        "httpMethod": method,
                        "requestId": f"req-{random.randint(100000000,999999999)}-{random.choice(['abcd','efgh','ijkl'])}",
                        "scheme": "https",
                        "host": f"api{random.randint(1,5)}.example.com"
                    },
                    "labels": labels,
                    "requestBodySize": random.randint(0, 8192),
                    "requestBodySizeInspectedByWAF": random.randint(0, 8192),
                    "ja3Fingerprint": f"{random.randint(10000,99999)}{random.choice(['a','b','c','d','e'])}{random.randint(10000,99999)}",
                    "ja4Fingerprint": f"ja4_{random.randint(10000,99999)}{random.choice(['x','y','z'])}",
                    "clientAsn": random.randint(1000, 65535),
                    "forwardedAsn": random.randint(1000, 65535) if random.random() > 0.5 else None
                }
            }
        }
        
        # Add CAPTCHA response if action is CAPTCHA
        if action == "CAPTCHA":
            doc["aws"]["waf"]["captchaResponse"] = {
                "responseCode": random.choice([200, 405]),
                "solveTimestamp": int(time.time() * 1000) - random.randint(1000, 60000),
                "failureReason": None if random.random() > 0.3 else "TOKEN_EXPIRED"
            }
        
        # Add Challenge response if action is CHALLENGE
        if action == "CHALLENGE":
            doc["aws"]["waf"]["challengeResponse"] = {
                "responseCode": random.choice([200, 405]),
                "solveTimestamp": int(time.time() * 1000) - random.randint(1000, 60000),
                "failureReason": None if random.random() > 0.3 else "TOKEN_INVALID"
            }
        
        return doc
    
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
        print("  export INDEX_NAME=my_waf_logs_index")
        return
    
    generator = TurboWAFGenerator(endpoint, username, password)
    
    # Test connection
    print("Testing connection...")
    test_docs = [generator.generate_doc() for _ in range(10)]
    if not generator.bulk_index('test-index', test_docs):
        print("Connection test failed. Check credentials and endpoint.")
        return
    print("Connection test successful!")
    target_docs = 100000000
    batch_size = 1500
    num_threads = 4
    
    batches_per_thread = target_docs // (batch_size * num_threads)
    
    print(f"WAF Turbo mode: {target_docs:,} docs, {num_threads} threads, {batch_size:,} batch size")
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
