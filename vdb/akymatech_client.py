"""Client for Akymatech specialized VDB endpoints."""

import logging
import aiohttp
from typing import List, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class AkymaTechVDBClient:
    """
    Client for Akymatech specialized vector database endpoints.
    Handles connections to Jyotish and Ayurveda VDB services.
    """

    def __init__(self, base_url: str, api_key: str, service_type: str = "jyotish"):
        """
        Initialize Akymatech VDB client.

        Args:
            base_url: Base URL for the VDB service
            api_key: API key for authentication
            service_type: Type of service (jyotish or ayurveda)
        """
        self.base_url = base_url
        self.api_key = api_key
        self.service_type = service_type
        self.session = None
        self.connected = False

    async def connect(self) -> bool:
        """Connect to the Akymatech VDB service."""
        try:
            self.session = aiohttp.ClientSession()
            health = await self._health_check()
            if health.get("status") == "ok":
                self.connected = True
                logger.info(f"Connected to {self.service_type} VDB: {self.base_url}")
                return True
            else:
                logger.error(f"Health check failed for {self.service_type} VDB")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to {self.service_type} VDB: {e}")
            self.connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from the service."""
        if self.session:
            await self.session.close()
            self.connected = False
            logger.info(f"Disconnected from {self.service_type} VDB")

    async def search(
        self, query: str, query_vector: Optional[List[float]] = None, top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Search the specialized VDB.

        Args:
            query: Text query
            query_vector: Optional vector for similarity search
            top_k: Number of results to return

        Returns:
            Search results
        """
        if not self.connected:
            logger.warning(f"{self.service_type} VDB not connected")
            return {"error": "Service not connected", "results": []}

        try:
            endpoint = f"{self.base_url}/search"
            payload = {
                "query": query,
                "query_vector": query_vector,
                "top_k": top_k,
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with self.session.post(endpoint, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Search successful for {self.service_type}: {len(data.get('results', []))} results")
                    return data
                else:
                    logger.error(f"Search failed with status {response.status}")
                    return {"error": f"Search failed: {response.status}", "results": []}

        except Exception as e:
            logger.error(f"Search error: {e}")
            return {"error": str(e), "results": []}

    async def semantic_search(
        self, query_vector: List[float], top_k: int = 5, filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Perform semantic search on the VDB.

        Args:
            query_vector: Query vector
            top_k: Number of results
            filters: Optional filters

        Returns:
            Search results
        """
        if not self.connected:
            return {"error": "Service not connected", "results": []}

        try:
            endpoint = f"{self.base_url}/semantic-search"
            payload = {
                "query_vector": query_vector,
                "top_k": top_k,
                "filters": filters or {},
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with self.session.post(endpoint, json=payload, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"Semantic search failed: {response.status}", "results": []}

        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return {"error": str(e), "results": []}

    async def hybrid_search(
        self, text_query: str, query_vector: List[float], top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Perform hybrid search (keyword + semantic).

        Args:
            text_query: Text query for keyword search
            query_vector: Vector for semantic search
            top_k: Number of results

        Returns:
            Hybrid search results
        """
        if not self.connected:
            return {"error": "Service not connected", "results": []}

        try:
            endpoint = f"{self.base_url}/hybrid-search"
            payload = {
                "text_query": text_query,
                "query_vector": query_vector,
                "top_k": top_k,
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with self.session.post(endpoint, json=payload, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"Hybrid search failed: {response.status}", "results": []}

        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            return {"error": str(e), "results": []}

    async def get_metadata(self, document_id: str) -> Dict[str, Any]:
        """Get metadata for a document."""
        if not self.connected:
            return {"error": "Service not connected"}

        try:
            endpoint = f"{self.base_url}/metadata/{document_id}"
            headers = {"Authorization": f"Bearer {self.api_key}"}

            async with self.session.get(endpoint, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"Failed to get metadata: {response.status}"}

        except Exception as e:
            logger.error(f"Error getting metadata: {e}")
            return {"error": str(e)}

    async def _health_check(self) -> Dict[str, Any]:
        """Check service health."""
        try:
            endpoint = f"{self.base_url}/health"
            async with self.session.get(endpoint, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "error", "code": response.status}
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "error", "message": str(e)}

    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status."""
        return {
            "connected": self.connected,
            "service_type": self.service_type,
            "base_url": self.base_url,
            "timestamp": datetime.now().isoformat(),
        }


class AkymaTechMultiVDB:
    """Manager for multiple Akymatech VDB services."""

    def __init__(self):
        """Initialize multi-VDB manager."""
        self.clients = {}

    def add_client(self, service_name: str, client: AkymaTechVDBClient) -> None:
        """Add a client for a service."""
        self.clients[service_name] = client

    async def connect_all(self) -> Dict[str, bool]:
        """Connect to all registered services."""
        results = {}
        for name, client in self.clients.items():
            try:
                results[name] = await client.connect()
            except Exception as e:
                logger.error(f"Failed to connect {name}: {e}")
                results[name] = False
        return results

    async def disconnect_all(self) -> None:
        """Disconnect from all services."""
        for client in self.clients.values():
            try:
                await client.disconnect()
            except Exception as e:
                logger.error(f"Disconnect error: {e}")

    async def search_all(self, query: str, query_vector: Optional[List[float]] = None) -> Dict[str, Any]:
        """Search across all services."""
        results = {}
        for name, client in self.clients.items():
            if client.connected:
                results[name] = await client.search(query, query_vector)
            else:
                results[name] = {"error": "Service not connected"}
        return results

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all connections."""
        return {name: client.get_connection_status() for name, client in self.clients.items()}
