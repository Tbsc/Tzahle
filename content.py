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
        self.alt_names = [name, *alt_name_processor(alt_names)]
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


class Group(Symbol):
    def __init__(self, name: str, alt_names: list[str], image_name: str, children: dict[str, Symbol], is_unit=True,
                 is_root=False):
        super().__init__(name, alt_names, image_name)
        self.children = OrderedDict(children)
        self.is_unit = is_unit
        self.is_root = is_root
        self.symbols = [*([] if is_root or not is_unit else [ParentSymbol(self)]), *self.children.values()]
        for folder, child in children.items():
            child.folder = folder
            if child.parent is None and not is_root:
                child.parent = self
            # Supply all group children's ParentSymbol with its information
            if isinstance(child, Group) and isinstance(child.symbols[0], ParentSymbol):
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
        super().__init__(group.name, group.alt_names, group.image_name)
        self.group = group


def as_singleton_tuple(var):
    if not isinstance(var, tuple):
        return var,
    return var


AltNames = list[str]
NameAndAlts = tuple[str, AltNames]
TupleStrs = tuple[str, ...]
StrOrTuple = Union[str, TupleStrs]


def make_combos(types: TupleStrs, names: StrOrTuple, prenum_types: TupleStrs, num: str) -> NameAndAlts:
    names = as_singleton_tuple(names)
    ret = []
    for t in types:
        for name in names:
            ret += [f'{t} {name}', f'{t} {name} {num}']
    for t in prenum_types:
        ret += [f'{t} {num}']
    hativa = 'חטיבה'
    return f'{types[0]} {names[0]} ({hativa} {num})', ret


def hatmar_combo(name: StrOrTuple, num: str) -> NameAndAlts:
    return make_combos(('עוצבת', 'חטיבת', 'חטמ"ר'), name, ('חטיבה', 'חטמ"ר', 'עוצבה'), num)


def ayosh_hatmar_combo(*names: str) -> NameAndAlts:
    hativat = 'חטיבת'
    hatmar = 'חטמ"ר'
    merhavit = 'חטיבה מרחבית',
    hamerhavit = 'החטיבה המרחבית'
    return f'{hativat} {names[0]}', reduce(lambda x, y: x + [f'{merhavit} {y}', f'{hatmar} {y}', f'{hamerhavit} {y}'], ([], *names))


def join_product(*iterables: typing.Iterable[Union[str, None]]) -> AltNames:
    return list(map(lambda x: " ".join(filter(None, x)), product(*iterables)))


def unit_combo(unit_type: TupleStrs, commands: TupleStrs, add_attr=()) -> AltNames:
    return join_product(('יחידת', 'מחלקת', *add_attr), unit_type, ('בפיקוד', 'פיקוד', None), commands)


def health_combo(command: str) -> AltNames:
    return unit_combo(('הרפואה', 'רפואה'), (command, 'ה' + command), ('חיל',))


def intelligence_combo(command: str) -> AltNames:
    return unit_combo(('המודיעין', 'מודיעין'), (command, 'ה' + command), (None,))


def engineering_combo(command: str, unit_num: str) -> AltNames:
    return join_product(('מפקדת הנדסה', 'הנדסה', 'הנדסה קרבית', 'מפקדת הנדסה קרבית', 'חה"ן'), ('פיקוד', 'בפיקוד', None),
                        (command, 'ה' + command), (unit_num, None))


def ammunition_combo(command: str, num: str) -> NameAndAlts:
    return f'יחידת החימוש המרחבית {num}', [f'יחידת חימוש מרחבית {num}', f'יחידת חימוש מרחבית {command}', f'אגד טכנולוגיה ואחזקה מרחבי {num}',
            f'אטנא"ם {num}', f'יחידת חימוש {num}', f'יחידת חימוש {command}']


