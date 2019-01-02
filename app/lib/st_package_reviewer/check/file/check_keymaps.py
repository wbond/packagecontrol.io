import json
import logging
import re
from pathlib import Path

from ...lib import jsonc
from . import FileChecker

from ... import __file__ as base_init_path


DATA_PATH = Path(base_init_path).parent / "data"

PLATFORMS = ("Linux", "OSX", "Windows")
PLATFORM_FILENAMES = tuple("Default ({}).sublime-keymap".format(plat)
                           for plat in PLATFORMS)
VALID_FILENAMES = PLATFORM_FILENAMES + ("Default.sublime-keymap",)

l = logging.getLogger(__name__)


class CheckKeymaps(FileChecker):

    def check(self):
        keymap_files = self.glob("**/*.sublime-keymap")

        # ignore unused files
        keymap_files = {path for path in keymap_files
                        if path.name in VALID_FILENAMES}

        if not keymap_files:
            return

        # cache default keymap files
        def_maps = KeyMapping.default_maps()

        # check for conflicts with default package
        for path in keymap_files:
            platforms = PLATFORMS
            m = re.search(r"\((.*?)\)", path.name)
            if m:
                platforms = {m.group(1)}

            k_map = KeyMapping(path)

            with self.file_context(path):
                self._verify_keymap(k_map)

                conflicts = []
                for plat in platforms:
                    local_conflicts = k_map.find_conflicts(def_maps[plat])
                    l.debug("#conflicts for %s on platform %s: %d",
                            self.rel_path(k_map.path), plat, len(local_conflicts))
                    # prevent duplicates while maintaining order
                    for conflict in local_conflicts:
                        if conflict not in conflicts:
                            conflicts.append(conflict)

                    # import pdb; pdb.set_trace()
                for conflict in conflicts:
                    if conflict.get('context'):
                        self.warn("The binding {} is also defined in default bindings "
                                  "but is masked with a 'context'".format(conflict['keys']))
                    else:
                        self.fail("The binding {} unconditionally overrides a default binding"
                                  .format(conflict['keys']))

    def _verify_keymap(self, k_map):
        allowed_keys = {'keys', 'command', 'args', 'context'}
        required_keys = {'keys', 'command'}

        idx_to_del = set()
        for i, binding in enumerate(k_map.data):
            with self.context("Binding: {}".format(json.dumps(binding, sort_keys=True))):
                keys = set(binding.keys())
                missing_keys = required_keys - keys
                if missing_keys:
                    self.fail("Binding is missing the keys {}".format(missing_keys))

                    # It would be useless to continue analyzing this entry,
                    # so schedule it for deletion
                    idx_to_del.add(i)

                supplementary_keys = keys - allowed_keys
                if supplementary_keys:
                    self.warn("Binding defines supplementary keys {}".format(supplementary_keys))

                if 'keys' in binding:
                    try:
                        norm_chords = k_map._verify_and_normalize_chords(binding['keys'])
                    except KeyMappingError as e:
                        self.fail(e.args[0])
                        idx_to_del.add(i)
                    else:
                        binding['keys'] = norm_chords

                # TODO verify 'context'

        # do actual deletion (in reverse)
        for i in sorted(idx_to_del, reverse=True):
            del k_map.data[i]


class KeyMappingError(ValueError):
    pass


class KeyMapping:

    _def_maps = None

    @classmethod
    def default_maps(cls):
        # type: Dict[str, KeyMapping]
        if not cls._def_maps:
            cls._def_maps = {plat: cls(DATA_PATH / fname)
                             for plat, fname in zip(PLATFORMS, PLATFORM_FILENAMES)}
            # Verify and normalize default maps
            for k_map in cls._def_maps.values():
                k_map._verify()

        return cls._def_maps

    def __init__(self, path):
        self.path = path
        self.data = self._load(path)

    def find_conflicts(self, other):
        # TODO two-part bindings conflict with single bindings and vice versa
        return [binding for binding in self.data
                if other.get_for_chords(binding['keys'])]

    def get_for_chords(self, chords):
        return [binding for binding in self.data
                if binding['keys'] == chords]

    @classmethod
    def _load(cls, path):
        with path.open(encoding='utf-8') as f:
            return jsonc.loads(f.read())

    def _verify(self):
        for binding in self.data:
            binding['keys'] = self._verify_and_normalize_chords(binding['keys'])

    @classmethod
    def _verify_and_normalize_chords(cls, chords):
        modifiers = ("ctrl", "super", "alt", "shift", "primary")

        if not chords or not isinstance(chords, list):
            raise KeyMappingError("'keys' key is empty or not a list")
        norm_chords = []
        for key_chord in chords:
            if len(key_chord) == 1:
                # Any single character key is valid (representing a symbol)
                norm_chords.append(key_chord)
                continue

            chord_parts = []
            while True:
                key, plus, key_chord = key_chord.partition("+")
                if not key_chord:  # we're at the end
                    if plus:  # a chord with '+' as key
                        key = plus
                    if not cls._key_is_valid(key):
                        raise KeyMappingError("Invalid key '{}'".format(key))
                    chord_parts.sort(key=modifiers.index)
                    chord_parts.append(key)
                    break

                if key == "option":
                    key = "alt"
                elif key == "command":
                    key = "super"
                # TODO "primary"
                if key not in modifiers:
                    raise KeyMappingError("Invalid modifier key '{}'".format(key))

                chord_parts.append(key)

            norm_chords.append("+".join(chord_parts))

        if norm_chords != chords:
            l.debug("normalized chords {!r} to {!r}".format(chords, norm_chords))
        return norm_chords

    @classmethod
    def _key_is_valid(cls, key):
        if len(key) == 1:
            # should include all typable symbols and more
            return not key.isupper()  # not equivalent to `key.islower()`
        elif key in cls._known_keys:
            # multi-character key aliases
            return True
        else:
            return False

    _known_keys = set()
    # _known_keys |= {chr(c) for c in range(ord('a'), ord('z') + 1)}
    _known_keys |= {"f{}".format(i) for i in range(1, 21)}
    _known_keys |= {"keypad{}".format(i) for i in range(10)}
    _known_keys |= {"up", "down", "left", "right",
                    "insert", "delete", "home", "end", "pageup", "pagedown",
                    "backspace", "enter", "tab",
                    "escape", "pause", "break",
                    "space", "context_menu",
                    "keypad_period", "keypad_divide", "keypad_multiply", "keypad_minus",
                    "keypad_plus", "keypad_enter",
                    "browser_back", "browser_forward", "browser_refresh", "browser_stop",
                    "browser_search", "browser_favorites", "browser_home",
                    "clear", "sysreq",
                    # these have single-character equivalents
                    # TODO resolve these aliases
                    "plus", "minus", "equals", "forward_slash", "backquote",
                    # Note: this list is incomplete and sourced from the default bindings
                    }
