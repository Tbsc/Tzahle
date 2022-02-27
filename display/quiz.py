import random

import content


def random_tag() -> content.Symbol:
    return random.choice(content.get_all_unit_tags())
