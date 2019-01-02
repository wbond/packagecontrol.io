from . import AstChecker
import re
import ast


# TODO: This only checks immediate base classes; need more traversing for deeper-derived base
# classes.
def _is_derived_from_command(node):
    interesting = ("TextCommand", "WindowCommand", "ApplicationCommand", "ExecCommand")
    for base in node.bases:
        if isinstance(base, ast.Attribute):
            # something of the form module_name.BaseClassName
            if isinstance(base.value, ast.Attribute):
                if base.value.value.id == "Default":
                    # Something derived from a class in Default... Must be ExecCommand
                    return True
            elif isinstance(base.value, ast.Name):
                if base.value.id == "sublime_plugin" and base.attr in interesting:
                    return True
        elif isinstance(base, ast.Name):
            # something of the form BaseClassName
            if base.id in interesting:
                return True
    return False


class CheckCommandNames(AstChecker):
    """Finds all sublime commands and does various checks on them."""

    def check(self):
        self.prefixes = set()
        super().check()
        if len(self.prefixes) > 1:
            self.warn("Found multiple command prefixes: {}."
                      " Consider using one single prefix"
                      " so as to not clutter the command namespace."
                      .format(", ".join(sorted(self.prefixes))))

    def visit_ClassDef(self, node):
        if not _is_derived_from_command(node):
            return

        with self.node_context(node):
            if not node.name.endswith("Command"):
                self.warn("Command class {!r} does not end with 'Command'".format(node.name))

            # Collect commands' prefixes
            match = re.findall(r"[A-Z][^A-Z]+", node.name)
            if match:
                self.prefixes.add(str(match[0]))

            # Check for PascalCase
            match = re.match(r"""(?x)
                             ^(
                                [A-Z][a-z0-9]+ [A-Z]
                              | [A-Z][a-z0-9]+ ([A-Z][a-z0-9]+)+ [A-Z]?
                             )$""",
                             node.name)
            if not match:
                self.warn("The command {!r} is not PascalCase".format(node.name))
