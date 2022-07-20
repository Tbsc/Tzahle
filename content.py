import typing
from functools import reduce
from itertools import product
import re
from collections import deque, OrderedDict
from typing import Union

from flask import url_for

final_letters_pattern = re.compile('("[ץךףןם])')
final_trans = str.maketrans('ץךףןם', 'צכפנמ')

no_punc_trans = str.maketrans('', '', '"“\'`()[],-')


def alt_name_processor(alt_names: list[str]):
    for name in alt_names:
        # Find acronyms ending with a final letter and add alternative with a regular letter
        # Doesn't work in reverse
        finals_match = re.search(final_letters_pattern, name)
        if finals_match:
            # Perhaps it's a name with multiple acronyms
            for group in finals_match.groups():
                alt_names.append(name.replace(group, group.translate(final_trans), 1))
    for name in alt_names:
        # Add alternatives without any punctuation
        # A separate loop to have alternatives without punctuation for names that were created in the previous loop
        new = name.translate(no_punc_trans)
        if name != new:
            alt_names.append(new)
    return alt_names


class Symbol:
    folder: str

    def __init__(self, name: str, alt_names: list[str], image_name: str):
        self.parent = None
        self.name = name
        self.alt_names = {name, *alt_name_processor(alt_names)}  # A set because repeats are unwanted
        self.image_name = image_name
        self.is_unit = True
        self.is_root = False
        self.is_group = False

    def asdict(self):
        return {'name': self.name, 'alt_names': self.alt_names, 'image_name': self.image_name}

    def __iter__(self):
        yield self

    def __reversed__(self):
        yield self

    def __eq__(self, other):
        # Handles root group edge case, since as a parent None is used instead of the root group object
        if self is None:
            return other is None or other.is_root
        if other is None:
            return self is None or self.is_root
        return self is other


class Group(Symbol):
    def __init__(self, name: str, alt_names: list[str], image_name: str, children: dict[str, Symbol], is_unit=True,
                 is_root=False):
        super().__init__(name, alt_names, image_name)
        self.children = {}
        for folder, child in children.items():
            self.children |= {folder: child}
            if isinstance(child, Group) and not child.is_unit:
                self.children |= child.children
        self.is_unit = is_unit
        self.is_root = is_root
        self.symbols = [*([] if is_root or not is_unit else [ParentSymbol(self)]), *self.children.values()]
        for folder, child in children.items():
            child.folder = folder
            if child.parent is None and not is_root:
                child.parent = self
            # Supply all group children's ParentSymbol with its information
            if isinstance(child, Group) and len(child.symbols) > 0 and isinstance(child.symbols[0], ParentSymbol):
                child.symbols[0].folder = child.folder
                child.symbols[0].parent = self if not is_root else None
        self.is_group = True

    def __iter__(self):
        return iter(self.symbols)

    def __reversed__(self):
        return reversed(self.symbols)


class ParentSymbol(Symbol):
    """Holds a group as a symbol."""
    def __init__(self, group: Group):
        super().__init__(group.name, [], group.image_name)
        self.group = group
        # Prevent processing alt_names again
        self.alt_names = group.alt_names


def as_singleton_tuple(var):
    if not isinstance(var, tuple):
        return var,
    return var


AltNames = list[str]
NameAndAlts = tuple[str, AltNames]
TupleStrs = tuple[str, ...]
StrOrNone = Union[str, None]
TupleStrsNones = tuple[StrOrNone, ...]
StrOrTuple = Union[str, TupleStrs]


def make_combos(types: TupleStrs, names: StrOrTuple, prenum_types: TupleStrs, num: str) -> NameAndAlts:
    names = as_singleton_tuple(names)
    ret = []
    for t in types:
        for name in names:
            ret += [f'{t} {name}'.strip(), f'{t} {name} {num}'.strip()]
    for t in prenum_types:
        ret += [f'{t} {num}'.strip()]
    hativa = 'חטיבה'
    return f'{types[0]} {names[0]} ({hativa} {num})', ret


def hatmar_combo(name: StrOrTuple, num: str) -> NameAndAlts:
    return make_combos(('עוצבת', 'חטיבת', 'חטמ"ר', 'חטיבה מרחבית', ''), name, ('חטיבה', 'חטמ"ר', 'עוצבה', 'חטיבה מרחבית', ''), num)


def ayosh_hatmar_combo(*names: str) -> NameAndAlts:
    hativat = 'חטיבת'
    hatmar = 'חטמ"ר'
    merhavit = 'חטיבה מרחבית',
    hamerhavit = 'החטיבה המרחבית'
    return f'{hativat} {names[0]}', reduce(lambda x, y: x + [f'{merhavit} {y}', f'{hatmar} {y}', f'{hamerhavit} {y}', y], ([], *names))


def join_product(*iterables: typing.Iterable[StrOrNone]) -> AltNames:
    return list(map(lambda x: " ".join(filter(None, x)), product(*iterables)))


def unit_combo(unit_type: TupleStrs, commands: TupleStrs, add_attr: TupleStrsNones = ()) -> AltNames:
    return join_product(('יחידת', 'מחלקת', *add_attr), unit_type, ('בפיקוד', 'פיקוד', None), commands)


def health_combo(command: str) -> AltNames:
    return unit_combo(('הרפואה', 'רפואה'), (command, 'ה' + command), ('חיל', None))


def intelligence_combo(command: str) -> AltNames:
    return unit_combo(('המודיעין', 'מודיעין'), (command, 'ה' + command), (None,))


def engineering_combo(command: str, unit_num: str) -> AltNames:
    return join_product(('מפקדת הנדסה', 'הנדסה', 'הנדסה קרבית', 'מפקדת הנדסה קרבית', 'חה"ן'), ('פיקוד', 'בפיקוד', None),
                        (command, 'ה' + command), (unit_num, None)) + [f'י"פ חה"ן {unit_num}']


def ammunition_combo(command: str, num: str) -> NameAndAlts:
    return f'יחידת החימוש המרחבית {num}', [f'יחידת חימוש מרחבית {num}', f'יחידת חימוש מרחבית {command}', f'אגד טכנולוגיה ואחזקה מרחבי {num}',
            f'אטנא"ם {num}', f'יחידת חימוש {num}', f'יחידת חימוש {command}']


def tikshuv_combo(gdud: str, parent_attr: str, parent_name: str, alt_definite=False, num: str = '') -> NameAndAlts:
    gdud_un = None
    if alt_definite and gdud[0] == 'ה':
        gdud_un = gdud[1:]
    return f'גדוד תקשוב {gdud}{" " + num if num != "" else ""}', join_product(
        ('גדוד', 'גדוד תקשוב', 'גדוד התקשוב', None),
        (gdud, f'{gdud} {num}', *((gdud_un, f'{gdud_un} {num}') if gdud_un is not None else ()))) + join_product(
        ('גדוד תקשוב', 'תקשוב', 'גדוד התקשוב'), (f'{parent_attr} {parent_name}', parent_name))


def isuf_combo(name: str, num: str, with_unit_names=False) -> AltNames:
    return join_product(('גדוד', 'יחידת', None) if with_unit_names else ('גדוד',),
                        (None, 'איסוף', 'איסוף קרבי'), (f'{name}', f'{num}', f'{name} {num}'))


def logistics_combo(names: StrOrTuple, num: str = None,
                    name_attr: TupleStrs = ('עוצבת', 'עוצבה', 'אוגדת', 'אוגדה')) -> AltNames:
    # num is the *logistics unit's* number if any
    names = as_singleton_tuple(names)
    name_num_tuple = (*names, num, *join_product(names, (num,))) if num is not None else names
    return join_product(('אגד', 'אגד לוגיסטי', 'אלו"ג'), (*name_num_tuple, *join_product(name_attr, name_num_tuple)))


def oref_combo(*area_names: str) -> NameAndAlts:
    start = 'פיקוד העורף מחוז'
    return f'{start} {area_names[0]}', join_product(('פיקוד העורף', 'פקע"ר'), ('מחוז', 'במחוז', None), area_names)


