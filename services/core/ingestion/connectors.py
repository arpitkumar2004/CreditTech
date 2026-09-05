"""External API connectors for Account Aggregator, Geospatial, and Bureau rails."""

import uuid
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from services.core.config import get_settings
from services.core.shared.logging import get_logger

settings = get_settings()
logger = get_logger("ingestion.connectors")


def _build_client(base_url: str, timeout: float) -> httpx.AsyncClient:
    """Build an httpx client, routing through the in-process ASGI app
    when the base URL points at the test server. This is how the
    Phase-1 "every engineer runs the full stack against mocks" DoD
    is satisfied without a second network hop.
    """
    if "testserver" in base_url:
        # Lazy import to avoid a cycle: main -> ingestion -> connectors -> main.
        from services.core.main import app

        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            timeout=timeout,
        )
    return httpx.AsyncClient(timeout=timeout)


class ConnectorError(Exception):
    """Base exception for external connectors."""

    pass


class ConnectorTimeoutError(ConnectorError):
    """Raised when an external API times out."""

    pass


class AccountAggregatorConnector:
    """Connector for the Account Aggregator FIU API client."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.base_url = settings.aa_base_url.rstrip("/")
        self.client = client or _build_client(self.base_url, timeout=10.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPStatusError),
        reraise=True,
    )
    async def fetch_bank_data(self, borrower_id: uuid.UUID, aa_consent_id: str) -> dict[str, Any]:
        """Fetch transaction history and account profiles via Account Aggregator sandbox/API."""
        url = f"{self.base_url}/fetch/{borrower_id}"
        headers = {
            "Authorization": f"Bearer {settings.aa_client_secret}",
            "X-Consent-ID": aa_consent_id,
        }
        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as e:
            logger.warn("aa_timeout", borrower_id=str(borrower_id), error=str(e))
            raise ConnectorTimeoutError("Account Aggregator API timed out") from e
        except Exception as e:
            logger.error("aa_fetch_failed", borrower_id=str(borrower_id), error=str(e))
            raise ConnectorError(f"AA fetch failed: {e}") from e


class GeospatialConnector:
    """Connector for satellite imagery and weather indicators (crop-land analytics)."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.base_url = settings.geospatial_base_url.rstrip("/")
        self.client = client or _build_client(self.base_url, timeout=15.0)

    async def fetch_satellite_data(
        self, borrower_id: uuid.UUID, latitude: float, longitude: float
    ) -> dict[str, Any]:
        """Fetch NDVI scores, rainfall deviation, and crop health statistics for farm coordinates."""
        url = f"{self.base_url}/analysis"
        headers = {"X-API-Key": settings.geospatial_api_key}
        params = {
            "borrower_id": str(borrower_id),
            "lat": latitude,
            "lon": longitude,
            "seasons": "2",
        }
        try:
            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as e:
            logger.warn("geospatial_timeout", borrower_id=str(borrower_id), error=str(e))
            raise ConnectorTimeoutError("Geospatial API timed out") from e
        except Exception as e:
            logger.error("geospatial_fetch_failed", borrower_id=str(borrower_id), error=str(e))
            raise ConnectorError(f"Geospatial fetch failed: {e}") from e


class BureauConnector:
    """Connector for Credit Information Companies (CIC) to verify existing loan performance."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.base_url = settings.bureau_base_url.rstrip("/")
        self.client = client or _build_client(self.base_url, timeout=8.0)

    async def fetch_credit_profile(self, aadhaar_hash: str) -> dict[str, Any]:
        """Fetch credit profile and outstanding loan records using borrower identifier."""
        url = f"{self.base_url}/report/{aadhaar_hash}"
        headers = {"X-API-Key": settings.bureau_api_key}
        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as e:
            logger.warn("bureau_timeout", error=str(e))
            raise ConnectorTimeoutError("Bureau API timed out") from e
        except Exception as e:
            logger.error("bureau_fetch_failed", error=str(e))
            raise ConnectorError(f"Bureau fetch failed: {e}") from e
