import random

import content


def random_tag():
    return random.choice(content.get_all_unit_tags())
