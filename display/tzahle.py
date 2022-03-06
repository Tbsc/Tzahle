import datetime
import os
from typing import Union

import app
from content import Symbol
import content
import random


TAG_LIST_FILE = 'tzahle_list.txt'
START_DATE_FILE = 'tzahle_startdate.txt'


def open_file(which, mode):
    return open(os.path.join(app.app.root_path, which), mode)


day_tag_list: Union[list[Symbol], None] = None
start_date: Union[datetime.date, None] = None


def init_if_needed():
    global day_tag_list
    global start_date
    if day_tag_list is None:
        with open_file(TAG_LIST_FILE, 'r') as file:
            day_tag_list = list(map(lambda path: content.find_unit_tag(path.strip()), file.readlines()))
    if start_date is None:
        with open_file(START_DATE_FILE, 'r') as file:
            start_date = datetime.date.fromisoformat(file.read().strip())


def get_tag_by_date(date: datetime.date = datetime.date.today()) -> tuple[Symbol, int]:
    init_if_needed()
    delta = date - start_date
    day_num = delta.days
    return get_tag_by_day_num(day_num), day_num


def get_tag_by_day_num(day_num: Union[int, None]) -> Symbol:
    """Returns that day number's tag, or the tag of the UTC day if given None"""
    if day_num is None:
        return get_tag_by_date()[0]
    init_if_needed()
    return day_tag_list[day_num]


def generate_tag_list(write_to_file: bool = False) -> list[Symbol]:
    """Create a list of all unit tags, shuffled, with the possibility of saving the paths of the unit tags to the file,
    in the order they should be played, overwriting the file."""
    all_tags = list(set(content.get_all_unit_tags()))
    random.shuffle(all_tags)
    if write_to_file:
        with open_file(TAG_LIST_FILE, 'w') as f:
            f.writelines(map(lambda tag: content.build_full_path(tag) + '\n', all_tags))
        with open_file(START_DATE_FILE, 'w') as f:
            f.write(datetime.date.today().isoformat())
    return all_tags