def ground_combo(names: StrOrTuple, num: str, otzva: bool = False, final_adds: TupleStrs = ()) -> NameAndAlts:
    if otzva:
        attrs_prename = ('עוצבת', 'חטיבת')
        attrs_prenum = ('חטיבה', 'עוצבה')
    else:
        attrs_prename = ('חטיבת',)
        attrs_prenum = ('חטיבה',)
    names = as_singleton_tuple(names)
    return f'{attrs_prename[0]} {names[0]} ({attrs_prenum[0]} {num})', [*names, *join_product(attrs_prename, names,
                                                                                              (num, None)),
                                                                        *join_product(attrs_prenum, (num,)),
                                                                        *final_adds]


def artillery_combo(name: str, num: str, attrs_prenum: StrOrTuple = (), final_adds: TupleStrs = ()) -> NameAndAlts:
    attrs_prenum = (*as_singleton_tuple(attrs_prenum), 'אגד', 'אגד ארטילרי')
    otzvat = 'עוצבת'
    return f'{otzvat} {name} ({attrs_prenum[0]} {num})', [*(f'{attr} {num}' for attr in attrs_prenum), name, f'{otzvat} {name}', *final_adds]


def police_combo(command: str, num: str):
    return f'יחידה פיקודית משטרה צבאית {command} {num}', join_product(('מ"ץ', 'משטרה צבאית', 'המשטרה הצבאית',
                                                                       'יחידה פיקודית משטרה צבאית',
                                                                       'יחידה פיקודית במשטרה הצבאית',
                                                                       'יחידה פיקודית המשטרה הצבאית', 'י"ף חמ"ץ',
                                                                       'יחידה פיקודית מ"ץ', 'י"ף משטרה צבאית'),
                                                                      ('פיקוד', 'בפיקוד', None),
                                                                      (command, 'ה' + command), (num, None))


def squadron_combo(names: StrOrTuple, num: str):
    names = as_singleton_tuple(names)
    squadron = 'טייסת'
    return f'{squadron} {names[0]} ({squadron} {num})', reduce(
        lambda x, name: x + [f'{squadron} {name}', f'{squadron} {name} {num}', f'{name} {num}', name],
        ([f'{squadron} {num}'], *names))


__logistics_unit_tags = Group('אגף הטכנולוגיה והלוגיסטיקה', ['אגף לוגיסטיקה', 'אגף טכנולוגיה ולוגיסטיקה', 'אט"ל'], 'logitech.png', {
    'technology': Group('חיל הטכנולוגיה והאחזקה', ['חיל החימוש', 'חיל טכנולוגיה ואחזקה', 'חיל הטנ"א', 'חיל טנ"א', 'חיל הטכנולוגיה', 'חיל טכנולוגיה'], 'technology.png', {
        'repair': Symbol('מרכז שיקום ואחזקה', ['מרכז השיקום והאחזקה', 'מש"א', 'מש"א 7000'], 'repair.png'),
        'ammunition': Symbol('מרכז התחמושת', ['מרכז תחמושת', 'מרת"ח'], 'ammunition.png')
    }),
    'logistics': Group('חיל הלוגיסטיקה', ['חיל לוגיסטיקה', 'חל"ג', 'חיל התחזוקה', 'חיל תחזוקה', 'חת"ק'], 'logistics.png', {
        'supply': Symbol('מרכז ההספקה האחוד', ['מרכז הספקה אחוד', 'מרה"ס', 'מרכז הספקה'], 'supply.png'),
        'transport': Symbol('מרכז ההובלה', ['מרכז הובלה', 'מרכז ההובלה (6900)', 'מרכז הובלה (6900)'], 'transport.png')
    }),
    'health': Group('חיל הרפואה', ['חיל רפואה'], 'health.png', {
        'services': Symbol('המרכז לשירותי רפואה',
                           ['משר"פ', 'מרכז לשירותי רפואה', 'מרכז שירותי רפואה', 'מרכז שרותי רפואה'],
                           'services.png'),
        'bahad10': Symbol('בית הספר לרפואה צבאית (בה"ד 10)',
                          ['בה"ד 10', 'בית הספר לרפואה צבאית', 'בי"ס לרפואה צבאית', 'בית ספר לרפואה צבאית',
                           'בית ספר לרפואה'], 'bahad10.png'),
    }),
    'weapons': Group('החטיבה הטכנולוגית ליבשה', ['חט"ל', 'חטיבה טכנולוגית ליבשה'], 'weapons.png', {
        'yiftach': Symbol('יחידת יפת"ח', ['יפת"ח'], 'yiftach.png')
    }),
    'magal': Symbol('מערך מגל', ['מג"ל', 'מערך מג"ל'], 'magal.png'),
    'bahadim': Symbol('קריית ההדרכה על שם האלוף אריאל שרון',
                      ['קריית ההדרכה', 'עיר הבה"דים', 'קרית ההדרכה', 'קריית הדרכה', 'קרית הדרכה', 'מחנה שרון'],
                      'bahadim.png')
})


