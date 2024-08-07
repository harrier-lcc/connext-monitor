
import datetime
import logging
import multiprocessing
import web3
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from eth_abi.codec import ABICodec
from eth_abi.registry import registry


from .abi import XCALLED_ABI, EXECUTED_ABI, RECONCILED_ABI
from .config import AlertConfig
from .observers import ABISignature

class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
    )    

class XCalledParams(BaseSchema):
    origin_domain: int
    destination_domain: int
    canonical_domain: int
    to: str
    delegate: str
    receive_local: bool
    call_data: bytes
    slippage: int
    origin_sender: str
    bridged_amt: int
    normalized_in: int
    nonce: int
    canonical_id: bytes

class XCalledEvent(BaseSchema):
    transfer_id: bytes
    nonce: int
    message_hash: bytes
    params: XCalledParams
    asset: str
    amount: int
    local: str
    message_body: bytes

class ExecutedParams(BaseSchema):
    origin_domain: int
    destination_domain: int
    canonical_domain: int
    to: str
    delegate: str
    receive_local: bool
    call_data: bytes
    slippage: int
    origin_sender: str
    bridged_amt: int
    normalized_in: int
    nonce: int
    canonical_id: bytes

class ExecutedArgs(BaseSchema):
    params: ExecutedParams
    routers: list[str]
    router_signatures: list[bytes]
    sequencer: str
    sequencer_signature: bytes


class ExecutedEvent(BaseSchema):
    transfer_id: bytes
    to: str
    asset: str
    args: ExecutedArgs
    local: str
    amount: int
    caller: str


class ReconciledEvent(BaseSchema):
    transfer_id: bytes
    origin_domain: int
    local: str
    routers: list[str]
    amount: int
    caller: str

class TransferChecker():
    def __init__(self, id, event_queue: multiprocessing.Queue, config: AlertConfig, scheduler_queue: multiprocessing.Queue) -> None:
        self.id = id
        self.queue = event_queue
        self.alert_config = config
        self.scheduler_queue = scheduler_queue
        self.logger = logging.getLogger(f"transfer_checker_{id}")
        self.logger.info(f"Initialize checker")


    def run(self):
        self.logger.info("Start checker")
        while True:
            (chain_id, event, timestamp) = self.queue.get()
            topics = event['topics']
            match topics[0].hex():
                case ABISignature.XCALLED_SIGNATURE:
                    self.process_xcalled(chain_id, event, timestamp)
                case ABISignature.EXECUTED_SIGNATURE:
                    self.process_executed(chain_id, event, timestamp)
                case ABISignature.RECONCILED_SIGNATURE:
                    self.process_reconciled(chain_id, event, timestamp)
                case _:
                    # NOTE: we do not handle any other log type yet
                    pass


    def process_xcalled(self, chain_id, event, timestamp):
        event_data = web3._utils.events.get_event_data(ABICodec(registry), XCALLED_ABI, event)
        event = XCalledEvent(**event_data['args'])
        transfer_id = event.transfer_id.hex()
        if event.params.destination_domain not in self.alert_config.domains:
            self.logger.debug(f"Skipped {transfer_id} with unsupported domain {event.params.destination_domain}")
            return

        block_time = datetime.datetime.fromtimestamp(timestamp)
        execution_alert_time = block_time + self.alert_config.execution_max_time
        reconcile_alert_time = block_time + self.alert_config.reconcile_max_time
        self.scheduler_queue.put(("add", f"{transfer_id}_execution", execution_alert_time, f"Transfer execution max wait time breached {transfer_id}"))
        self.scheduler_queue.put(("add", f"{transfer_id}_reconcile", reconcile_alert_time, f"Transfer reconcile max wait time breached {transfer_id}"))
        # TODO: Insert transfer into database
        self.logger.info(f"Processing xcalled {transfer_id}")


    def process_executed(self, chain_id, event, timestamp):
        event_data = web3._utils.events.get_event_data(ABICodec(registry), EXECUTED_ABI, event)
        event = ExecutedEvent(**event_data["args"])
        transfer_id = event.transfer_id.hex()
        self.scheduler_queue.put(("remove", f"{transfer_id}_execution"))
        # TODO: get transfer from database and update executed_time
        self.logger.info(f"Processing excecuted {event.transfer_id.hex()}")
        
    def process_reconciled(self, chain_id, event, timestamp):
        event_data = web3._utils.events.get_event_data(ABICodec(registry), RECONCILED_ABI, event)
        event = ReconciledEvent(**event_data['args'])
        transfer_id = event.transfer_id.hex()
        self.scheduler_queue.put(("remove", f"{transfer_id}_reconcile"))
        # TODO: get transfer from database and update executed_time
        self.logger.info(f"Processing reconciled {event.transfer_id.hex()}")
