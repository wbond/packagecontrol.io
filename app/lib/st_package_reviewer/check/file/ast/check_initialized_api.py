import ast
import logging

from . import AstChecker

l = logging.getLogger(__name__)


def _is_derived_from_listener(node):
    interesting = ("EventListener",)
    for base in node.bases:
        if isinstance(base, ast.Attribute):
            # something of the form module_name.BaseClassName
            if isinstance(base.value, ast.Name):
                if base.value.id == "sublime_plugin" and base.attr in interesting:
                    return True
        elif isinstance(base, ast.Name):
            # something of the form BaseClassName
            if base.id in interesting:
                return True
    return False


class CheckInitializedApiUsage(AstChecker):

    """Check for function calls of the sublime module in unsafe places.

    Notably, these are:

    - the global module scope
    - __init__ methods of event listeners
    - functions that are called from the module scope
    """

    def __init__(self, base_path):
        super().__init__(base_path)

    def visit_Module(self, node):
        self._module_calls = set()
        self._module_functions = {}

        self.generic_visit(node)

        l.debug("module calls: %s", self._module_calls)
        l.debug("module functions: %s", self._module_functions)
        # Visit function bodies that are called from the module scope
        relevant_functions = set(self._module_functions.keys()) & self._module_calls
        for fname in relevant_functions:
            for stmt in self._module_functions[fname].body:
                self.generic_visit(stmt)

    def visit_ClassDef(self, node):
        # ClassDef(identifier name, expr* bases, keyword* keywords, stmt* body,
        #          expr* decorator_list)
        # Visit __init__ methods of listener classes, but not any other
        if _is_derived_from_listener(node):
            l.debug("found EventListener subclass %s", node.name)
            for stmt in node.body:
                if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                    l.debug("found '__init__' method within EventListener subclass %r", node.name)
                    self.generic_visit(stmt)

    def visit_FunctionDef(self, node):
        # Don't recursively visit function definitions,
        # but store them in a dict of global functions.
        self._module_functions[node.name] = node

    def visit_Call(self, node):
        # Call(expr func, expr* args, keyword* keywords)
        # Attribute(expr value, identifier attr, expr_context ctx)
        # Name(identifier id, expr_context ctx)
        #
        # This handler will only be called for calls that could be relevant.
        try:
            id_ = node.func.id
        except AttributeError:
            pass
        else:
            self._module_calls.add(id_)
            return

        # All 'remaining' calls of `sublime` attributes that are not safe
        # must be in places where the API may not have been initialized.
        try:
            attr = node.func.attr
            id_ = node.func.value.id
        except AttributeError as e:
            return
        else:
            if id_ == "sublime" and attr not in ("platform", "arch", "version", "channel"):
                with self.node_context(node):
                    self.fail("Calling unsafe method {!r} of sublime module"
                              " when API may not have been initialized".format(attr))
