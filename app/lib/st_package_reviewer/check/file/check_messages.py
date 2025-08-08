import json
import re

from . import FileChecker

_semver_regex = re.compile(
    r"""
    ^\s*
    v?
    (?P<release>[0-9]+(?:\.[0-9]+){2})                    # semver release segment
    (?P<pre>                                              # pre-release
        [-_.]?
        (?P<pre_l>alpha|a|beta|b|prerelease|preview|pre|c|rc)
        [-_.]?
        (?P<pre_n>[0-9]+)?
    )?
    (?P<post>                                             # post release
        (?:-(?P<post_n1>[0-9]+))
        |
        (?:
            [-_.]?
            (?P<post_l>patch|post|rev|r)
            [-_.]?
            (?P<post_n2>[0-9]+)?
        )
    )?
    (?P<dev>                                              # dev release
        [-_.]?
        (?P<dev_l>development|develop|devel|dev)
        [-_.]?
        (?P<dev_n>[0-9]+)?
    )?
    \s*$
    """,
    re.VERBOSE,
)


class CheckMessages(FileChecker):

    prefixes = None

    def add_prefix(self, prefix):
        if self.prefixes is None:
            self.prefixes = {'v'}
        self.prefixes.add(prefix)

    def check(self):
        if self.prefixes is None:
            self.prefixes = {'v'}

        msg_path = self.sub_path("messages.json")
        folder_exists = self.sub_path("messages").is_dir()
        file_exists = msg_path.is_file()

        if not (folder_exists or file_exists):
            return
        elif folder_exists and not file_exists:
            self.fail("`messages` folder exists, but `messages.json` does not")
            return
        assert file_exists

        with self.file_context(msg_path):
            with msg_path.open() as f:
                try:
                    data = json.load(f)
                except ValueError as e:
                    self.fail("unable to load `messages.json`", exception=e)
                    return

            prefix_regex = '^(' + '|'.join(list(self.prefixes)) + ')'
            for key, rel_path in data.items():
                if key == "install":
                    pass
                elif _semver_regex.match(re.sub(prefix_regex, '', key)):
                    pass
                else:
                    self.fail("Key {!r} is not 'install' or a valid semantic version"
                              .format(key))

                messsage_path = self.sub_path(rel_path)
                if not messsage_path.is_file():
                    self.fail("File '{}', as specified by key {!r}, does not exist"
                              .format(rel_path, key))
