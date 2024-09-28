import ast
import pathlib
import importlib
import os
from .abstract_handler import AbstractHandler

class HandlerFactory:
    _handlers = {}
    _handler_paths = {}

    @classmethod
    def discover_handlers(cls, root_path=None):
        # Clear existing handlers and handler paths
        cls._handlers.clear()
        cls._handler_paths.clear()

        # print(f"Discovering handlers...")

        # Discover handlers inside the package
        package_handlers_root = pathlib.Path(__file__).parent
        cls._search_for_handlers_in_path(package_handlers_root)

        # Check for custom handlers path in environment variable
        custom_handlers_path = os.getenv('custom_handlers_path')
        if custom_handlers_path:
            # print(f"Custom handlers path found: {custom_handlers_path}")
            custom_handlers_root = pathlib.Path(custom_handlers_path)
            cls._search_for_handlers_in_path(custom_handlers_root)
        # else:
        #     print("No custom handlers path set.")

        # print(f"Discovered handlers: {cls._handler_paths}")

    @classmethod
    def _search_for_handlers_in_path(cls, root_path):
        """
        Helper method to search for handlers in a given path.
        """
        if not root_path.exists():
            print(f"Path {root_path} does not exist.")
            return

        # print(f"Searching in path: {root_path}")
        for path in root_path.rglob('*.py'):
            if path.name == '__init__.py':
                continue

            # print(f"Checking file: {path}")
            # Read the content of the Python file
            with open(path, 'r') as file:
                node = ast.parse(file.read(), filename=path.name)

            # Traverse the AST to find class definitions that extend AbstractHandler
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.ClassDef):
                    for base in child.bases:
                        if (isinstance(base, ast.Attribute) and base.attr == 'AbstractHandler') or \
                           (isinstance(base, ast.Name) and base.id == 'AbstractHandler'):
                            handler_name = child.name
                            # Calculate the module path relative to the search path
                            module_path_parts = path.relative_to(root_path.parent).with_suffix('').parts
                            module_path = '.' + '.'.join(module_path_parts[1:])
                            cls._handler_paths[handler_name] = module_path
                            # print(f"Handler found: {handler_name} at {module_path}")
                            break

    @classmethod
    def get_handler(cls, handler_type):
        if not cls._handlers:
            cls.discover_handlers()

        # print(f"Requested handler type: {handler_type}")
        # print(f"Available handlers: {cls._handler_paths.keys()}")

        if handler_type not in cls._handlers:
            module_path = cls._handler_paths.get(handler_type)
            if module_path:
                try:
                    # print(f"Importing module {module_path} for handler {handler_type}")
                    # Dynamically import the module when requested
                    module = importlib.import_module(module_path, package='awschain.handlers')
                    handler_class = getattr(module, handler_type)
                    if issubclass(handler_class, AbstractHandler):
                        cls._handlers[handler_type] = handler_class
                        # print(f"Handler {handler_type} successfully imported and instantiated.")
                        return handler_class()
                    else:
                        raise ValueError(f"The class {handler_type} is not a subclass of AbstractHandler")
                except ModuleNotFoundError as e:
                    print(f"Module import error: {e}")
                    raise ImportError(f"Could not import module for handler: {handler_type}") from e
            else:
                raise ValueError(f"Handler not found for type: {handler_type}")
        return cls._handlers[handler_type]()