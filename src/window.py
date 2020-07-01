import cuid
import datetime
from storage import Storage
from collections import Iterable
from utils import get_logger

logger = get_logger()


class Window:
    class StopCrits:
        INGESTION_TIME = 0
        LENGTH = 1
        SINGLE_RECORD = 2

    def __init__(self, stop_crit, stop_value=None, group_by_keys=None, window_id=None, storage_mode = None):
        self.stop_crit = stop_crit
        self.window_id = cuid.cuid() if not window_id else window_id
        self.group_by_keys = group_by_keys if group_by_keys else []
        self.stop_value = stop_value
        self.cache = Storage(storage_mode)
        self.existing_keys = set()

        self._count = None
        self.reset_window()

    def reset_count(self):
        if self.stop_crit == Window.StopCrits.INGESTION_TIME:
            self._count = datetime.datetime.now().timestamp()
        elif self.stop_crit == Window.StopCrits.LENGTH:
            self._count = 0
        elif self.stop_crit == Window.StopCrits.SINGLE_RECORD:
            self._count = None
        else:
            raise NotImplementedError("Only supporting windows by ingestiontime or length.")

    def reset_window(self):
        self.reset_count()

        for key in self.existing_keys:
            self.cache.dump(key)
            logger.debug(f"Dumped data for key {key}")

        self.existing_keys = set()
        logger.info("reset window")

    def add_dict_to_storage(self, item):
        grouping_values = [str(item[key]) for key in self.group_by_keys]
        storage_key = "_".join([self.window_id] + grouping_values)
        logger.debug(f"adding item {item} with key {storage_key} to cache.")
        self.existing_keys.add(storage_key)

        self.cache.append(storage_key, item)

    def add_to_window(self, values):
        if not isinstance(values, Iterable) or isinstance(values, dict):
            data = [values]
        else:
            data = values
        for item in data:
            if not isinstance(item, dict):
                self.add_to_window(item)
            else:
                self.add_dict_to_storage(item)

        if self.stop_crit == Window.StopCrits.LENGTH:
            self._count += 1

    def return_window_data(self, reset_window = True):
        data = []
        keys = []
        for key in self.existing_keys:
            data.append(self.cache.get(key))
            keys.append(key)

        if reset_window:
            self.reset_window()
        return keys, data

    def stop_crit_applies(self):
        if self.stop_crit == Window.StopCrits.SINGLE_RECORD:
            return True
        elif self.stop_crit == Window.StopCrits.LENGTH:
            if self._count >= self.stop_value:
                return True
        elif self.stop_crit == Window.StopCrits.INGESTION_TIME:
            if datetime.datetime.now().timestamp() - self._count >= self.stop_value:
                return True
        else:
            return False
