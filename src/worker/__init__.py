from worker.kafka_worker import KafkaWorker
from utils.config_parser import parse_config
from utils import get_logger

def get_worker(config_path, designated_task = None):
    plattform_config, tasks = parse_config(config_path)

    logger = get_logger()
    logger.info("parsed config")
    logger.debug(plattform_config)
    logger.debug(tasks)

    if designated_task:
        tasks = [task for task in tasks if task.name == designated_task]
        logger.debug(f"Chose designated task {tasks}")
    
    worker_type = plattform_config.type

    #this can certainly be done in a nicer way...
    if worker_type == 'kafka':
        return KafkaWorker(plattform_config, tasks)
