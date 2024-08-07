import logging
from typing import AsyncGenerator
import web3.middleware
from .config import ChainConfig, ProviderConfig

import web3

# TODO: Add a base class for provider

class HTTPProvider():
    def __init__(self, url, chain_config: ChainConfig) -> None:
        self.url = url
        self.w3 = web3.AsyncWeb3(web3.AsyncHTTPProvider(url))
        self.chain_config = chain_config

class WebSocketProvider():
    def __init__(self, url, chain_config: ChainConfig) -> None:
        self.url = url
        self.type = type
        self.w3 = web3.AsyncWeb3(web3.WebSocketProvider(url))
        self.chain_config = chain_config

    async def start_connection(self):
        # Add POA middleware as needed
        # Ref: https://web3py.readthedocs.io/en/stable/middleware.html#why-is-geth-poa-middleware-necessary
        match self.chain_config.chain_id:
            case 137: # Polygon
                self.w3.middleware_onion.inject(web3.middleware.ExtraDataToPOAMiddleware, layer=0)
            case _:
                pass
        await self.w3

    async def get_block(self, block):
        return await self.w3.eth.get_block(block)

    async def subscribe(self, *args) -> str:
        """ 
        Return a subscription id that is used for unsubscribe
        """
        return await self.w3.eth.subscribe("logs", *args)

    def subscription_stream(self) -> AsyncGenerator:
        """
        Return a async generator of current subscription stream
        """
        return self.w3.socket.process_subscriptions()
    

class MockAsyncLogStream():
    def __init__(self, data):
        self.data = data
    
    async def stream(self):
        for i in self.data:
            yield {"result": i}


class MockWebSocketProvider():
    """
    Mocking websocketprovider for test.
    Instead of subscribing and listening to current data, this mocks a subscription via past data.
    """
    def __init__(self, url, chain_config: ChainConfig, from_block: str) -> None:
        self.url = url
        self.type = type
        self.w3 = web3.AsyncWeb3(web3.WebSocketProvider(url))
        self.chain_config = chain_config
        self.from_block = from_block

    async def start_connection(self):
        # Add POA middleware as needed
        # Ref: https://web3py.readthedocs.io/en/stable/middleware.html#why-is-geth-poa-middleware-necessary
        match self.chain_config.chain_id:
            case 137: # Polygon
                self.w3.middleware_onion.inject(web3.middleware.ExtraDataToPOAMiddleware, layer=0)
            case _:
                pass
        await self.w3
    
    async def get_block(self, block):
        return await self.w3.eth.get_block(block)

    async def subscribe(self, *args) -> str:
        """ 
        Return a subscription id that is used for unsubscribe
        """
        assert len(args) >= 1
        obj = args[0]
        obj["fromBlock"] = self.from_block
        # TODO: set latest to be delta from from_block and do a sliding window get logs
        obj["toBlock"] = "latest"
        previous_logs = await self.w3.eth.get_logs(obj)
        self.subscription = MockAsyncLogStream(previous_logs)
        return ""

    def subscription_stream(self):
        """
        Return a async generator of current subscription stream
        """
        return self.subscription.stream()
    

def get_provider(provider_config: ProviderConfig, chain_config: ChainConfig):
    logging.info(f"Getting provider {provider_config.type} for {chain_config.chain_id}")
    match provider_config.type:
        case "http":
            return HTTPProvider(provider_config.url, chain_config)
        case "ws":
            return WebSocketProvider(provider_config.url, chain_config)
        case "ws-mock":           
            return MockWebSocketProvider(provider_config.url, chain_config, provider_config.from_block)
        case _:
            raise f"Unimplemented provider type {provider_config.type}"
