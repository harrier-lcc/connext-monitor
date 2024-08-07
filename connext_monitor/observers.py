import logging
import multiprocessing

from .providers import WebSocketProvider
from .config import ChainConfig
from .utils import chain_id_to_name

class ABISignature:
    XCALLED_SIGNATURE = "ed8e6ba697dd65259e5ce532ac08ff06d1a3607bcec58f8f0937fe36a5666c54"
    EXECUTED_SIGNATURE = "0b07a8b0b083f8976b3c832b720632f49cb8ba1e7a99e1b145f51a47d3391cb7"
    RECONCILED_SIGNATURE = "30bf44531c04b96173a40012c90db840a147cf7d50a3e160f5227f1af2faa3a0"

class Observer():
    def __init__(self, provider: WebSocketProvider, config: ChainConfig, queue: multiprocessing.Queue) -> None:
        self.provider = provider
        self.config = config
        self.queue = queue
        chain_name = chain_id_to_name(self.config.chain_id)
        self.logger = logging.getLogger(f"observer_{chain_name}")

    async def event_watch(self):
        current_block = await self.provider.w3.eth.block_number
        self.sub_id = await self.provider.subscribe({
            "address": self.config.core_contract,
            "topics": []
        })
        self.logger.info(f"Setting up event watch at block {current_block}")
        async for message in self.provider.subscription_stream():
            event = message["result"]
            topics = event['topics']
            assert len(topics) != 0, f"unknown empty topic {event}"
            match topics[0].hex():
                case ABISignature.XCALLED_SIGNATURE:
                    self.logger.debug(f"xcalled event observed {event['topics'][1].hex()}")
                case ABISignature.EXECUTED_SIGNATURE:
                    self.logger.debug(f"executed event observed {event['topics'][1].hex()}")
                case ABISignature.RECONCILED_SIGNATURE:
                    self.logger.debug(f"reconciled event observed {event['topics'][1].hex()}")
                case _:
                    self.logger.debug(f"unimplemented topic {topics[0].hex()}")
            if topics[0].hex() not in [ABISignature.XCALLED_SIGNATURE, ABISignature.EXECUTED_SIGNATURE, ABISignature.RECONCILED_SIGNATURE]:
                continue

            # Get timestamp via get_block
            block = await self.provider.get_block(event['blockNumber'])
            timestamp = block['timestamp']
            self.queue.put((self.config.chain_id, event, timestamp))
            

    async def event_unsubscribe(self):
        if self.sub_id:
            await self.provider.w3.eth.unsubscribe(self.sub_id)
