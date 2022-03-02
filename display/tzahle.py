import datetime
import os
import typing

import app
from content import Symbol
import content
import random


TAG_LIST_FILE = 'tzahle_list.txt'
START_DATE = datetime.date(2022, 3, 2)


def open_file(mode):
    return open(os.path.join(app.app.root_path, TAG_LIST_FILE), mode)


day_tag_list: typing.Optional[list[Symbol]] = None


def init_if_needed():
    global day_tag_list
    if day_tag_list is None:
        with open_file('r') as file:
            day_tag_list = list(map(lambda path: content.find_unit_tag(path.strip()), file.readlines()))


def get_tag_of_day(date: datetime.date = datetime.date.today()) -> tuple[Symbol, int]:
    init_if_needed()
    delta = date - START_DATE
    day_num = delta.days
    return day_tag_list[day_num], day_num


def generate_tag_list(write_to_file: bool = True) -> list[Symbol]:
    """Create a list of all unit tags, shuffled, with the possibility of saving the paths of the unit tags to the file,
    in the order they should be played, overwriting the file."""
    all_tags = list(set(content.get_all_unit_tags()))
    random.shuffle(all_tags)
    if write_to_file:
        with open_file('w') as f:
            f.writelines(map(lambda tag: content.build_full_path(tag) + '\n', all_tags))
    return all_tags