def tikshuv_combo(gdud: str, alt_definite=False, num: str = '') -> NameAndAlts:
    gdud_un = None
    if alt_definite and gdud[0] == 'ה':
        gdud_un = gdud[1:]
    return f'גדוד תקשוב {gdud}{" " + num if num != "" else ""}', join_product(
        ('גדוד', 'גדוד תקשוב', 'גדוד התקשוב', None),
        (gdud, f'{gdud} {num}', *((gdud_un, f'{gdud_un} {num}') if gdud_un is not None else ())))


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
    'magal': Symbol('מערך מגל', ['מג"ל', 'מערך מג"ל'], 'magal.png'),
    'bahadim': Symbol('קריית ההדרכה על שם האלוף אריאל שרון',
                      ['קריית ההדרכה', 'עיר הבה"דים', 'קרית ההדרכה', 'קריית הדרכה', 'קרית הדרכה', 'מחנה שרון'],
                      'bahadim.png')
})


unit_tags = Group('תגי יחידה', [], '', {
    'general': Symbol('המטה הכללי', ['מטה כללי', 'מטכ"ל'], 'general.png'),
    'commands': Group('פיקודים', [], 'commands.png', {
        'north': Group('פיקוד הצפון', ['פיקוד צפון', 'פצ"ן'], 'north.png', {
            'gaash': Group('עוצבת געש (אוגדה 36)', ['עוצבת געש', 'אוגדה 36', 'עוצבת געש 36'], 'gaash.png', {
                'seon': Symbol('גדוד תקשוב שיאון', join_product(
                    ('גדוד תקשוב', 'גדוד', 'גדוד התקשוב', None), ('שיאון', 'שאון')), 'seon.png'),
                'logistics': Symbol('אגד לוגיסטי עוצבת געש', logistics_combo('געש'), 'logistics.png')
            }),
            'galil': Group('עוצבת הגליל (אוגדה 91)', ['עוצבת הגליל', 'אוגדה 91', 'עוצבת הגליל 91'], 'galil.png', {
                'baram': Symbol(*hatmar_combo('ברעם', '300'), 'baram.png'),
                'hiram': Symbol(*hatmar_combo('חירם', '769'), 'hiram.png'),
                'nofim': Symbol(*tikshuv_combo('נופים'), 'nofim.png'),
                'shahaf': Symbol('גדוד איסוף שחף 869', isuf_combo('שחף', '869'), 'shahaf.png'),
                'logistics': Symbol('אגד לוגיסטי עוצבת הגליל', logistics_combo(('הגליל', 'גליל')), 'logistics.png')
            }),
            'mapatz': Group('עוצבת המפץ (אוגדה 146)', ['עוצבת המפץ', 'אוגדה 146', 'אוגדה 319', 'עוצבת המפץ 146'], 'mapatz.png', {
                'logistics': Symbol('אגד לוגיסטי עוצבת המפץ 319', logistics_combo(('המפץ', 'מפץ'), '319'), 'logistics.png')
            }),
            'bashan': Group('אוגדת הבשן (אוגדה 210)', ['אוגדת הבשן', 'אוגדה 210', 'אוגדת הבשן 210'], 'bashan.png', {
                'golan': Symbol(*hatmar_combo('הגולן', '474'), 'golan.png'),
                'hermon': Symbol(*hatmar_combo('החרמון', '810'), 'hermon.png'),
                'snir': Symbol(*tikshuv_combo('שניר'), 'snir.png'),
                'ayit': Symbol('גדוד איסוף עיט 595', isuf_combo('עיט', '595'), 'ayit.png'),
                'logistics': Symbol('אגד לוגיסטי אוגדת הבשן 6366',
                                    logistics_combo(('הבשן', 'בשן'), '6366', ('אוגדת', 'אוגדה')), 'logistics.png')
            }),
            'health': Symbol('יחידת הרפואה בפיקוד הצפון', health_combo('צפון'), 'health.png'),
            'eliakim': Symbol('בסיס אימונים פיקודי אליקים',
                              ['בסיס אימונים פיקודי צפון', 'בא"פ אליקים', 'בסיס אימונים צפון',
                               'בסיס אימונים אליקים', 'בא"פ צפון', 'בסיס אליקים'], 'eliakim.png'),
            'ammunition': Symbol(*ammunition_combo('צפון', '651'), 'ammunition.png'),
            'intelligence': Symbol('מחלקת המודיעין בפיקוד הצפון', intelligence_combo('צפון'), 'intelligence.png'),
            'logistics5001': Symbol('אגד לוגיסטי מרחבי 5001', ['אלמ"ר 5001', 'אגד לוגיסטי 5001'], 'logistics5001.png'),
            'logistics5002': Symbol('אגד לוגיסטי מרחבי 5002', ['אלמ"ר 5002', 'אגד לוגיסטי 5002'], 'logistics5002.png'),
            'ayalim': Symbol(*tikshuv_combo('איילים'), 'ayalim.png'),
            'engineering': Symbol('מפקדת הנדסה קרבית בפיקוד הצפון 801', engineering_combo('צפון', '801'), 'engineering.png')
        }),
        'south': Group('פיקוד הדרום', ['פיקוד דרום', 'פד"ם'], 'south.png', {
            'gaza': Group('עוצבת שועלי האש (אוגדה 143)', ['אוגדת עזה', 'עוצבת שועלי האש', 'אוגדה 143', 'עוצבת שועלי האש 143', 'אוגדת עזה 143'], 'gaza.png', {
                'geffen': Symbol('חטיבת הגפן', ['חטיבת גפן', 'החטיבה הצפונית', 'החטיבה הצפונית ברצועת עזה', 'חטמ"ר צפונית', 'חטיבה צפונית'], 'geffen.png'),
                'katif': Symbol('חטיבת קטיף', ['החטיבה הדרומית', 'החטיבה הדרומית ברצועת עזה', 'חטמ"ר דרומית', 'חטיבה דרומית'], 'katif.png'),
                'bsor': Symbol(*tikshuv_combo('הבשור', alt_definite=True), 'bsor.png'),
                'nesher': Symbol('יחידת איסוף נשר 414', isuf_combo('נשר', '414', True), 'nesher.png')
            }),
            'edom': Group('עוצבת אדום (אוגדה מרחבית 80)', ['עוצבת אדום', 'אוגדה 80', 'אוגדה מרחבית 80', 'אוגמ"ר 80', 'עוצבת אדום 80'], 'edom.png', {
                'faran': Symbol('חטיבת פארן (חטיבה 512)', ['חטמ"ר פארן', 'חטיבה 512', 'חטיבה מרחבית פארן', 'חטיבת פארן'], 'faran.png'),
                'yoav': Symbol('חטיבת יואב (חטיבה 406)', ['חטמ"ר יואב', 'חטיבה 406', 'חטיבה מרחבית יואב', 'חטיבת יואב'], 'yoav.png'),
                'marom': Symbol(*tikshuv_combo('מרום'), 'marom.png'),
                'eitam': Symbol('גדוד איסוף איתם 727', isuf_combo('איתם', '727'), 'eitam.png'),
            }),
            'steel': Group('עוצבת הפלדה (אוגדה 162)', ['עוצבת הפלדה', 'אוגדה 162', 'עוצבת הפלדה 162', 'אוגדת הפלדה'], 'steel.png', {
                'afik': Symbol(*tikshuv_combo('אפיק'), 'afik.png'),
                'logistics': Symbol('אגד לוגיסטי עוצבת הפלדה 6162', logistics_combo(('הפלדה', 'פלדה'), '6162'), 'logistics.png')
            }),
            'sinai': Group('עוצבת סיני (אוגדה 252)', ['אוגדת סיני', 'עוצבת סיני', 'אוגדה 252', 'עוצבת סיני 252'], 'sinai.png', {
                'logistics': Symbol('אגד לוגיסטי עוצבת סיני', logistics_combo('סיני'), 'logistics.png')
            }),
            'health': Symbol('יחידת הרפואה בפיקוד הדרום', health_combo('דרום'), 'health.png'),
            'tzeelim': Symbol('בסיס אימונים פיקודי צאלים',
                              ['בסיס אימונים פיקודי דרום', 'בא"פ צאלים', 'בא"פ דרום', 'בסיס צאלים', 'בסיס אימונים דרום',
                               'בסיס אימונים צאלים'], 'tzeelim.png'),
            'ammunition': Symbol(*ammunition_combo('דרום', '653'), 'ammunition.png'),
            'intelligence': Symbol('מחלקת המודיעין בפיקוד הדרום', intelligence_combo('דרום'), 'intelligence.png'),
            'logistics': Symbol('אגד לוגיסטי מרחבי 5006',
                                ['אלמ"ר 5006', 'אגד לוגיסטי מרחבי דרום', 'אגד לוגיסטי 5006', 'אגד לוגיסטי דרום',
                                 'אגד 5006', 'אגד דרום'],
                                'logistics.png'),
            'raam': Symbol(*tikshuv_combo('רעם'), 'raam.png'),
            'engineering': Symbol('מפקדת הנדסה קרבית בפיקוד הדרום 803', engineering_combo('דרום', '803'), 'engineering.png')
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
                'ofek': Symbol(*tikshuv_combo('אופק'), 'ofek.png')
            }),
            'fire': Group('עוצבת האש (אוגדה 98)', ['עוצבת האש', 'אוגדה 98', 'עוצבת האש 98', 'אוגדת האש'], 'fire.png', {
                'lapid': Symbol(*tikshuv_combo('לפיד', num='492'), 'lapid.png'),
                'logistics': Symbol('יחידת שקנאי (אגד לוגיסטי עוצבת האש)',
                                    ['אגד לוגיסטי האש', 'יחידת שקנאי', 'אגד לוגיסטי עוצבת האש', 'אלו"ג שקנאי',
                                     'אלו"ג האש', 'אלו"ג עוצבת האש', 'אגד לוגיסטי שקנאי'], 'logistics.png')
            }),
            'bika': Symbol(*hatmar_combo(('הבקעה והעמקים', 'הבקעה'), '417'), 'bika.png'),
            'health': Symbol('יחידת הרפואה בפיקוד המרכז', health_combo('מרכז'), 'health.png'),
            'lachish': Symbol('בסיס אימונים פיקודי לכיש',
                              ['בסיס אימונים פיקודי מרכז', 'בא"פ לכיש', 'בא"פ מרכז', 'בסיס לכיש', 'בסיס אימונים מרכז',
                               'בסיס אימונים לכיש'], 'lachish.png'),
            'ammunition': Symbol(*ammunition_combo('מרכז', '650'), 'ammunition.png'),
            'intelligence': Symbol('מחלקת המודיעין בפיקוד המרכז', intelligence_combo('מרכז'), 'intelligence.png'),
            'logistics': Symbol('אגד לוגיסטי מרחבי 5004',
                                ['אלמ"ר 5004', 'אגד לוגיסטי מרחבי מרכז', 'אגד לוגיסטי 5004', 'אגד לוגיסטי מרכז',
                                 'אגד 5004', 'אגד מרכז'],
                                'logistics.png'),
            'segev': Symbol(*tikshuv_combo('שגב', num='372'), 'segev.png'),
            'engineering': Symbol('מפקדת הנדסה קרבית בפיקוד המרכז 802', ['י"פ חה"ן 802', *engineering_combo('מרכז', '802')], 'engineering.png')
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
            'tikshuv': Symbol('גדוד תקשוב פיקוד העורף 456', join_product(('גדוד תקשוב', 'גדוד התקשוב'),
                                                                         ('פיקוד העורף', 'פקע"ר', 'פיקוד העורף',
                                                                          'פקע"ר 456')), 'tikshuv.png')
        }),
        'depth': Group('מפקדת העומק', ['פיקוד העומק', 'מפע"ם'], 'depth.png', {
            'intelligence': Symbol('מחלקת המודיעין במפקדת העומק', intelligence_combo('עומק'), 'intelligence.png')
        })
    }, is_unit=False),
    'forces': Group('זרועות', [], 'forces.png', {
        'ground': Group('זרוע היבשה', [], 'ground.png', {
            'infantry': Group('חיל הרגלים', ['חיל רגלים', 'חי"ר'], 'infantry.png', {
                'golani': Symbol(*ground_combo('גולני', '1'), 'golani.png'),
                'paratroopers': Symbol(*ground_combo(('הצנחנים', 'צנחנים'), '35'), 'paratroopers.png'),
                'givati': Symbol(*ground_combo('גבעתי', '84'), 'givati.png'),
                'oz': Symbol(*ground_combo('עוז', '89'), 'oz.png'),
                'kfir': Symbol(*ground_combo('כפיר', '900'), 'kfir.png'),
                'nahal': Symbol(*ground_combo(('הנח"ל', 'נח"ל'), '933'), 'nahal.png'),
                'carmeli': Symbol(*ground_combo('כרמלי', '2'), 'carmeli.png'),
                'alexandroni:': Symbol(*ground_combo('אלכסנדרוני', '3'), 'kfir.png'),
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
                                   'יחידת סיור מדברי', 'גדוד סיור מדברי', 'יחס"ר בדואי', 'גדוד הסיור המדברי 585'],
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
            'armor': Group('חיל השריון', ['חיל שריון', 'חש"ן'], 'armor.png', {
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
            'engineering': Group('חיל ההנדסה הקרבית', ['חיל הנדסה קרבית', 'חיל הנדסה', 'חה"ן'], 'engineering.png', {

            }),
            'artillery': Group('חיל התותחנים', ['חיל תותחנים', 'חת"ם'], 'artillery.png', {

            }),
            'borders': Group('חיל הגנת הגבולות', ['חיל הגנת גבולות'], 'borders.png', {

            }),
            'logistics': __logistics_unit_tags,
            'bazak': Symbol('עוצבת הבזק (אוגדה 99)', ['אוגדה 99', 'עוצבת הבזק', 'אוגדת הבזק', 'עוצבת בזק', 'עוצבת הבזק 99'], 'bazak.png'),
            'marom': Symbol('מרכז הטסה והכשרות מיוחדות', ['מרו"ם', 'מרהו"ם', 'מרום פתרונות מבצעיים'], 'marom.png'),
            'bahad1': Symbol('בית הספר לקצינים של צה"ל על שם חיים לסקוב (בה"ד 1)',
                             ['בה"ד 1', 'בית הספר לקצינים', 'בית ספר לקצינים'], 'bahad1.png'),
            'mali': Symbol('המרכז הלאומי לאימונים ביבשה 500',
                           [*join_product(('מרכז לאומי לאימונים ביבשה', 'המרכז הלאומי לאימונים ביבשה',
                                           'המרכז לאימונים ביבשה', 'מרכז לאימונים ביבשה', 'מל"י'), ('500', None)),
                            'באלי"ש', 'בסיס אימון ליחידות שדה', 'מחנה שומרון', 'בסיס שומרון'], 'mali.png'),
            'attack': Symbol('חטיבת התקיפה הרב-זרועית', ['חטיבת התקיפה הרב זרועית', 'חטיבת תקיפה רב זרועית'], 'attack.png')
        }),
        'air': Group('זרוע האוויר והחלל', ['חיל האוויר', 'חיל האוויר והחלל', 'זרוע האוויר'], 'air.gif', {

        }),
        'navy': Group('זרוע הים', ['חיל הים'], 'navy.png', {

        })
    }, is_unit=False),
    'sections': Group('אגפים', [], 'sections.png', {
        'personnel': Group('אגף כוח האדם', ['אגף כוח אדם', 'אכ"א'], 'personnel.png', {
            'meitav': Symbol('מיטב', ['מיט"ב', 'בקו"ם', 'יחידת מיט"ב'], 'meitav.png'),
            'police': Group('חיל המשטרה הצבאית', ['משטרה צבאית', 'חיל משטרה צבאית', 'מ"ץ'], 'police.png', {

            }),
            'adjutant': Symbol('חיל משאבי האנוש', ['חיל משאבי אנוש', 'משא"ן'], 'adjutant.png'),
            'education': Symbol('חיל החינוך והנוער', ['חיל חינוך ונוער', 'חיל חינוך'], 'education.png'),
            'general': Group('החיל הכללי', ['חיל כללי', 'חכ"ל'], 'general.png', {
                'matpash': Symbol('מתאם פעולות הממשלה בשטחים',
                                  ['תיאום פעולות הממשלה בשטחים', 'מתפ"ש', 'המנהל האזרחי', 'מנהל אזרחי', 'מנהא"ז'],
                                  'matpash.png'),
                'complaints': Symbol('נציבות קבילות החיילים', ['נציב קבילות החיילים', 'נקח"ל'], 'complaints.png')
            })
        }),
        'operations': Group('אגף המבצעים', ['אגף מבצעים', 'אמ"ץ', 'אג"ם', 'אגף המטה הכללי', 'אגף מטה כללי'], 'operations.png', {
            'spokesperson': Symbol('דובר צה"ל', ['דו"ץ', 'מערך דובר צה"ל', 'מערך דו"ץ'], 'spokesperson.png')
        }),
        'intelligence': Symbol('אגף המודיעין', ['אמ"ן', 'אגף מודיעין'], 'intelligence.png'),
        'tikshuv': Group('אגף התקשוב וההגנה בסב"ר', ['אגף תקשוב', 'אגף התקשוב וההגנה בסייבר', 'את"ק'], 'tikshuv.png', {

        }),
        'planning': Symbol('אגף התכנון ובניין הכוח הרב-זרועי',
                           ['אג"ת', 'אגף התכנון', 'אגף בניין הכוח', 'אגף בניין כוח', 'אגף תכנון ובניין כוח',
                            'אגף תכנון ובניין כוח רב זרועי'], 'planning.png'),
        'strategy': Symbol('אגף אסטרטגיה ומעגל שלישי', ['אגף אסטרטגיה', 'אגף האסטרטגיה', 'אגא"ס'], 'strategy.png')
    }, is_unit=False),
    'courts': Symbol('יחידת בתי הדין הצבאיים',
                     ['בתי הדין הצבאיים', 'בית דין צבאי', 'יבד"ץ', 'יבד"ץ 205', 'יחידה 205', 'בתי דין צבאיים'],
                     'courts.png'),
    'advocate': Group('הפרקליטות הצבאית', ['פרקליטות צבאית', 'מפקדת הפרקליט הצבאי הראשי', 'מפצ"ר'], 'advocate.png', {
        'defense': Symbol('הסנגוריה הצבאית', ['הסנגוריה', 'סנגוריה צבאית'], 'defense.png')
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


def find_path(tag: Symbol, joiner='/') -> str:
    """Traverses the parent chain to create a string describing the path of the tag"""
    ret = ''
    parent: Group = tag.parent
    while parent is not None:
        ret = join_path(parent.folder, ret, joiner)
        parent = parent.parent
    return ret


def get_image_path(tag: Symbol, joiner='/') -> str:
    return find_path(tag, joiner) + tag.image_name


def get_folder_path(tag: Symbol, joiner='/') -> str:
    return find_path(tag, joiner) + tag.folder


def get_full_image_path(tag: Symbol) -> str:
    return url_for('static', filename='units/' + get_image_path(tag))


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


def get_all_tags_path(path: str, joiner='/') -> list[Symbol]:
    """Recursively returns all unit tags in a group, specified by path"""
    return get_all_unit_tags(find_unit_tag(path, joiner))


def is_parent_symbol(tag: Symbol) -> bool:
    """Is the tag a ParentSymbol, that is a group that is being displayed as a unit and not a group"""
    return isinstance(tag, ParentSymbol)