unit_tags = Group('תגי יחידה', [], '', {
    'general': Symbol('המטה הכללי', ['מטה כללי', 'מטכ"ל'], 'general.png'),
    'commands': Group('פיקודים', [], 'commands.png', {
        'north': Group('פיקוד הצפון', ['פיקוד צפון', 'פצ"ן'], 'north.png', {
            'gaash': Group('עוצבת געש (אוגדה 36)', ['עוצבת געש', 'אוגדה 36', 'עוצבת געש 36', 'געש', 'געש 36'], 'gaash.png', {
                'seon': Symbol('גדוד תקשוב שיאון',
                               join_product(('גדוד תקשוב', 'גדוד', 'גדוד התקשוב', None), ('שיאון', 'שאון'))
                               + join_product(('גדוד תקשוב', 'תקשוב', 'גדוד התקשוב'), ('עוצבת געש', 'געש')), 'seon.png'),
                'logistics': Symbol('אגד לוגיסטי עוצבת געש', logistics_combo('געש'), 'logistics.png')
            }),
            'galil': Group('עוצבת הגליל (אוגדה 91)', ['עוצבת הגליל', 'אוגדה 91', 'עוצבת הגליל 91', 'הגליל', 'הגליל 91'], 'galil.png', {
                'baram': Symbol(*hatmar_combo('ברעם', '300'), 'baram.png'),
                'hiram': Symbol(*hatmar_combo('חירם', '769'), 'hiram.png'),
                'nofim': Symbol(*tikshuv_combo('נופים', 'עוצבת', 'הגליל'), 'nofim.png'),
                'shahaf': Symbol('גדוד איסוף שחף 869', isuf_combo('שחף', '869'), 'shahaf.png'),
                'logistics': Symbol('אגד לוגיסטי עוצבת הגליל', logistics_combo(('הגליל', 'גליל')), 'logistics.png')
            }),
            'mapatz': Group('עוצבת המפץ (אוגדה 146)', ['עוצבת המפץ', 'אוגדה 146', 'אוגדה 319', 'עוצבת המפץ 146', 'המפץ', 'המפץ 146'], 'mapatz.png', {
                'logistics': Symbol('אגד לוגיסטי עוצבת המפץ 319', logistics_combo(('המפץ', 'מפץ'), '319'), 'logistics.png')
            }),
            'bashan': Group('אוגדת הבשן (אוגדה 210)', ['אוגדת הבשן', 'אוגדה 210', 'אוגדת הבשן 210', 'הבשן 210'], 'bashan.png', {
                'golan': Symbol(*hatmar_combo('הגולן', '474'), 'golan.png'),
                'hermon': Symbol(*hatmar_combo('החרמון', '810'), 'hermon.png'),
                'snir': Symbol(*tikshuv_combo('שניר', 'אוגדת', 'הבשן'), 'snir.png'),
                'ayit': Symbol('גדוד איסוף עיט 595', isuf_combo('עיט', '595'), 'ayit.png'),
                'logistics': Symbol('אגד לוגיסטי אוגדת הבשן 6366',
                                    logistics_combo(('הבשן', 'בשן'), '6366', ('אוגדת', 'אוגדה')), 'logistics.png')
            }),
            'health': Symbol('יחידת הרפואה בפיקוד הצפון', health_combo('צפון'), 'health.png'),
            'eliakim': Symbol('בסיס אימונים פיקודי אליקים',
                              ['בסיס אימונים פיקודי צפון', 'בא"פ אליקים', 'בסיס אימונים צפון',
                               'בסיס אימונים אליקים', 'בא"פ צפון', 'בסיס אליקים', 'אליקים'], 'eliakim.png'),
            'ammunition': Symbol(*ammunition_combo('צפון', '651'), 'ammunition.png'),
            'intelligence': Symbol('מחלקת המודיעין בפיקוד הצפון', intelligence_combo('צפון'), 'intelligence.png'),
            'logistics5001': Symbol('אגד לוגיסטי מרחבי 5001', ['אלמ"ר 5001', 'אגד לוגיסטי 5001'], 'logistics5001.png'),
            'logistics5002': Symbol('אגד לוגיסטי מרחבי 5002', ['אלמ"ר 5002', 'אגד לוגיסטי 5002'], 'logistics5002.png'),
            'ayalim': Symbol(*tikshuv_combo('איילים', 'פיקוד', 'צפון'), 'ayalim.png'),
            'engineering': Symbol('מפקדת הנדסה קרבית בפיקוד הצפון 801', engineering_combo('צפון', '801'), 'engineering.png')
        }),
        'center': Group('פיקוד המרכז', ['פיקוד מרכז', 'פקמ"ז'], 'center.png', {
            'ayosh': Group('אוגדת איו"ש (אוגדה 877)', ['אוגדת איו"ש', 'אוגדה 877', 'אוגדת יו"ש', 'אוגדת יהודה ושומרון',
                                                       'אוגדת אזור יהודה ושומרון'], 'ayosh.png', {
                'menashe': Symbol(*ayosh_hatmar_combo('מנשה'), 'menashe.png'),
                'efraim': Symbol(*ayosh_hatmar_combo('אפרים', 'אפריים'), 'efraim.png'),
                'shomron': Symbol(*ayosh_hatmar_combo('שומרון'), 'shomron.png'),
                'binyamin': Symbol(*ayosh_hatmar_combo('בנימין'), 'binyamin.png'),
                'yehuda': Symbol(*ayosh_hatmar_combo('יהודה'), 'yehuda.png'),
                'etzion': Symbol(*ayosh_hatmar_combo('עציון'), 'etzion.png'),
                'nitzan': Symbol('גדוד איסוף ניצן 636', isuf_combo('ניצן', '636'), 'nitzan.png'),
                'ofek': Symbol(*tikshuv_combo('אופק', 'אוגדת', 'איו"ש'), 'ofek.png')
            }),
            'fire': Group('עוצבת האש (אוגדה 98)', ['עוצבת האש', 'אוגדה 98', 'עוצבת האש 98', 'אוגדת האש', 'האש', 'האש 98'], 'fire.png', {
                'lapid': Symbol(*tikshuv_combo('לפיד', 'עוצבת', 'האש', num='492'), 'lapid.png'),
                'logistics': Symbol('יחידת שקנאי (אגד לוגיסטי עוצבת האש)',
                                    ['אגד לוגיסטי האש', 'יחידת שקנאי', 'אגד לוגיסטי עוצבת האש', 'אלו"ג שקנאי',
                                     'אלו"ג האש', 'אלו"ג עוצבת האש', 'אגד לוגיסטי שקנאי'], 'logistics.png')
            }),
            'bika': Symbol(*hatmar_combo(('הבקעה והעמקים', 'הבקעה'), '417'), 'bika.png'),
            'health': Symbol('יחידת הרפואה בפיקוד המרכז', health_combo('מרכז'), 'health.png'),
            'lachish': Symbol('בסיס אימונים פיקודי לכיש',
                              ['בסיס אימונים פיקודי מרכז', 'בא"פ לכיש', 'בא"פ מרכז', 'בסיס לכיש', 'בסיס אימונים מרכז',
                               'בסיס אימונים לכיש', 'לכיש'], 'lachish.png'),
            'ammunition': Symbol(*ammunition_combo('מרכז', '650'), 'ammunition.png'),
            'intelligence': Symbol('מחלקת המודיעין בפיקוד המרכז', intelligence_combo('מרכז'), 'intelligence.png'),
            'logistics': Symbol('אגד לוגיסטי מרחבי 5004',
                                ['אלמ"ר 5004', 'אגד לוגיסטי מרחבי מרכז', 'אגד לוגיסטי 5004', 'אגד לוגיסטי מרכז',
                                 'אגד 5004', 'אגד מרכז', '5004'],
                                'logistics.png'),
            'segev': Symbol(*tikshuv_combo('שגב', 'פיקוד', 'מרכז', num='372'), 'segev.png'),
            'engineering': Symbol('מפקדת הנדסה קרבית בפיקוד המרכז 802', engineering_combo('מרכז', '802'), 'engineering.png')
        }),
        'south': Group('פיקוד הדרום', ['פיקוד דרום', 'פד"ם'], 'south.png', {
            'gaza': Group('עוצבת שועלי האש (אוגדה 143)',
                          ['אוגדת עזה', 'עוצבת שועלי האש', 'אוגדה 143', 'עוצבת שועלי האש 143', 'אוגדת עזה 143',
                           'שועלי האש', 'עזה', 'שועלי האש 143'], 'gaza.png', {
                'geffen': Symbol('חטיבת הגפן',
                               ['חטיבת גפן', 'החטיבה הצפונית', 'החטיבה הצפונית ברצועת עזה',
                                'חטמ"ר צפונית', 'חטיבה צפונית', 'הצפונית', 'הגפן', 'גפן'],
                               'geffen.png'),
                'katif': Symbol('חטיבת קטיף', ['החטיבה הדרומית', 'החטיבה הדרומית ברצועת עזה', 'חטמ"ר דרומית',
                                               'חטיבה דרומית', 'הדרומית', 'קטיף'], 'katif.png'),
                'bsor': Symbol(*tikshuv_combo('הבשור', 'עוצבת', 'שועלי האש', alt_definite=True), 'bsor.png'),
                'nesher': Symbol('יחידת איסוף נשר 414', isuf_combo('נשר', '414', True), 'nesher.png')
            }),
            'edom': Group('עוצבת אדום (אוגדה מרחבית 80)', ['עוצבת אדום', 'אוגדה 80', 'אוגדה מרחבית 80', 'אוגמ"ר 80', 'עוצבת אדום 80', 'אדום', 'אדום 80'], 'edom.png', {
                'faran': Symbol('חטיבת פארן (חטיבה 512)', ['חטמ"ר פארן', 'חטיבה 512', 'חטיבה מרחבית פארן', 'חטיבת פארן', 'פארן', 'פארן 512'], 'faran.png'),
                'yoav': Symbol('חטיבת יואב (חטיבה 406)', ['חטמ"ר יואב', 'חטיבה 406', 'חטיבה מרחבית יואב', 'חטיבת יואב', 'יואב', 'יואב 406'], 'yoav.png'),
                'marom': Symbol(*tikshuv_combo('מרום', 'עוצבת', 'אדום'), 'marom.png'),
                'eitam': Symbol('גדוד איסוף איתם 727', isuf_combo('איתם', '727'), 'eitam.png'),
            }),
            'steel': Group('עוצבת הפלדה (אוגדה 162)', ['עוצבת הפלדה', 'אוגדה 162', 'עוצבת הפלדה 162', 'אוגדת הפלדה', 'הפלדה', 'הפלדה 162'], 'steel.png', {
                'afik': Symbol(*tikshuv_combo('אפיק', 'עוצבת', 'הפלדה'), 'afik.png'),
                'logistics': Symbol('אגד לוגיסטי עוצבת הפלדה 6162', logistics_combo(('הפלדה', 'פלדה'), '6162'), 'logistics.png')
            }),
            'sinai': Group('עוצבת סיני (אוגדה 252)', ['אוגדת סיני', 'עוצבת סיני', 'אוגדה 252', 'עוצבת סיני 252', 'סיני', 'סיני 252'], 'sinai.png', {
                'logistics': Symbol('אגד לוגיסטי עוצבת סיני', logistics_combo('סיני'), 'logistics.png')
            }),
            'health': Symbol('יחידת הרפואה בפיקוד הדרום', health_combo('דרום'), 'health.png'),
            'tzeelim': Symbol('בסיס אימונים פיקודי צאלים',
                              ['בסיס אימונים פיקודי דרום', 'בא"פ צאלים', 'בא"פ דרום', 'בסיס צאלים', 'בסיס אימונים דרום',
                               'בסיס אימונים צאלים', 'צאלים'], 'tzeelim.png'),
            'ammunition': Symbol(*ammunition_combo('דרום', '653'), 'ammunition.png'),
            'intelligence': Symbol('מחלקת המודיעין בפיקוד הדרום', intelligence_combo('דרום'), 'intelligence.png'),
            'logistics': Symbol('אגד לוגיסטי מרחבי 5006',
                                ['אלמ"ר 5006', 'אגד לוגיסטי מרחבי דרום', 'אגד לוגיסטי 5006', 'אגד לוגיסטי דרום',
                                 'אגד 5006', 'אגד דרום', '5006'],
                                'logistics.png'),
            'raam': Symbol(*tikshuv_combo('רעם', 'פיקוד', 'דרום'), 'raam.png'),
            'engineering': Symbol('מפקדת הנדסה קרבית בפיקוד הדרום 803', engineering_combo('דרום', '803'), 'engineering.png')
        }),
        'oref': Group('פיקוד העורף', ['פקע"ר'], 'oref.png', {
            'north': Symbol(*oref_combo('הצפון', 'צפון'), 'north.png'),
            'haifa': Symbol(*oref_combo('חיפה'), 'haifa.png'),
            'center': Symbol(*oref_combo('ירושלים והמרכז', 'ירושלים ומרכז', 'מרכז', 'המרכז', 'ירושלים'), 'center.png'),
            'dan': Symbol(*oref_combo('דן'), 'dan.png'),
            'south': Symbol(*oref_combo('הדרום', 'דרום'), 'south.png'),
            'rescue': Symbol('חטיבת החילוץ וההדרכה',
                             ['חטיבת החילוץ', 'חטיבת חילוץ והדרכה', 'חטיבת חילוץ', 'פלוגות חילוץ והצלה', 'פלח"ץ'],
                             'rescue.png'),
            'bahad16': Symbol('המרכז הלאומי לחילוץ, אב"ך והתגוננות אזרחית (בה"ד 16)',
                              ['בה"ד 16', 'המרכז הלאומי לחילוץ', 'המרכז הלאומי לחילוץ, אב"ך והתגוננות אזרחית',
                               'מרכז לאומי לחילוץ'], 'bahad16.png'),
            'intelligence': Symbol('מחלקת המודיעין בפיקוד העורף', intelligence_combo('עורף'), 'intelligence.png'),
            'tikshuv': Symbol('גדוד תקשוב בפיקוד העורף 456', join_product(('גדוד תקשוב', 'גדוד התקשוב'),
                                                                          ('פיקוד העורף', 'פקע"ר', 'פיקוד העורף 456',
                                                                           'פקע"ר 456', 'בפיקוד העורף',
                                                                           'בפיקוד העורף 456', '456')), 'tikshuv.png')
        }),
        'depth': Group('מפקדת העומק', ['פיקוד העומק', 'מפע"ם'], 'depth.png', {
            'intelligence': Symbol('מחלקת המודיעין במפקדת העומק', intelligence_combo('עומק'), 'intelligence.png')
        })
    }, is_unit=False),
    'forces': Group('זרועות', [], 'forces.png', {
        'ground': Group('זרוע היבשה', [], 'ground_2.png', {
            'infantry': Group('חיל הרגלים', ['חיל רגלים', 'חי"ר'], 'infantry.png', {
                'golani': Symbol(*ground_combo('גולני', '1'), 'golani.png'),
                'paratroopers': Symbol(*ground_combo(('הצנחנים', 'צנחנים'), '35'), 'paratroopers.png'),
                'givati': Symbol(*ground_combo('גבעתי', '84'), 'givati.png'),
                'oz': Symbol(*ground_combo('עוז', '89'), 'oz.png'),
                'kfir': Symbol(*ground_combo('כפיר', '900'), 'kfir.png'),
                'nahal': Symbol(*ground_combo(('הנח"ל', 'נח"ל'), '933'), 'nahal.png'),
                'carmeli': Symbol(*ground_combo('כרמלי', '2'), 'carmeli.png'),
                'alexandroni': Symbol(*ground_combo('אלכסנדרוני', '3'), 'kfir.png'),
                'sharon': Symbol(*ground_combo(('השרון', 'שרון'), '5', otzva=True), 'sharon.png'),
                'etzioni': Symbol(*ground_combo('עציוני', '6'), 'etzioni.png'),
                'oded': Symbol(*ground_combo('עודד', '9'), 'oded.png'),
                'yiftach': Symbol(*ground_combo('יפתח', '11'), 'yiftach.png'),
                'negev': Symbol(*ground_combo(('הנגב', 'נגב', 'סרגיי'), '12'), 'negev.png'),
                'jerusalem': Symbol(*ground_combo('ירושלים', '16'), 'jerusalem.png'),
                'speartip': Symbol(*ground_combo('חוד החנית', '55', otzva=True, final_adds=('המרכזית',)), 'speartip.png'),
                'nesher': Symbol(*ground_combo('נשר', '226', otzva=True, final_adds=('הצפונית',)), 'nesher.png'),
                'alon': Symbol(*ground_combo('אלון', '228', final_adds=('חטיבת הנח"ל הצפונית',)), 'alon.png'),
                'firearrows': Symbol(*ground_combo('חצי האש', '551', otzva=True), 'firearrows.png'),
                'foxes': Symbol(*ground_combo('שועלי מרום', '646', otzva=True, final_adds=('הדרומית',)), 'foxes.png'),
                'bedouin': Symbol('יחידת הסיור המדברי 585',
                                  ['יחס"ר 585', 'היחס"ר הבדואי', 'סיירי המדבר', 'גדוד הסיור המדברי', 'סיור מדברי',
                                   'יחידת סיור מדברי', 'גדוד סיור מדברי', 'יחס"ר בדואי', 'גדוד הסיור המדברי 585',
                                   'סיור מדברי 585'],
                                  'bedouin.png'),
                'bislamah': Symbol('בית הספר למפקדי כיתות ומקצועות חיל הרגלים (חטיבה 828)',
                                   ['ביסלמ"ח', 'חטיבה 828', 'בית הספר למפקדי כיתות ומקצועות חיל הרגלים',
                                    'בית ספר למפקדי כיתות ומקצועות חיל הרגלים',
                                    'בית ספר למפקדי כיתות ומקצועות חיל רגלים', 'בית ספר למפקדי כיתות',
                                    'בית הספר למפקדי כיתות', 'בית הספר למ"כים ומקצועות החי"ר'],
                                   'bislamah.png'),
                'bahad8': Symbol('בית הספר לכושר קרבי (בה"ד 8)',
                                 ['בה"ד 8', 'בית הספר לכושר קרבי', 'בית ספר לכושר קרבי'], 'bahad8.png')
            }),
            'armor': Group('חיל השריון', ['חיל שריון', 'חש"ן', 'שריון', 'השריון', 'שיריון', 'השיריון', 'חיל השיריון', 'חיל שיריון'], 'armor.png', {
                'saar': Symbol(*ground_combo('סער מגולן', '7', otzva=True), 'saar.png'),
                'barak': Symbol(*ground_combo('ברק', '188', otzva=True), 'barak.png'),
                'iron': Symbol(*ground_combo('עקבות הברזל', '401', otzva=True), 'iron.png'),
                'bneor': Symbol(*ground_combo('בני אור', '460', otzva=True, final_adds=(
                    'ביסל"ש', 'בית הספר לשריון', 'בית ספר לשריון', 'שיזפון', 'בסיס שיזפון', 'מחנה שיזפון')),
                                'bneor.png'),
                'kiryati': Symbol(*ground_combo('קרייתי', '4'), 'kiryati.png'),
                'zaken': Symbol(*ground_combo(('הזקן', 'זקן'), '8'), 'zaken.png'),
                'harel': Symbol(*ground_combo('הראל', '10'), 'harel.png'),
                'mahatz': Symbol(*ground_combo(('המחץ', 'מחץ'), '14'), 'mahatz.png'),
                'reem': Symbol(*ground_combo('ראם', '179', otzva=True), 'reem.png'),
                'ironfist': Symbol(*ground_combo('אגרוף הברזל', '205'), 'ironfist.png'),
                'yiftach': Symbol(*ground_combo('יפתח', '434', otzva=True), 'yiftach.png')
            }),
            'engineering': Group('חיל ההנדסה הקרבית', ['חיל הנדסה קרבית', 'חיל הנדסה', 'חה"ן', 'הנדסה קרבית', 'הנדסה'], 'engineering.png', {
                'asaf': Symbol('גדוד אסף 601', ['גדוד אסף', 'גדוד 601', 'אסף', 'אסף 601'], 'asaf.png'),
                'lahav': Symbol('גדוד להב 603', ['גדוד להב', 'גדוד 603', 'להב', '603'], 'lahav.png'),
                'mahatz': Symbol('גדוד המח"ץ 605', ['גדוד המח"ץ', 'גדוד 605', 'המח"ץ', '605'], 'mahatz.png'),
                'yovel': Symbol('גדוד היובל 614', ['גדוד היובל', 'גדוד 614', 'היובל', '614'], 'yovel.png'),
                'raz': Symbol('גדוד רז 7107', ['גדוד רז', 'גדוד 7107', 'רז', '7107'], 'raz.png'),
                '710': Symbol('גדוד 710', ['710'], '710.png'),
                '8170': Symbol('גדוד 8170', ['8170'], '8170.png'),
                'diamond': Symbol('יחידה הנדסית למשימות מיוחדות (יהל"ם)',
                                  ['יהל"ם', 'יחידה הנדסית למשימות מיוחדות', 'יהלו"ם'], 'diamond.png'),
                'bahad14': Symbol('בית הספר להנדסה צבאית (בה"ד 14)',
                                  ['בה"ד 14', 'בית הספר להנדסה צבאית', 'בית ספר להנדסה צבאית', 'בהל"ץ'], 'bahad14.png')
            }),
            'artillery': Group('חיל התותחנים', ['חיל תותחנים', 'חת"ם', 'תותחנים', 'התותחנים'], 'artillery.png', {
                'golan': Symbol(*artillery_combo('גולן', '282', 'חטיבת האש'), 'golan.png'),
                'pillar': Symbol(*artillery_combo('עמוד האש', '215', 'חטיבת האש'), 'pillar.png'),
                'sling': Symbol(*artillery_combo('קלע דוד', '214', 'חטיבת אש מיוחדת'), 'sling.png'),
                'flame': Symbol(*artillery_combo('שלהבת האש', '425', final_adds=(
                    'בית הספר לתותחנות וסיוע אש ביבשה', 'ביסל"ת', 'בה"ד 9', 'מחנה שבטה', 'מחנה שיבטה', 'שיבטה',
                    'שבטה', 'בית הספר לתותחנות', 'בית ספר לתותחנות')), 'flame.png'),
                'kidon': Symbol(*artillery_combo('כידון', '209'), 'kidon.png'),
                'tavor': Symbol(*artillery_combo('התבור', '454'), 'tavor.png'),
                'tkuma': Symbol(*artillery_combo('התקומה', '213', 'חטיבת האש'), 'tkuma.png'),
                'adirim': Symbol(*artillery_combo('אדירים', '7338'), 'adirim.png'),
                'zik': Symbol('יחידת זיק ירוק (יחידה 5252)',
                              ['יחידת זיק ירוק', 'יחידה 5252', 'יחידת זיק ירוק 5252', 'יחידת זיק', 'זיק', 'זיק ירוק',
                               'זיק 5252'], 'zik.png'),
                'hatam': Symbol('מרכז חת"ם', ['מרכז חיל התותחנים', 'מרכז חיל תותחנים'], 'hatam.png')
            }),
            'borders': Group('חיל הגנת הגבולות', ['חיל הגנת גבולות', 'הגנת גבולות', 'הגנת הגבולות'], 'borders.png', {
                'bahalag': Symbol('בית הספר להגנת הגבולות',
                                  ['בהל"ג', 'ביסל"ק', 'בית הספר לאיסוף קרבי', 'בית הספר למודיעין שדה', 'ביסלמ"ש',
                                   'בית ספר להגנת הגבולות', 'בית ספר להגנת גבולות', 'בית ספר לאיסוף קרבי',
                                   'בית ספר למודיעין שדה'], 'bahalag.png')
            }),
            'logistics': __logistics_unit_tags,
            'bazak': Symbol('עוצבת הבזק (אוגדה 99)', ['אוגדה 99', 'עוצבת הבזק', 'אוגדת הבזק', 'עוצבת בזק', 'עוצבת הבזק 99', 'הבזק', 'בזק', 'הבזק 99'], 'bazak.png'),
            'marom': Symbol('מרכז הטסה והכשרות מיוחדות', ['מרו"ם', 'מרהו"ם', 'מרום פתרונות מבצעיים'], 'marom.png'),
            'bahad1': Symbol('בית הספר לקצינים של צה"ל על שם חיים לסקוב (בה"ד 1)',
                             ['בה"ד 1', 'בית הספר לקצינים', 'בית ספר לקצינים'], 'bahad1.png'),
            'mali': Symbol('המרכז הלאומי לאימונים ביבשה 500',
                           [*join_product(('מרכז לאומי לאימונים ביבשה', 'המרכז הלאומי לאימונים ביבשה',
                                           'המרכז לאימונים ביבשה', 'מרכז לאימונים ביבשה', 'מל"י'), ('500', None)),
                            'באלי"ש', 'בסיס אימון ליחידות שדה', 'מחנה שומרון', 'בסיס שומרון'], 'mali.png'),
            'attack': Symbol('חטיבת התקיפה הרב-זרועית', ['חטיבת התקיפה הרב זרועית', 'חטיבת תקיפה רב זרועית'], 'attack.png')
        }),
        'air': Group('זרוע האוויר והחלל', ['חיל האוויר', 'חיל האוויר והחלל', 'זרוע האוויר', 'אוויר'], 'air.png', {
            'staff': Group('להק ראש המטה', ['למ"ט', 'להק ראש מטה', 'מטה'], 'staff.png', {}, is_unit=False),
            'generic': Symbol('תג יחידה כללי בחיל האוויר', ['חיל האוויר', 'זרוע האוויר', 'תג כללי', 'תג כללי חיל האוויר'], 'generic.png'),
            'air': Group('להק האוויר', ['לה"א', 'להק אוויר'], '', {}, is_unit=False),
            'operations': Group('להק מבצעי אוויר', ['מבצעי אוויר'], 'operations.png', {
                'control': Symbol('יחידת השליטה והמבצעים', ['יש"ם קרב 333', 'יחידת שליטה ומבצעים'], 'control.png'),
                'special': Group('כנף 7 (כנף כוחות האוויר המיוחדים)',
                                 ['כנף 7', 'כנף כוחות האוויר המיוחדים', 'כוחות האוויר המיוחדים', 'כוחות אוויר מיוחדים',
                                  'מכא"ם', 'מפקדת כוחות האוויר המיוחדים'], 'special.png', {
                    'yahak': Symbol('יחידת הנחתה קדמית (יה"ק 5700)',
                                    ['יחידת הנחתה קדמית', 'יה"ק 5700', 'יחידת ההנחתה הקדמית',
                                     'יחידת הנחתה קדמית 5700', 'יחידת ההנחתה הקדמית 5700'],
                                    'yahak.png')
                })
            }),
            'helicoop': Group('להק השתתפות ומסוקים', ['לה"מ'], '', {
                'cooperation': Symbol('היחידה לשיתוף פעולה (יחשת"ף 5620)',
                                      ['היחידה לשיתוף פעולה', 'יחידה לשיתוף פעולה', 'יחשת"ף 5620',
                                       'היחידה לשיתוף פעולה 5620', 'יחידה לשיתוף פעולה 5620', 'היחידה לשת"ף',
                                       'יחידה לשת"ף', 'היחידה לשת"ף 5620', 'יחידה לשת"ף 5620'], 'cooperation.png')
            }, is_unit=False),
            'intelligence': Group('להק המודיעין', ['למד"ן', 'להק מודיעין'], '', {
                'shatal': Symbol('יחידת שירות טכנולוגי למודיעין 121',
                                 ['יחידת שט"ל 121', 'שט"ל', 'שט"ל 121', 'יחידת שירות טכנולוגי למודיעין', 'יחידה 121',
                                  'יחידת שט"ל'], 'shatal.png')
            }, is_unit=False),
            'equipment': Group('להק הציוד', ['לצ"ד', 'להק ציוד'], '', {
                'yaa22': Symbol('יחידת האחזקה האווירית (יא"א 22)',
                                ['יא"א 22', 'יחידת האחזקה האווירית', 'יחידת אחזקה אווירית', 'יחידת האחזקה האווירית 22',
                                 'יחידת אחזקה אווירית 22'], 'yaa22.png'),
                'ofek': Symbol('יחידת אופק 324', ['יחידת אופק', 'יחידה 324', 'אופק', '324', 'אופק 324'], 'ofek.png'),
                'electric': Symbol('בית מלאכה לציוד אלקטרוני (במצ"א 108)',
                                   ['במצ"א 108', 'במצ"א', 'בית מלאכה לציוד אלקטרוני', 'בית מלאכה לציוד אלקטרוני 108'],
                                   'electric.png'),
                'lahav': Symbol('לה"ב (לוגיסטיקה, הנדסה ובקרה)', ['לה"ב', 'לוגיסטיקה, הנדסה ובקרה', 'לוגיסטיקה'], 'lahav.png'),
                'comms': Symbol('יחידת קשר (י"ק 502)', ['יחידת קשר 502', 'י"ק 502', 'יחידה 502'], 'comms.png')
            }, is_unit=False),
            'personnel': Group('להק כוח האדם', ['לכ"א', 'להק כוח אדם'], '', {
                'health': Group('מפקדת קצין רפואה חילי (מקרפ"ח 5710)',
                                ['מקרפ"ח 5710', 'מפקדת קצין רפואה חילי', 'מקרפ"ח', '5710',
                                 'מפקדת קצין רפואה חילי 5710'], 'health.png', {
                    'health': Symbol('יחידת רפואה אווירית (ירפ"א 112)',
                                     ['יחידת רפואה אווירית', 'ירפ"א 112', 'ירפ"א',
                                      'יחידת רפואה אווירית 112'], 'health.png')
                })
            }, is_unit=False),
            'protection': Group('מערך ההגנה האווירית', ['הגנ"א', 'מערך הגנה אווירית', 'הגנה אווירית'], 'protection.png', {
                'bisla': Symbol('בית הספר להגנה אווירית (ביסל"א 883)',
                                ['בית הספר להגנה אווירית', 'ביסל"א', 'משאבים', 'מחנה משאבים',
                                 'בית הספר להגנה אווירית 883', 'ביסל"א 883'], 'bisla.png'),
                'repair': Symbol('טייסת תחזוקה הגנה אווירית', ['תחזוקה הגנה אווירית', 'תחזוקה הגנ"א', 'טייסת תחזוקה הגנ"א'], 'repair.png'),
                'comms': Symbol('גדוד קשר 533', ['גדוד קשר', 'י"ק 533', 'יחידת קשר 533', 'יחידה 533', 'גדוד 533'], 'comms.png')
            }),
            'control': Group('מערך הבקרה', [], '', {
                'command': Symbol('מפקדת יחידות הבקרה האווירית (מיח"ה 517)',
                                  ['מפקדת יחידות הבקרה האווירית', 'מיח"ה 517', 'מיח"ה',
                                   'מפקדת יחידות הבקרה האווירית 517'], 'command.png')
            }, is_unit=False),
            'leadership': Symbol('בית הספר לפיקוד ומנהיגות', ['בית ספר לפיקוד ומנהיגות'], 'leadership.png'),
            'bases': Group('בסיסים', [], '', {
                'ramatdavid': Group('בסיס רמת דוד (כנף 1)', ['כנף 1', 'בסיס רמת דוד', 'רמת דוד'], 'ramatdavid.png', {
                    'valley': Symbol(*squadron_combo('העמק', '109'), 'valley.png'),
                    'combat': Symbol(*squadron_combo('הקרב הראשונה', '101'), 'combat.png'),
                    'scorpion': Symbol(*squadron_combo('העקרב', '105'), 'scorpion.png'),
                    'west': Symbol(*squadron_combo(('מגיני המערב', 'הים היחידה'), '193'), 'west.png')
                }),
                'hatzor': Group('בסיס חצור (כנף 4)', ['בסיס חצור', 'חצור', 'כנף 4'], 'hatzor.png', {
                    'camel': Symbol(*squadron_combo('הגמל המעופף', '100'), 'camel.png'),
                    'training': Symbol(*squadron_combo('מאמני קרב', '420'), 'training.png')
                }),
                'hatzerim': Group('בסיס חצרים (בח"א 6)', ['בסיס חצרים', 'חצרים', 'בח"א 6'], 'hatzerim.png', {
                    'knights': Symbol(*squadron_combo('אבירי הזנב הכתום', '107'), 'knights.png'),
                    'hammers': Symbol(*squadron_combo('הפטישים', '69'), 'hammers.png'),
                    'leopard': Symbol(*squadron_combo('הנמר המעופף', '102'), 'leopard.png'),
                    'school': Symbol('בית הספר לטיסה (ביס"ט 12)',
                                     ['ביס"ט 12', 'ביס"ט', 'בית הספר לטיסה', 'בית ספר לטיסה', 'בית הספר לטיסה 12',
                                      'בית ספר לטיסה 12'], 'school.png')
                }),
                'telnof': Group('בסיס תל נוף (בח"א 8)', ['בסיס תל נוף', 'תל נוף', 'בח"א 8'], 'telnof.png', {
                    'speartip': Symbol(*squadron_combo(('חוד החנית', 'הבז השנייה'), '106'), 'speartip.png'),
                    'doubletail': Symbol(*squadron_combo('הזנב הכפול', '133'), 'doubletail.png'),
                    'night': Symbol(*squadron_combo('מובילי הלילה', '114'), 'night.png'),
                    'raptors': Symbol(*squadron_combo('דורסי הלילה', '118'), 'raptors.png'),
                    'eagle': Symbol(*squadron_combo(('הנשר הלבן', 'המל"טים השלישית'), '210'), 'eagle.png'),
                    'experiment': Symbol('טייסת מרכז ניסויי טיסה 5601',
                                         ['טייסת מנ"ט', 'מנ"ט', 'טייסת 5601', 'מרכז ניסויי טיסה',
                                          'מרכז ניסויי טיסה 5601', 'מנ"ט 5601'], 'experiment.png'),
                    'crows': Symbol('יחידת לוחמה אלקטרונית עורבי השחקים 555',
                                    join_product(('יחידת ל"א', 'לוחמה אלקטרונית', 'יחידת לוחמה אלקטרונית', 'יחידת'),
                                                 ('עורבי השחקים', 'עורבי השחקים 555')) + join_product(
                                        ('יחידת ל"א', 'יחידה', 'יחידת לוחמה אלקטרונית', 'לוחמה אלקטרונית'), ('555',)),
                                    'crows.png'),
                    'redbaron': Symbol('טייסת הברון האדום', ['הברון האדום'], 'redbaron.png')
                }),
                'ovda': Group('בסיס עובדה (בח"א 10)', ['בסיס עובדה', 'עובדה', 'בח"א 10'], 'ovda.png', {
                    'dragon': Symbol(*squadron_combo(('הדרקון המעופף', 'הטייסת האדומה'), '115'), 'dragon.png'),
                    'bismat': Symbol('בית הספר למקצועות התעופה (ביסמ"ת)', ['ביסמ"ת', 'בית הספר למקצועות התעופה', 'בית ספר למקצועות התעופה'], 'bismat.png'),
                    'bislak': Symbol('בית הספר לקצינים של חיל האוויר (ביסל"ק)',
                                     ['ביסל"ק', 'בית הספר לקצינים', 'בית ספר לקצינים', 'בית הספר לקצינים של חיל האוויר',
                                      'בית ספר לקצינים של חיל האוויר'], 'bislak.png')
                }),
                'haifa': Group('בסיס חיפה (בח"א 21)', ['בסיס חיפה', 'חיפה', 'בח"א 21'], 'haifa.png', {
                    'bislat': Symbol('בית הספר למקצועות הטכניים (ביסל"ט)',
                                     ['ביסל"ט', 'בית הספר למקצועות הטכניים', 'בית ספר למקצועות טכניים', 'הטכני'],
                                     'bislat.png')
                }),
                'ramon': Group('בסיס רמון (כנף 25)', ['בסיס רמון', 'רמון', 'כנף 25'], 'ramon.png', {
                    'negev': Symbol(*squadron_combo('הנגב', '253'), 'negev.png'),
                    'bat': Symbol(*squadron_combo('העטלף', '119'), 'bat.png'),
                    'one': Symbol(*squadron_combo('האחת', '201'), 'one.png'),
                    'magictouch': Symbol(*squadron_combo('מגע הקסם', '190'), 'magictouch.png'),
                    'hornet': Symbol(*squadron_combo('הצרעה', '113'), 'hornet.png')
                }),
                'nevatim': Group('בסיס נבטים (בח"א 28)', ['בסיס נבטים', 'נבטים', 'בח"א 28'], 'nevatim.png', {
                    'elephants': Symbol(*squadron_combo('הפילים', '103'), 'elephants.png'),
                    'lions': Symbol(*squadron_combo('אריות הדרום', '116'), 'lions.png'),
                    'jet': Symbol(*squadron_combo('הסילון הראשונה', '117'), 'jet.png'),
                    'giants': Symbol(*squadron_combo('ענקי המדבר', '120'), 'giants.png'),
                    'nahshon': Symbol(*squadron_combo('הנחשון', '122'), 'nahshon.png'),
                    'yellowbird': Symbol(*squadron_combo('אבירי הציפור הצהובה', '131'), 'yellowbird.png'),
                    'goldeneagle': Symbol(*squadron_combo(('נשר הזהב', 'החמקן הראשונה'), '140'), 'goldeneagle.png'),
                    'loading': Symbol('יחידת ההעמסה (יחידה 757)',
                                      ['יחידת ההעמסה', 'יחידה 757', 'יחידת ההעמסה 757', 'יחידת העמסה',
                                       'יחידת העמסה 757'], 'loading.png')
                }),
                'palmahim': Group('בסיס פלמחים (בח"א 30)', ['', '', ''], 'palmahim.png', {
                    'desertbirds': Symbol(*squadron_combo('ציפורי המדבר', '123'), 'desertbirds.png'),
                    'sword': Symbol(*squadron_combo('החרב המתהפכת', '124'), 'sword.png'),
                    'malat': Symbol(*squadron_combo('המל"טים הראשונה', '200'), 'malat.png'),
                    'snake': Symbol(*squadron_combo('הנחש השחור', '161'), 'snake.png'),
                    'firebirds': Symbol(*squadron_combo('ציפורי האש', '166'), 'firebirds.png'),
                    'katmamtraining': Symbol(*squadron_combo('מאמני כטב"ם ומסוקים', '320'), 'katmamtraining.png'),
                    'katmamschool': Symbol('בית הספר למפעילי כטמ"ם',
                                           ['בית ספר למפעילי כטמ"ם', 'בית הספר לכטמ"ם', 'בית ספר לכטב"ם',
                                            'בית הספר למפעילי כטב"ם'], 'katmamschool.png'),
                    'repair': Symbol('טייסת תחזוקה פלמחים', ['תחזוקה פלמחים'], 'repair.png'),
                    'rocket': Symbol('יחידת ניסוי טילים (ינ"ט 151)',
                                     ['יחידת ניסוי טילים', 'ינ"ט 151', 'ינ"ט', 'יחידת ניסוי טילים 151'], 'rocket.png')
                })
            }, is_unit=False)
        }),
        'navy': Group('זרוע הים', ['חיל הים', 'ים'], 'navy.png', {

        })
    }, is_unit=False),
    'sections': Group('אגפים', [], 'sections.png', {
        'personnel': Group('אגף כוח האדם', ['אגף כוח אדם', 'אכ"א', 'כוח אדם'], 'personnel.png', {
            'meitav': Symbol('מיטב', ['מיט"ב', 'בקו"ם', 'יחידת מיט"ב'], 'meitav.png'),
            'police': Group('חיל המשטרה הצבאית', ['משטרה צבאית', 'חיל משטרה צבאית', 'מ"ץ', 'חמ"ץ'], 'police.png', {
                'north': Symbol(*police_combo('צפון', '390'), 'north.png'),
                'center': Symbol(*police_combo('מרכז', '391'), 'center.png'),
                'south': Symbol(*police_combo('דרום', '392'), 'south.png'),
                'staff': Symbol('יחידת משטרה צבאית המטה הכללי', join_product(
                    ('יחידת משטרה צבאית', 'יחידת המשטרה הצבאית', 'משטרה צבאית', 'המשטרה הצבאית', 'מ"ץ'),
                    ('המטה הכללי', 'מטה כללי', 'מטכ"ל')), 'staff.png'),
                'bahad13': Symbol('בית הספר למשטרה צבאית (בה"ד 13)',
                                  ['בה"ד 13', 'בית הספר למשטרה צבאית', 'בית ספר למשטרה צבאית'], 'bahad13.png'),
                'metzah': Symbol('משטרה צבאית חוקרת', ['מצ"ח', 'המשטרה הצבאית החוקרת'], 'metzah.png'),
                'passes': Symbol('המשטרה הצבאית גדודי מעבר ארז ותעוז', [], 'passes.png')
            }),
            'adjutant': Symbol('חיל משאבי האנוש', ['חיל משאבי אנוש', 'משא"ן', 'משאבי אנוש', 'משאבי האנוש'], 'adjutant.png'),
            'education': Symbol('חיל החינוך והנוער', ['חיל חינוך ונוער', 'חיל חינוך', 'חינוך', 'חינוך ונוער'], 'education.png'),
            'general': Group('החיל הכללי', ['חיל כללי', 'חכ"ל', 'כללי'], 'general.png', {
                'matpash': Symbol('מתאם פעולות הממשלה בשטחים',
                                  ['תיאום פעולות הממשלה בשטחים', 'מתפ"ש', 'המנהל האזרחי', 'מנהל אזרחי', 'מנהא"ז'],
                                  'matpash.png'),
                'complaints': Symbol('נציבות קבילות החיילים', ['נציב קבילות החיילים', 'נקח"ל'], 'complaints.png')
            }),
            'mofet': Symbol('מופת', ['יחידת מופת', 'מופ"ת', 'יחידת מופ"ת'], 'mofet.png')
        }),
        'operations': Group('אגף המבצעים', ['אגף מבצעים', 'אמ"ץ', 'אג"ם', 'אגף המטה הכללי', 'אגף מטה כללי', 'מבצעים'], 'operations.png', {
            'spokesperson': Symbol('דובר צה"ל', ['דו"ץ', 'מערך דובר צה"ל', 'מערך דו"ץ'], 'spokesperson.png')
        }),
        'intelligence': Group('אגף המודיעין', ['אמ"ן', 'אגף מודיעין', 'מודיעין'], 'intelligence.png', {
            'tikshuv': Symbol('גדוד תקשוב באגף המודיעין', join_product(('גדוד תקשוב', 'גדוד התקשוב'),
                                                                       ('אגף מודיעין', 'אמ"ן', 'אגף המודיעין',
                                                                        'באגף מודיעין', 'באמ"ן', 'באגף המודיעין')),
                              'tikshuv.png')
        }),
        'tikshuv': Group('אגף התקשוב וההגנה בסב"ר', ['אגף תקשוב', 'אגף התקשוב וההגנה בסייבר', 'את"ק', 'אגף התקשוב'], 'tikshuv.png', {
            'lotem': Group('יחידת לוטם (החטיבה להתעצמות טכנולוגית מבצעית)',
                           ['יחידת לוט"ם', 'החטיבה להתעצמות טכנולוגית מבצעית', 'חטיבת ההתעצמות', 'לוט"ם',
                            'חטיבה להתעצמות טכנולוגית מבצעית', 'היחידה לתקשוב וטכנולוגיות מידע',
                            'יחידה לתקשוב וטכנולוגיות מידע'], 'lotem.png', {
                'hoshen': Group('מרכז חושן', ['חושן', 'יחידת חושן'], '', {
                    'amirim': Symbol('גדוד אמירים 376', ['גדוד אמירים', 'אמירים', 'גדוד 376', 'אמירים 376'], 'amirim.png'),
                    'tzameret': Symbol('גדוד צמרת 383', ['גדוד צמרת', 'צמרת', 'גדוד 383', 'צמרת 383'], 'tzameret.png'),
                    'eitanim': Symbol('גדוד איתנים 858', ['גדוד איתנים', 'איתנים', 'גדוד 858', 'איתנים 858'], 'eitanim.png')
                }, is_unit=False),
               'basmach': Symbol('בית הספר למקצועות המחשב וההגנה בסב"ר',
                                 ['בסמ"ח', 'בית הספר למקצועות המחשב',
                                  'בית ספר למקצועות המחשב וההגנה בסב"ר',
                                  'בית הספר למקצועות המחשב וההגנה בסייבר'], 'basmach.png')
            }),
            'bahad7': Symbol('בית הספר הארצי לקשר, תקשוב וסב"ר (בה"ד 7)',
                             ['בה"ד 7', 'בית הספר הארצי לקשר', 'בית הספר לקשר', 'בית הספר הארצי לקשר, תקשוב וסב"ר',
                              'בית הספר הארצי לקשר, תקשוב וסייבר'], 'bahad7.png'),
            'psagot': Symbol('גדוד לוחמה אלקטרונית פסגות',
                             ['גדוד ל"א', 'ל"א', 'לוחמה אלקטרונית', 'פסגות', 'גדוד פסגות', 'גדוד לוחמה אלקטרונית'],
                             'psagot.png')
        }),
        'planning': Symbol('אגף התכנון ובניין הכוח הרב-זרועי',
                           ['אג"ת', 'אגף התכנון', 'אגף בניין הכוח', 'אגף בניין כוח', 'אגף תכנון ובניין כוח',
                            'אגף תכנון ובניין כוח רב זרועי'], 'planning.png'),
        'strategy': Symbol('אגף אסטרטגיה ומעגל שלישי', ['אגף אסטרטגיה', 'אגף האסטרטגיה', 'אגא"ס'], 'strategy.png')
    }, is_unit=False),
    'courts': Symbol('יחידת בתי הדין הצבאיים',
                     ['בתי הדין הצבאיים', 'בית דין צבאי', 'יבד"ץ', 'יבד"ץ 205', 'יחידה 205', 'בתי דין צבאיים',
                      'בתי דין', 'בתי הדין', 'בית דין'],
                     'courts.png'),
    'advocate': Group('הפרקליטות הצבאית', ['פרקליטות צבאית', 'מפקדת הפרקליט הצבאי הראשי', 'מפצ"ר', 'פרקליטות', 'הפרקליטות'], 'advocate.png', {
        'defense': Symbol('הסנגוריה הצבאית', ['הסנגוריה', 'סנגוריה צבאית', 'סנגוריה'], 'defense.png')
    })
}, is_unit=False, is_root=True)


