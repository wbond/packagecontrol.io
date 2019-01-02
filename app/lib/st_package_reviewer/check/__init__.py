import abc
from contextlib import contextmanager
import functools
import importlib
import logging
import os
import sys

from .. import debug_active
from .report import Report

__all__ = ('Report', 'Checker', 'find_all')

l = logging.getLogger(__name__)


class Checker(metaclass=abc.ABCMeta):

    def __init__(self):
        self.failures = []
        self.warnings = []
        self._checked = False
        self._context_stack = []

        # construct reporting functions
        self.fail = functools.partial(self._append_report, self.failures)
        self.warn = functools.partial(self._append_report, self.warnings)

    def _append_report(self, append_to, message, context=None, exception=None, exc_info=None):
        # TODO capture calling frame
        if context is None:
            context = tuple(self._context_stack)
        report = Report(message, context[:], exception, exc_info)
        append_to.append(report)

    def perform_check(self):
        try:
            self.check()
        except Exception as e:  # pragma: no cover
            msg = "Unhandled exception in 'check' routine"
            self.fail(msg, exception=e, exc_info=sys.exc_info())
            if debug_active():
                import pdb
                pdb.post_mortem()
            l.exception(msg)
        self._checked = True

    def result(self):
        """Return whether checks ran without issues (`True`) or there were failures (`False`)."""
        if not self._checked:
            raise RuntimeError("Check has not been perfomed yet")
        return not bool(self.failures)

    @abc.abstractmethod
    def check(self):
        pass

    @contextmanager
    def context(self, context_entry):
        self._context_stack.append(context_entry)
        yield
        assert self._context_stack.pop() == context_entry


@functools.lru_cache()
def find_all(path, package, base_class=Checker, exclude=()):
    """Find and collect all checker subclasses at the specified path.

    Class names that should be excluded from the result
    can be specified with the `exclude` parameter.
    """
    all_checkers = set()

    l.debug("Collecting checkers from sub-modules of '%s'...", package)
    for checker_file in path.glob("**/*.py"):
        rel_path = checker_file.relative_to(path)
        if rel_path.name == "__init__.py":
            l.debug("Skipping %s", rel_path)
            continue

        l.debug("Loading %s...", rel_path)
        relative_module_segments = str(rel_path.with_suffix('')).split(os.sep)
        module_path = "." + ".".join(relative_module_segments)
        module = importlib.import_module(module_path, package)

        for thing in module.__dict__.values():
            if not isinstance(thing, type):  # not a class
                continue

            # l.debug("checking %r", thing)
            if thing is not base_class and issubclass(thing, base_class):
                if thing.__name__ in exclude:
                    l.debug("Skipping %r because it was excluded", thing)
                    continue
                l.debug("Found %s subclass: %r", base_class.__name__, thing)
                all_checkers.add(thing)

    l.debug("Loaded %d checkers", len(all_checkers))

    return all_checkers
