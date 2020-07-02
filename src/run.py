from worker import get_worker
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SPI worker for Apache Kafka.')
    parser.add_argument('--config-path', required=True, help='the path to the config.yml file.')
    parser.add_argument('--designated-task', required=False, help='the name of a designated task from the config file.')

    args = parser.parse_args()
    config_path = args.config_path
    designated_task = args.designated_task

    worker = get_worker(config_path, designated_task)

    worker.run()