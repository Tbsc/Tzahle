import itertools
import re
from collections import deque


final_letters_pattern = re.compile('("[ץךףןם])')
final_trans = str.maketrans('ץךףןם', 'צכפנמ')


def alt_name_processor(alt_names: list[str]):
    for name in alt_names:
        # Find acronyms ending with a final letter and add alternative with a regular letter
        # Doesn't work in reverse
        finals_match = re.search(final_letters_pattern, name)
        if finals_match:
            # Perhaps it's a name with multiple acronyms
            for group in finals_match.groups():
                alt_names.append(name.replace(group, group.translate(final_trans), 1))
    return alt_names


class Symbol:
    folder: str

    def __init__(self, name: str, alt_names: list[str], image_name: str):
        self.parent = None
        self.name = name
        self.alt_names = alt_name_processor(alt_names)
        self.image_name = image_name
        self.is_unit = True
        self.is_root = False
        self.is_group = False

    def asdict(self):
        return {'name': self.name, 'alt_names': self.alt_names, 'image_name': self.image_name}


class Group(Symbol):
    def __init__(self, name: str, alt_names: list[str], image_name: str, children: dict[str, Symbol], is_unit=True,
                 is_root=False):
        super().__init__(name, alt_names, image_name)
        self.children = children
        self.is_unit = is_unit
        self.is_root = is_root
        self.symbols = [*([] if is_root or not is_unit else [ParentSymbol(self)]), *self.children.values()]
        for folder, child in children.items():
            child.folder = folder
            if child.parent is None and not is_root:
                child.parent = self
            if isinstance(child, Group) and isinstance(child.symbols[0], ParentSymbol):
                child.symbols[0].folder = child.folder
                child.symbols[0].parent = self
        self.is_group = True

    def __iter__(self):
        return iter(self.symbols)


class ParentSymbol(Symbol):
    """Holds a group as a symbol."""
    def __init__(self, group: Group):
        super().__init__(group.name, group.alt_names, group.image_name)
        self.group = group


def make_combos(types: tuple, name: str, prenum_types: tuple, num: str) -> tuple[str, list[str]]:
    ret = []
    for t in types:
        ret += [f'{t} {name}', f'{t} {name} {num}']
    for t in prenum_types:
        ret += [f'{t} {num}']
    hativa = 'חטיבה'
    return f'{types[0]} {name} ({hativa} {num})', ret


def hatmar_combo(name: str, num: str) -> tuple[str, list[str]]:
    return make_combos(('עוצבת', 'חטיבת', 'חטמ"ר'), name, ('חטיבה', 'חטמ"ר', 'עוצבה'), num)


def unit_combo(type: tuple, commands: tuple):
    return list(map(lambda x: " ".join(x),
                    itertools.product(('יחידת', 'מחלקת'), type, ('בפיקוד', 'פיקוד'), commands)))


def tikshuv_combo(gdud: str):
    start = 'גדוד'
    start_tik = 'גדוד תקשוב'
    start_hatik = 'גדוד התקשוב'
    return f'{start_tik} {gdud}', [gdud, f'{start} {gdud}', f'{start_hatik} {gdud}']


