from locust import HttpUser, task, between
import random
from pathlib import Path
import os
from requests.auth import HTTPBasicAuth


class ThreadPoolMetrics:
    def __init__(self):
        self.active = 0
        self.queue = 0
        self.rejected = 0


class OpenSearchPPLUser(HttpUser):
    queries = {}
    log_type = None

    def on_start(self):
        # Add authentication if credentials are provided via environment variables
        username = os.getenv("OPENSEARCH_USER")
        password = os.getenv("OPENSEARCH_PASSWORD")
        
        if username and password:
            self.client.auth = HTTPBasicAuth(username, password)
            print(f"Using authentication for user: {username}")
        
        # Determine which log type to test from environment variable
        # Options: vpc, nfw, cloudtrail, waf, or 'all' (default)
        OpenSearchPPLUser.log_type = os.getenv("LOG_TYPE", "all").lower()
        
        if not OpenSearchPPLUser.queries:
            self._load_queries()

    def _load_queries(self):
        """Load PPL queries based on log type selection"""
        ppl_base = Path("ppl")
        
        if OpenSearchPPLUser.log_type == "all":
            # Load from all subdirectories
            log_types = ["vpc", "nfw", "cloudtrail", "waf"]
        else:
            # Load only from specified log type
            log_types = [OpenSearchPPLUser.log_type]
        
        for log_type in log_types:
            log_type_dir = ppl_base / log_type
            if log_type_dir.exists() and log_type_dir.is_dir():
                for ppl_file in log_type_dir.glob("*.ppl"):
                    with open(ppl_file, "r") as f:
                        query = f.read().strip()
                        # Include log type in query name for identification
                        query_name = f"{log_type}/{ppl_file.stem}"
                        OpenSearchPPLUser.queries[query_name] = query
        
        if not OpenSearchPPLUser.queries:
            raise RuntimeError(
                f"No queries found for log type: {OpenSearchPPLUser.log_type}. "
                f"Please ensure the ppl/{OpenSearchPPLUser.log_type} directory exists and contains .ppl files."
            )
        
        print(f"Loaded {len(OpenSearchPPLUser.queries)} queries for log type(s): {OpenSearchPPLUser.log_type}")

    wait_time = between(1, 3)

    @task
    def execute_ppl_query(self):
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
