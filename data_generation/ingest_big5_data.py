#!/usr/bin/env python3

import json
import requests
import time
import urllib3
from requests.auth import HTTPBasicAuth

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
OPENSEARCH_ENDPOINT = "https://search-calcite-testing-epucq7tfw4t6ier57ep2wl2vh4.us-west-2.es.amazonaws.com"
USERNAME = "admin"
PASSWORD = "h7iCC<DEb73z.}O?n1H-3w!>"
INDEX_NAME = "big5"
DATA_FILE = "/Users/aaarone/Documents/Code/ppl_performance_analysis/locust-sql/locust-sql/data/documents-100.json"

def send_batch(docs):
    lines = []
    for doc in docs:
        lines.append(f'{{"index":{{"_index":"{INDEX_NAME}"}}}}')
        lines.append(json.dumps(doc, separators=(',', ':')))
    
    bulk_data = '\n'.join(lines) + '\n'
    
    try:
        response = requests.post(
            f"{OPENSEARCH_ENDPOINT}/_bulk",
            data=bulk_data,
            headers={'Content-Type': 'application/x-ndjson'},
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            verify=False,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if not result.get('errors', False):
                return True, len(docs)
            else:
                successful = 0
                for item in result.get('items', []):
                    if 'index' in item and item['index'].get('status') in [200, 201]:
                        successful += 1
                return True, successful
        else:
            print(f"HTTP {response.status_code}: {response.text[:200]}")
            return False, 0
    except Exception as e:
        print(f"Connection error: {str(e)[:100]}")
        return False, 0

def main():
    print("Starting fast ingestion...")
    
    total_docs = 0
    successful_docs = 0
    batch_count = 0
    batch_size = 1000
    
    start_time = time.time()
    
    with open(DATA_FILE, 'r') as f:
        batch_docs = []
        
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
                
            try:
                doc = json.loads(line.strip())
                doc["@timestamp"] = "2024-01-01T00:00:00Z"
                batch_docs.append(doc)
                total_docs += 1
                
                if total_docs % 50000 == 0:
                    elapsed = time.time() - start_time
                    rate = total_docs / elapsed if elapsed > 0 else 0
                    print(f"Processed {total_docs:,} documents... Rate: {rate:.0f} docs/sec")
                
                if len(batch_docs) >= batch_size:
                    success, indexed = send_batch(batch_docs)
                    batch_count += 1
                    
                    if success:
                        successful_docs += indexed
                        if indexed < len(batch_docs):
                            print(f"Batch {batch_count}: {indexed}/{len(batch_docs)} docs successful")
                    else:
                        print(f"Batch {batch_count} FAILED")
                    
                    batch_docs = []
                    time.sleep(0.2)
                    
            except json.JSONDecodeError as e:
                print(f"Invalid JSON on line {line_num}: {e}")
                continue
        
        # Send remaining documents
        if batch_docs:
            success, indexed = send_batch(batch_docs)
            batch_count += 1
            if success:
                successful_docs += indexed
                print(f"Final batch {batch_count}: {indexed}/{len(batch_docs)} docs successful")
            else:
                print(f"Final batch {batch_count} FAILED")
    
    elapsed = time.time() - start_time
    rate = successful_docs / elapsed if elapsed > 0 else 0
    
    print(f"\nIngestion complete:")
    print(f"Total documents processed: {total_docs:,}")
    print(f"Successfully ingested: {successful_docs:,}")
    print(f"Failed: {total_docs - successful_docs:,}")
    print(f"Total batches: {batch_count}")
    print(f"Time: {elapsed:.1f}s | Rate: {rate:.0f} docs/sec")
    
    # Refresh and check final count
    print(f"\nRefreshing index...")
    try:
        refresh_response = requests.post(
            f"{OPENSEARCH_ENDPOINT}/{INDEX_NAME}/_refresh",
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            verify=False
        )
        print(f"Refresh status: {refresh_response.status_code}")
        
        count_response = requests.get(
            f"{OPENSEARCH_ENDPOINT}/{INDEX_NAME}/_count",
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            verify=False
        )
        
        if count_response.status_code == 200:
            count = count_response.json().get('count', 0)
            print(f"Final index count: {count:,} documents")
    except Exception as e:
        print(f"Refresh error: {e}")

if __name__ == "__main__":
    main()