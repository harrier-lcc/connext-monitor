import multiprocessing
import asyncio
import concurrent.futures
import os
import logging

from .config import load_config, Config
from .alert_manager import DiscordAlert, AlertManager
from .observers import Observer
from .providers import get_provider
from .scheduler import Scheduler
from .transfer_checker import TransferChecker

DEFAULT_LOG_LEVEL = 'WARN'
DEFAULT_CONFIG_FILE = 'config.toml'

logger = logging.getLogger(__name__)

async def run_monitor(config: Config):
    loop = asyncio.get_running_loop()


    with multiprocessing.Manager() as manager:
        event_queue = manager.Queue()

        # chain observers
        observers = []
        for chain in config.chains:
            chainConfig = config.chains[chain]
            if chain not in config.providers:
                raise f"{chain} provider not provided in config"
            provider = get_provider(config.providers[chain], chainConfig)
            await provider.start_connection()
            observers.append(Observer(provider, chainConfig, event_queue))
            
        tasks: list[asyncio.Task] = []
        for observer in observers:
            tasks.append(asyncio.create_task(observer.event_watch()))

        # Alert Manager        
        alert_queue = manager.Queue()
        alert_manager = AlertManager(alert_queue)
        if 'discord' in config.alert_providers:
            discord_alert = DiscordAlert(config.alert_providers['discord'], alert_queue)
            asyncio.ensure_future(discord_alert.start())
            asyncio.ensure_future(discord_alert.background_task())


        # Scheduler
        scheduler_queue = manager.Queue()
        scheduler = Scheduler(config.scheduler, scheduler_queue, alert_manager)
        
        # TODO: Add stat reporter thread that periodically get and report latency data from database
        # TODO: Add periodic database backup to, e.g. S3

        max_workers = config.max_worker
        checkers = [TransferChecker(i, event_queue, config.alerts, scheduler_queue) for i in range(max_workers)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            loop.run_in_executor(pool, scheduler.scheduler_process)
            worker_tasks = [
                loop.run_in_executor(pool, checkers[i].run)
                for i in range(max_workers)
            ]
            try:
                await asyncio.gather(*tasks)
            except asyncio.CancelledError:
                logger.error("Task cancelled")
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)



def entry():
    config_file = DEFAULT_CONFIG_FILE
    log_level = DEFAULT_LOG_LEVEL
    if "CONNEXT_LOG_LEVEL" in os.environ:
        log_level = os.environ['CONNEXT_LOG_LEVEL']
    if "CONNEXT_CONFIG" in os.environ:
        config_file = os.environ['CONNEXT_CONFIG']
    
    logging.basicConfig(level=log_level)
    logger.info(f"Getting config from {config_file}")
    config = load_config(config_file)
    logger.info(f"Current configurations: {config}")
    
    logger.info(f"Starting monitor process")
    asyncio.run(run_monitor(config))