__logistics_unit_tags = Group('אגף הטכנולוגיה והלוגיסטיקה', ['אגף לוגיסטיקה', 'אגף טכנולוגיה ולוגיסטיקה', 'אט"ל'], 'logitech.png', {
    'technology': Group('חיל הטכנולוגיה והאחזקה', ['חיל החימוש', 'חיל טכנולוגיה ואחזקה', 'חיל הטנ"א', 'חיל טנ"א'], 'technology.jpg', {
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
    'commands': Group('פיקודים', [], '', {
        'north': Group('פיקוד הצפון', ['פיקוד צפון', 'פצ"ן'], 'north.gif', {
            'gaash': Group('עוצבת געש (אוגדה 36)', ['עוצבת געש', 'אוגדה 36', 'עוצבת געש 36'], 'gaash.png', {
                'seon': Symbol('גדוד תקשוב שיאון', ['שיאון', 'גדוד שיאון'], 'seon.png'),
                'logistics': Symbol('אגד לוגיסטי עוצבת געש', ['אגד לוגיסטי'], 'logistics.png')
            }),
            'galil': Group('עוצבת הגליל (אוגדה 91)', ['עוצבת הגליל', 'אוגדה 91', 'עוצבת הגליל 91'], 'galil.png', {
                'baram': Symbol(*hatmar_combo('ברעם', '300'), 'baram.png'),
                'hiram': Symbol(*hatmar_combo('חירם', '769'), 'hiram.png'),
                'nofim': Symbol(*tikshuv_combo('נופים'), 'nofim.png'),
                'shahaf': Symbol('גדוד איסוף שחף 869',
                                 ['גדוד שחף', 'גדוד 869', 'גדוד איסוף קרבי 869', 'גדוד איסוף קרבי שחף'], 'shahaf.png'),
                'logistics': Symbol('אגד תחזוקה עוצבת הגליל', ['אגד תחזוקה', 'אגד התחזוקה'], 'logistics.png')
            }),
            'mapatz': Group('עוצבת המפץ (אוגדה 146)', ['עוצבת המפץ', 'אוגדה 146', 'אוגדה 319', 'עוצבת המפץ 146'],
                            'mapatz.png', {
                'logistics': Symbol('אגד תחזוקה עוצבת המפץ', ['אגד תחזוקה', 'אגד התחזוקה'], 'logistics.png')
            }),
            'bashan': Group('אוגדת הבשן (אוגדה 210)', ['אוגדת הבשן', 'אוגדה 210', 'אוגדת הבשן 210'], 'bashan.png', {
                'golan': Symbol(*hatmar_combo('הגולן', '474'), 'golan.png'),
                'snir': Symbol(*tikshuv_combo('שניר'), 'snir.png'),
                'ayit': Symbol('גדוד איסוף עיט 595',
                               ['גדוד עיט', 'גדוד 595', 'גדוד איסוף קרבי 595', 'גדוד איסוף קרבי עיט'], 'ayit.png'),
                'logistics': Symbol('אגד תחזוקה אוגדת הבשן', ['אגד תחזוקה', 'אגד התחזוקה'], 'logistics.png')
            }),
            'health': Symbol('יחידת הרפואה בפיקוד הצפון',
                             unit_combo(('רפואה', 'הרפואה'), ('צפון', 'הצפון')), 'health.png'),
            'eliakim': Symbol('בא"פ אליקים',
                              ['בסיס אימונים פיקודי צפון', 'בסיס אימונים פיקודי אליקים', 'בסיס אימונים צפון',
                               'בסיס אימונים אליקים'], 'eliakim.png'),
            'ammunition': Symbol('יחידת החימוש המרחבית 651',
                                 ['יחידת חימוש מרחבית 651', 'יחידת חימוש מרחבית צפון', 'אגד טכנולוגיה ואחזקה מרחבי 651',
                                  'אטנא"ם 651'], 'ammunition.png'),
            'intelligence': Symbol('מחלקת המודיעין בפיקוד הצפון',
                                   unit_combo(('המודיעין', 'מודיעין'), ('צפון', 'הצפון')), 'intelligence.png'),
            'logistics5001': Symbol('אגד לוגיסטי מרחבי 5001', ['אלמ"ר 5001'], 'logistics5001.png'),
            'logistics5002': Symbol('אגד לוגיסטי מרחבי 5002', ['אלמ"ר 5002'], 'logistics5002.png'),
            'ayalim': Symbol(*tikshuv_combo('איילים'), 'ayalim.png'),
            'engineering': Symbol('גדוד ציוד מכני הנדסי פיקוד צפון 7064',
                                  ['גדוד צמ"ה צפון', 'צמ"ה צפון', 'גדוד 7064', 'צמ"ה', 'ציוד מכני הנדסי',
                                   'גדוד ציוד מכני הנדסי', 'גדוד צמ"ה'], 'engineering.png')
        }),
        'south': Group('פיקוד הדרום', ['פיקוד דרום', 'פד"ם'], 'south.png', {
            'gaza': Group('עוצבת שועלי האש (אוגדה 143)', ['אוגדת עזה', 'עוצבת שועלי האש', 'אוגדה 143', 'עוצבת שועלי האש 143', 'אוגדת עזה 143'], 'gaza.png', {
                'geffen': Symbol('חטיבת הגפן', ['חטיבת גפן', 'החטיבה הצפונית', 'החטיבה הצפונית ברצועת עזה'], 'geffen.png'),
                'katif': Symbol('חטיבת קטיף', [''], 'katif.png')
            })
        }),
        'center': Group('פיקוד המרכז', ['פיקוד מרכז', 'פקמ"ז'], 'center.gif', {
            'ayosh': Group('אוגדת איו"ש (אוגדה 877)', ['אוגדת איו"ש', 'אוגדה 877', 'אוגדת יו"ש', 'אוגדת יהודה ושומרון',
                                               'אוגדת אזור יהודה ושומרון'], 'ayosh.png', {

            })
        }),
        'oref': Symbol('פיקוד העורף', ['פקע"ר'], 'oref.gif'),
        'depth': Symbol('מפקדת העומק', ['פיקוד העומק', 'מפע"ם'], 'depth.gif')
    }, is_unit=False),
    'forces': Group('זרועות', [], '', {
        'ground': Group('זרוע היבשה', [], 'ground.png', {
            'infantry': Group('חיל הרגלים', ['חיל רגלים', 'חי"ר'], '', {

            }),
            'armor': Group('חיל השריון', ['חיל שריון', 'חש"ן'], '', {

            }),
            'engineering': Group('חיל ההנדסה הקרבית', ['חיל הנדסה קרבית', 'חיל הנדסה', 'חה"ן'], '', {

            }),
            'artillery': Group('חיל התותחנים', ['חיל תותחנים', 'חת"ם'], '', {

            }),
            'borders': Group('חיל הגנת הגבולות', ['חיל הגנת גבולות'], '', {

            }),
            'logistics': __logistics_unit_tags,
            'bazak': Symbol('עוצבת הבזק (אוגדה 99)', ['אוגדה 99', 'עוצבת הבזק', 'אוגדת הבזק', 'עוצבת בזק', 'עוצבת הבזק 99'], 'bazak.png'),
            'marom': Symbol('מרכז הטסה והכשרות מיוחדות', ['מרו"ם', 'מרהו"ם', 'מרום פתרונות מבצעיים'], 'marom.png')
        }),
        'air': Group('זרוע האוויר והחלל', ['חיל האוויר', 'חיל האוויר והחלל', 'זרוע האוויר'], 'air.gif', {

        }),
        'navy': Group('זרוע הים', ['חיל הים'], 'navy.png', {

        })
    }, is_unit=False),
    'sections': Group('אגפים', [], '', {
        'intelligence': Symbol('אגף המודיעין', ['אמ"ן', 'אגף מודיעין'], 'intelligence.png'),
        'planning': Symbol('אגף התכנון ובניין הכוח הרב-זרועי',
                           ['אג"ת', 'אגף התכנון', 'אגף בניין הכוח', 'אגף בניין כוח', 'אגף תכנון ובניין כוח',
                            'אגף תכנון ובניין כוח רב זרועי'], ''),
        'tikshuv': Group('אגף התקשוב וההגנה בסב"ר', ['אגף תקשוב', 'אגף התקשוב וההגנה בסייבר', 'את"ק'], '', {

        }),
        'personnel': Group('אגף כוח האדם', ['אגף כוח אדם', 'אכ"א'], '', {
            'meitav': Symbol('יחידת מיטב', ['מיטב', 'בקו"ם'], 'meitav.png'),
            'police': Group('חיל המשטרה הצבאית', ['משטרה צבאית', 'חיל משטרה צבאית', 'מ"ץ'], '', {

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
        'operations': Group('אגף המבצעים', ['אגף מבצעים', 'אמ"ץ'], '', {
            'spokesperson': Symbol('דובר צה"ל', ['דו"ץ'], 'spokesperson.jpg')
        }),
        'strategy': Group('אגף אסטרטגיה ומעגל שלישי', ['אגף אסטרטגיה', 'אגף האסטרטגיה', 'אגא"ס'], '', {

        })
    }, is_unit=False),
    'courts': Symbol('יחידת בתי הדין הצבאיים',
                     ['בתי הדין הצבאיים', 'בית דין צבאי', 'יבד"ץ', 'יבד"ץ 205', 'יחידה 205', 'בתי דין צבאיים'],
                     'courts.png'),
    'advocate': Group('הפרקליטות הצבאית', ['פרקליטות צבאית', 'מפקדת הפרקליט הצבאי הראשי', 'מפצ"ר'], 'advocate.png', {
        'defense': Symbol('הסנגוריה הצבאית', ['הסנגוריה', 'סנגוריה צבאית'], 'defense.png')
    })
}, is_unit=False, is_root=True)


def find_unit_tag(path: str, joiner='/'):
    """Get the wanted unit tag, following the given path. The path must be slash-separated. Returns the symbol
    object or None if not found. Can return both groups and symbols, using the same syntax."""
    paths = path.split(joiner)
    ret = unit_tags
    try:
        for folder in paths:
            if folder != '':
                ret = ret.children[folder]
    except KeyError:
        return None
    return ret


def join_path(base, folder, joiner='/'):
    return base + joiner + folder


def find_path(tag: Symbol, joiner='/') -> str:
    """Traverses the parent tree to create a string describing the path of the tag"""
    ret = ''
    parent: Group = tag.parent
    while parent is not None:
        ret = join_path(parent.folder, ret, joiner)
        parent = parent.parent
    return ret


def get_image_path(tag: Symbol, joiner='/'):
    return find_path(tag, joiner) + tag.image_name


def get_folder_path(tag: Symbol, joiner='/'):
    return find_path(tag, joiner) + tag.folder


def get_full_image_path(tag: Symbol, joiner='/'):
    return f'static{joiner}units{joiner}' + get_image_path(tag)


def get_all_unit_tags(group=unit_tags) -> list[Symbol]:
    """Returns all tags under the given group. Includes both symbols and groups marked as a unit."""
    ret = deque()
    for child in reversed(group.children.values()):
        if isinstance(child, Group):
            ret.extendleft(reversed(get_all_unit_tags(child)))
        if child.is_unit and not child.is_root:
            ret.appendleft(child)
    return list(ret)


def get_all_tags_path(path: str, joiner='/') -> list[Symbol]:
    return get_all_unit_tags(find_unit_tag(path, joiner))


def handle_request(query, recurse):
    if recurse:
        return get_all_tags_path(query, '-')
    else:
        return find_unit_tag(query, '-')


def is_parent_symbol(tag):
    return isinstance(tag, ParentSymbol)