def find_unit_tag(path: str, joiner='/') -> Union[Symbol, Group, None]:
    """Get the wanted unit tag, following the given path. The path must be slash-separated. Returns the symbol
    object, or None if not found. Can return both groups and symbols, using the same syntax."""
    # None or empty paths mean root
    if path is None or path == '':
        return unit_tags

    paths = path.split(joiner)
    ret = unit_tags
    try:
        for folder in paths:
            if folder != '':
                ret = ret.children[folder]
    except KeyError:
        return None
    return ret


def join_path(base: str, folder: str, joiner: str = '/') -> str:
    return base + joiner + folder


def build_root_path(tag: Symbol, joiner='/') -> str:
    """Traverses the parent chain to create a string describing the path of the tag"""
    ret = ''
    parent: Group = tag.parent
    while parent is not None:
        ret = join_path(parent.folder, ret, joiner)
        parent = parent.parent
    return ret


def build_image_path(tag: Symbol, joiner='/') -> str:
    return build_root_path(tag, joiner) + tag.image_name


def build_full_path(tag: Symbol, joiner='/') -> str:
    return build_root_path(tag, joiner) + tag.folder


def build_full_image_path(tag: Symbol) -> str:
    return url_for('static', filename='units/' + build_image_path(tag))


def get_all_unit_tags(group=unit_tags) -> list[Symbol]:
    """Returns all tags under the given group. Includes both symbols and groups marked as a unit."""
    # If it's just a symbol and not a group (thus no children), no recursion was done, simply return the symbol
    if not group.is_group:
        return list(group)

    # Was given a group, begin going through its immediate children
    # All the reversing and left-appends are needed to have the result ordered correctly
    # extendleft reverses the given iterable when appending, so a reverse to undo that
    ret = deque()
    for child in reversed(group.children.values()):
        # The group builder adds grandchildren whose parent is not a unit to the grandparent
        # This means duplicate symbols when recursing! Add this check to make sure we add only direct children
        if child.parent != group:
            continue
        # Append only the end symbols, the group itself is added later outside the loop through the recursion
        if isinstance(child, Group):
            ret.extendleft(reversed(get_all_unit_tags(child)))
        elif child.is_unit:
            ret.appendleft(child)

    # The for loop above only adds end symbols, this is what adds the groups
    # No need to add groups that aren't units, such as the commands or sections groups.
    if group.is_unit:
        ret.appendleft(group)

    return list(ret)


def get_all_tags_in_path(path: str, joiner='/') -> list[Symbol]:
    """Recursively returns all unit tags in a group, specified by path"""
    return get_all_unit_tags(find_unit_tag(path, joiner))


def is_parent_symbol(tag: Symbol) -> bool:
    """Is the tag a ParentSymbol, that is a group that is being displayed as a unit and not a group"""
    return isinstance(tag, ParentSymbol)
