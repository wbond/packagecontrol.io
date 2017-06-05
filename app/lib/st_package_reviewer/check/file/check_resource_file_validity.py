import sys
import plistlib
import xml.etree.ElementTree as ET
from xml.parsers.expat import ExpatError

from . import FileChecker
from ...lib import jsonc


class CheckJsoncFiles(FileChecker):

    def check(self):
        # All these files allow comments and trailing commas,
        # which is why we'll call them "jsonc" (JSON with Comments)
        jsonc_file_globs = {
            "**/*.sublime-build",
            "**/*.sublime-commands",
            "**/*.sublime-completions",
            "**/*.sublime-keymap",
            "**/*.sublime-macro",
            "**/*.sublime-menu",
            "**/*.sublime-mousemap",
            "**/*.sublime-settings",
            "**/*.sublime-theme",
        }

        for file_path in self.globs(*jsonc_file_globs):
            with self.file_context(file_path):
                with file_path.open(encoding='utf-8') as f:
                    try:
                        jsonc.loads(f.read())
                    except ValueError as e:
                        self.fail("Invalid JSON (with comments)", exception=e)


class CheckPlistFiles(FileChecker):

    def check(self):
        plist_file_globs = {
            "**/*.tmLanguage",
            "**/*.tmPreferences",
            "**/*.tmSnippet",
            "**/*.tmTheme",
        }

        for file_path in self.globs(*plist_file_globs):
            with self.file_context(file_path):
                with file_path.open('rb') as f:
                    try:
                        if sys.version_info < (3, 4):
                            plistlib.readPlist(f)
                        else:
                            plistlib.load(f)
                    except (ValueError, ExpatError) as e:
                        self.fail("Invalid Plist", exception=e)


class CheckXmlFiles(FileChecker):

    def check(self):
        for file_path in self.glob("**/*.sublime-snippet"):
            with self.file_context(file_path):
                try:
                    ET.parse(str(file_path))
                except ET.ParseError as e:
                    self.fail("Invalid XML", exception=e)
