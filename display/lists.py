from typing import Iterable, Union

from flask import url_for
import content as c


def handle_web_request(query: str, recurse: bool) -> Iterable[Union[c.Symbol, c.Group]]:
    if recurse:
        ret = c.get_all_tags_path(query)
    else:
        ret = c.find_unit_tag(query)
    return filter(should_display_tag, ret)


def should_display_tag(tag: c.Symbol) -> bool:
    # Always show units
    if tag.is_unit:
        return True
    # Never show root
    if tag.is_root:
        return False
    # Not a unit nor root, thus a plain group (such as commands)
    # It can either be a ParentSymbol (which means it is the group that is currently shown), or not
    # a ParentSymbol (which means it's a child of the currently shown group)
    # It should be shown only in the latter case, when it's not a ParentSymbol
    if c.is_parent_symbol(tag):
        return False
    # Better display than not
    return True


def build_href(tag: c.Symbol, r: bool) -> str:
    """Construct a unit tag's link. Preserves recursive mode."""
    return url_for('units_dir', tag_path=c.get_folder_path(tag)) + ('?r=' if r else '')


def build_name(tag: c.Symbol) -> str:
    """Construct the name shown under the unit tag's image. If it's a group that can be opened, adds a '>' character."""
    return f'{tag.name}{" >" if tag.is_group and not c.is_parent_symbol(tag) else ""}'
