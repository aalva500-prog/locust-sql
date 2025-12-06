from locust import HttpUser, task, between
import random
from pathlib import Path
import os
import json
from requests.auth import HTTPBasicAuth


class ThreadPoolMetrics:
    def __init__(self):
        self.active = 0
        self.queue = 0
        self.rejected = 0


class OpenSearchPPLUser(HttpUser):
    queries = {}
    dsl_queries = {}
    log_type = None
    query_type = None

    def on_start(self):
        # Add authentication if credentials are provided via environment variables
        username = os.getenv("OPENSEARCH_USER")
        password = os.getenv("OPENSEARCH_PASSWORD")
        
        if username and password:
            self.client.auth = HTTPBasicAuth(username, password)
            print(f"Using authentication for user: {username}")
        
        # Determine which log type to test from environment variable
        # Options: vpc, nfw, cloudtrail, waf, big5, or 'all' (default)
        OpenSearchPPLUser.log_type = os.getenv("LOG_TYPE", "all").lower()
        
        # Determine which query type to test from environment variable
        # Options: ppl, dsl, or 'both' (default)
        OpenSearchPPLUser.query_type = os.getenv("QUERY_TYPE", "both").lower()
        
        if not OpenSearchPPLUser.queries and not OpenSearchPPLUser.dsl_queries:
            self._load_queries()

    def _load_queries(self):
        """Load PPL and/or DSL queries based on log type and query type selection"""
        if OpenSearchPPLUser.log_type == "all":
            # Load from all subdirectories
            log_types = ["vpc", "nfw", "cloudtrail", "waf", "big5"]
        else:
            # Load only from specified log type
            log_types = [OpenSearchPPLUser.log_type]
        
        # Load PPL queries if query_type is 'ppl' or 'both'
        if OpenSearchPPLUser.query_type in ["ppl", "both"]:
            ppl_base = Path("ppl")
            for log_type in log_types:
                log_type_dir = ppl_base / log_type
                if log_type_dir.exists() and log_type_dir.is_dir():
                    for ppl_file in log_type_dir.glob("*.ppl"):
                        with open(ppl_file, "r") as f:
                            query = f.read().strip()
                            # Include log type in query name for identification
                            query_name = f"{log_type}/{ppl_file.stem}"
                            OpenSearchPPLUser.queries[query_name] = query
            
            if OpenSearchPPLUser.queries:
                print(f"Loaded {len(OpenSearchPPLUser.queries)} PPL queries for log type(s): {OpenSearchPPLUser.log_type}")
        
        # Load DSL queries if query_type is 'dsl' or 'both'
        if OpenSearchPPLUser.query_type in ["dsl", "both"]:
            dsl_base = Path("dsl")
            for log_type in log_types:
                log_type_dir = dsl_base / log_type
                if log_type_dir.exists() and log_type_dir.is_dir():
                    for dsl_file in log_type_dir.glob("*.dsl"):
                        with open(dsl_file, "r") as f:
                            query_json = json.load(f)
                            # Include log type in query name for identification
                            query_name = f"{log_type}/{dsl_file.stem}"
                            OpenSearchPPLUser.dsl_queries[query_name] = query_json
            
            if OpenSearchPPLUser.dsl_queries:
                print(f"Loaded {len(OpenSearchPPLUser.dsl_queries)} DSL queries for log type(s): {OpenSearchPPLUser.log_type}")
        
        # Validate that at least some queries were loaded
        if not OpenSearchPPLUser.queries and not OpenSearchPPLUser.dsl_queries:
            raise RuntimeError(
                f"No queries found for log type: {OpenSearchPPLUser.log_type} and query type: {OpenSearchPPLUser.query_type}. "
                f"Please ensure the appropriate directories exist and contain query files."
            )

    wait_time = between(1, 3)

    @task
    def execute_ppl_query(self):
        # Only execute if PPL queries are available and query_type allows PPL
        if not self.queries or self.query_type not in ["ppl", "both"]:
            return
        
        query_name = random.choice(list(self.queries.keys()))
        query = self.queries[query_name]

        payload = {"query": query}

        with self.client.post(
            "/_plugins/_ppl",
            json=payload,
            headers={"Content-Type": "application/json"},
            name=f"PPL Query: {query_name}",
            catch_response=True,
        ) as response:
            try:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Got status code {response.status_code}")
            except Exception as e:
                response.failure(f"Request failed: {str(e)}")

    @task
    def execute_dsl_query(self):
        # Only execute if DSL queries are available and query_type allows DSL
        if not self.dsl_queries or self.query_type not in ["dsl", "both"]:
            return
        
        query_name = random.choice(list(self.dsl_queries.keys()))
        query_json = self.dsl_queries[query_name]
        
        # Extract log type from query name (format: "log_type/query_name")
        log_type = query_name.split("/")[0]
        
        # Use the log type as the index name
        index_name = log_type

        with self.client.post(
            f"/{index_name}/_search",
            json=query_json,
            headers={"Content-Type": "application/json"},
            name=f"DSL Query: {query_name}",
            catch_response=True,
        ) as response:
            try:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Got status code {response.status_code}")
            except Exception as e:
                response.failure(f"Request failed: {str(e)}")
