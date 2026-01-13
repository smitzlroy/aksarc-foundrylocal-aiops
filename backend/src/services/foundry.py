"""Foundry Local AI client service."""

import httpx
import structlog
from typing import AsyncGenerator

logger = structlog.get_logger(__name__)


class FoundryConnectionError(Exception):
    """Raised when unable to connect to Foundry Local."""

    pass


class FoundryTimeoutError(Exception):
    """Raised when Foundry query times out."""

    pass


class FoundryClient:
    """Client for interacting with Azure AI Foundry Local.

    This client handles communication with the local Foundry instance,
    including health checks, query submission, and response streaming.
    """

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:58366",
        model: str = "qwen2.5-0.5b",
        timeout: float = 30.0,
    ) -> None:
        """Initialize Foundry client.

        Args:
            endpoint: Foundry Local endpoint URL
            model: Model name to use for queries
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

        logger.info(
            "foundry_client_initialized",
            endpoint=self.endpoint,
            model=self.model,
            timeout=self.timeout,
        )

    async def health_check(self) -> bool:
        """Check if Foundry Local is accessible and healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try common health check endpoints
            endpoints_to_try = [
                f"{self.endpoint}/health",
                f"{self.endpoint}/v1/models",
                f"{self.endpoint}/",
            ]

            for health_endpoint in endpoints_to_try:
                try:
                    response = await self.client.get(health_endpoint)
                    if response.status_code in (200, 404):  # 404 is ok, means server is up
                        logger.info(
                            "foundry_health_check_success",
                            endpoint=health_endpoint,
                            status_code=response.status_code,
                        )
                        return True
                except httpx.RequestError:
                    continue

            logger.warning("foundry_health_check_failed_all_endpoints")
            return False

        except Exception as e:
            logger.error("foundry_health_check_error", error=str(e), exc_info=e)
            return False

    async def query(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """Send a query to Foundry Local and get response.

        Args:
            prompt: User's query or prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response

        Returns:
            AI-generated response text

        Raises:
            FoundryConnectionError: If unable to connect
            FoundryTimeoutError: If query times out
        """
        try:
            logger.info("foundry_query_start", prompt_length=len(prompt))

            # Foundry Local typically uses OpenAI-compatible API
            request_body = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            response = await self.client.post(
                f"{self.endpoint}/v1/chat/completions",
                json=request_body,
            )

            response.raise_for_status()
            data = response.json()

            # Extract response text
            if "choices" in data and len(data["choices"]) > 0:
                response_text = data["choices"][0]["message"]["content"]
                logger.info(
                    "foundry_query_success",
                    response_length=len(response_text),
                    model=self.model,
                )
                return response_text
            else:
                logger.error("foundry_response_invalid_format", data=data)
                raise FoundryConnectionError("Invalid response format from Foundry")

        except httpx.TimeoutException as e:
            logger.error("foundry_query_timeout", timeout=self.timeout, exc_info=e)
            raise FoundryTimeoutError(f"Query timed out after {self.timeout}s") from e

        except httpx.RequestError as e:
            logger.error("foundry_connection_error", error=str(e), exc_info=e)
            raise FoundryConnectionError(f"Unable to connect to Foundry: {e}") from e

        except Exception as e:
            logger.error("foundry_query_error", error=str(e), exc_info=e)
            raise

    async def stream_query(
        self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048
    ) -> AsyncGenerator[str, None]:
        """Stream response from Foundry Local token by token.

        Args:
            prompt: User's query or prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response

        Yields:
            Response tokens as they arrive

        Raises:
            FoundryConnectionError: If unable to connect
            FoundryTimeoutError: If query times out
        """
        try:
            logger.info("foundry_stream_query_start", prompt_length=len(prompt))

            request_body = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
            }

            async with self.client.stream(
                "POST",
                f"{self.endpoint}/v1/chat/completions",
                json=request_body,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix

                        if data_str == "[DONE]":
                            break

                        try:
                            import json

                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue

            logger.info("foundry_stream_query_complete")

        except httpx.TimeoutException as e:
            logger.error("foundry_stream_timeout", timeout=self.timeout, exc_info=e)
            raise FoundryTimeoutError(f"Stream timed out after {self.timeout}s") from e

        except httpx.RequestError as e:
            logger.error("foundry_stream_connection_error", error=str(e), exc_info=e)
            raise FoundryConnectionError(f"Unable to connect to Foundry: {e}") from e

        except Exception as e:
            logger.error("foundry_stream_error", error=str(e), exc_info=e)
            raise

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("foundry_client_closed")


async def test_foundry_connection() -> None:
    """Test script to validate Foundry Local connection.

    This function tests connectivity and basic query functionality
    with Foundry Local. Run this to verify setup before building
    the full application.
    """
    print("🔍 Testing Foundry Local connection...")
    print(f"📍 Endpoint: http://127.0.0.1:58366")
    print(f"🤖 Model: qwen2.5-0.5b\n")

    client = FoundryClient(
        endpoint="http://127.0.0.1:58366",
        model="qwen2.5-0.5b",
        timeout=30.0,
    )

    try:
        # Test 1: Health check
        print("Test 1: Health Check")
        is_healthy = await client.health_check()
        if is_healthy:
            print("✅ Health check passed - Foundry Local is accessible\n")
        else:
            print("❌ Health check failed - Foundry Local is not accessible\n")
            return

        # Test 2: Simple query
        print("Test 2: Simple Query")
        test_prompt = "What is Kubernetes? Answer in one sentence."
        print(f"Question: {test_prompt}")

        response = await client.query(test_prompt, temperature=0.7, max_tokens=100)
        print(f"Response: {response}\n")
        print("✅ Query test passed\n")

        # Test 3: Streaming query
        print("Test 3: Streaming Query")
        stream_prompt = "List 3 benefits of using Kubernetes."
        print(f"Question: {stream_prompt}")
        print("Streaming response: ", end="", flush=True)

        async for token in client.stream_query(stream_prompt, temperature=0.7, max_tokens=200):
            print(token, end="", flush=True)

        print("\n✅ Streaming test passed\n")

        print("🎉 All tests passed! Foundry Local is working correctly.")

    except FoundryConnectionError as e:
        print(f"❌ Connection Error: {e}")
        print("\nTroubleshooting:")
        print("1. Verify Foundry Local is running")
        print("2. Check endpoint URL is correct")
        print("3. Ensure no firewall is blocking port 58366")

    except FoundryTimeoutError as e:
        print(f"❌ Timeout Error: {e}")
        print("\nTroubleshooting:")
        print("1. Foundry Local may be processing slowly")
        print("2. Try increasing timeout value")
        print("3. Check system resources")

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

    finally:
        await client.close()
        print("\n👋 Test complete.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_foundry_connection())
