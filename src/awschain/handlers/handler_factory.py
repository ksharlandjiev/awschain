import ast
import pathlib
import importlib.util
import os
from .abstract_handler import AbstractHandler

class HandlerFactory:
    _handlers = {}
    _handler_paths = {}
    _custom_handler_files = {}  # To store file paths of custom handlers

    @classmethod
    def _debug(cls, message):
        """
        Helper method to print debugging information if DEBUG environment variable is set.
        """
        if os.getenv('DEBUG', 'false').lower() == 'true':
            print(message)

    @classmethod
    def discover_handlers(cls, root_path=None):
        # Clear existing handlers, handler paths, and custom handler file paths
        cls._handlers.clear()
        cls._handler_paths.clear()
        cls._custom_handler_files.clear()

        # Discover handlers inside the package
        package_handlers_root = pathlib.Path(__file__).parent
        cls._search_for_handlers_in_path(package_handlers_root)

        # Check for custom handlers path in environment variable
        custom_handlers_path = os.getenv('custom_handlers_path')
        if custom_handlers_path:
            cls._debug(f"Searching for custom handlers in: {custom_handlers_path}")
            custom_handlers_root = pathlib.Path(custom_handlers_path)
            cls._search_for_handlers_in_path(custom_handlers_root, custom=True)

    @classmethod
    def _search_for_handlers_in_path(cls, root_path, custom=False):
        """
        Helper method to search for handlers in a given path.
        If custom is True, handlers are considered as external/custom.
        """
        if not root_path.exists():
            cls._debug(f"Path {root_path} does not exist.")
            return

        for path in root_path.rglob('*.py'):
            if path.name == '__init__.py':
                continue

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
                            if custom:
                                # Store the actual file path for custom handlers
                                cls._custom_handler_files[handler_name] = path
                                cls._debug(f"Custom handler found: {handler_name} at {path}")
                            else:
                                # Calculate the module path relative to the package's handlers folder
                                module_path_parts = path.relative_to(root_path.parent).with_suffix('').parts
                                module_path = '.' + '.'.join(module_path_parts[1:])
                                cls._handler_paths[handler_name] = module_path
                                cls._debug(f"Handler found: {handler_name} at {module_path} (custom={custom})")
                            break

    @classmethod
    def get_handler(cls, handler_type):
        if not cls._handlers:
            cls.discover_handlers()

        if handler_type not in cls._handlers:
            # First try to find the handler in the custom handler files
            if handler_type in cls._custom_handler_files:
                file_path = cls._custom_handler_files[handler_type]
                cls._debug(f"Loading custom handler from: {file_path}")
                try:
                    # Load custom handler from file path
                    spec = importlib.util.spec_from_file_location(handler_type, file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    handler_class = getattr(module, handler_type)
                    if issubclass(handler_class, AbstractHandler):
                        cls._handlers[handler_type] = handler_class
                        return handler_class()
                    else:
                        raise ValueError(f"The class {handler_type} is not a subclass of AbstractHandler")
                except Exception as e:
                    cls._debug(f"Error loading custom handler {handler_type} from {file_path}: {e}")
                    raise ImportError(f"Could not import custom handler: {handler_type}") from e

            # Otherwise, try to find the handler in the package
            module_path = cls._handler_paths.get(handler_type)
            if module_path:
                try:
                    cls._debug(f"Importing package handler {handler_type} from {module_path}")
                    # Import as a package handler
                    module = importlib.import_module(module_path, package='awschain.handlers')
                    handler_class = getattr(module, handler_type)
                    if issubclass(handler_class, AbstractHandler):
                        cls._handlers[handler_type] = handler_class
                        return handler_class()
                    else:
                        raise ValueError(f"The class {handler_type} is not a subclass of AbstractHandler")
                except ModuleNotFoundError as e:
                    cls._debug(f"Module import error: {e}")
                    raise ImportError(f"Could not import package handler: {handler_type}") from e

            raise ValueError(f"Handler not found for type: {handler_type}")

        return cls._handlers[handler_type]()