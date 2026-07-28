from __future__ import annotations

import logging
from functools import lru_cache

from tree_sitter import Language, Node, Parser, Query, QueryCursor

import tree_sitter_go as tsgo
import tree_sitter_javascript as tsjavascript
import tree_sitter_python as tspython
import tree_sitter_typescript as tstypescript

from parsers.models import ParsedSymbol

logger = logging.getLogger(__name__)

PYTHON_QUERY = """
(function_definition
  name: (identifier) @name) @symbol
(class_definition
  name: (identifier) @name) @symbol
(import_statement) @import
(import_from_statement) @import
"""

JAVASCRIPT_QUERY = """
(function_declaration
  name: (identifier) @name) @symbol
(class_declaration
  name: (identifier) @name) @symbol
(method_definition
  name: (property_identifier) @name) @symbol
(lexical_declaration
  (variable_declarator
    name: (identifier) @name
    value: [(arrow_function) (function_expression)])) @symbol
(import_statement) @import
"""

TYPESCRIPT_QUERY = """
(function_declaration
  name: (identifier) @name) @symbol
(class_declaration
  name: [(type_identifier) (identifier)] @name) @symbol
(method_definition
  name: (property_identifier) @name) @symbol
(interface_declaration
  name: (type_identifier) @name) @symbol
(type_alias_declaration
  name: (type_identifier) @name) @symbol
(lexical_declaration
  (variable_declarator
    name: (identifier) @name
    value: [(arrow_function) (function_expression)])) @symbol
(import_statement) @import
"""

GO_QUERY = """
(function_declaration
  name: (identifier) @name) @symbol
(method_declaration
  name: (field_identifier) @name) @symbol
(type_declaration
  (type_spec
    name: (type_identifier) @name)) @symbol
(import_declaration) @import
"""

CLASS_NODE_TYPES = {
    "class_definition",
    "class_declaration",
    "interface_declaration",
}

METHOD_NODE_TYPES = {
    "method_definition",
    "method_declaration",
}

TYPE_NODE_TYPES = {
    "interface_declaration",
    "type_alias_declaration",
    "type_declaration",
}


@lru_cache(maxsize=1)
def _languages() -> dict[str, Language]:
    return {
        "python": Language(tspython.language()),
        "javascript": Language(tsjavascript.language()),
        "typescript": Language(tstypescript.language_typescript()),
        "tsx": Language(tstypescript.language_tsx()),
        "go": Language(tsgo.language()),
    }


@lru_cache(maxsize=1)
def _queries() -> dict[str, Query]:
    languages = _languages()
    return {
        "python": Query(languages["python"], PYTHON_QUERY),
        "javascript": Query(languages["javascript"], JAVASCRIPT_QUERY),
        "typescript": Query(languages["typescript"], TYPESCRIPT_QUERY),
        "tsx": Query(languages["tsx"], TYPESCRIPT_QUERY),
        "go": Query(languages["go"], GO_QUERY),
    }


def extract_symbols(source: bytes, language: str) -> list[ParsedSymbol]:
    languages = _languages()
    queries = _queries()
    if language not in languages:
        return []

    parser = Parser(languages[language])
    tree = parser.parse(source)
    cursor = QueryCursor(queries[language])
    symbols: list[ParsedSymbol] = []

    for _pattern_index, captures in cursor.matches(tree.root_node):
        try:
            symbol = _symbol_from_match(source, captures)
        except Exception:
            logger.debug("Skipping malformed symbol match in %s file", language, exc_info=True)
            continue
        if symbol is not None:
            symbols.append(symbol)

    return symbols


def _symbol_from_match(source: bytes, captures: dict[str, list[Node]]) -> ParsedSymbol | None:
    if "import" in captures:
        node = captures["import"][0]
        text = _node_text(source, node).strip()
        name = _import_name(text)
        return ParsedSymbol(
            name=name,
            kind="import",
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            signature=text[:500] if text else None,
        )

    if "symbol" not in captures or "name" not in captures:
        return None

    node = captures["symbol"][0]
    name_node = captures["name"][0]
    name = _node_text(source, name_node).strip()
    if not name:
        return None

    kind = _symbol_kind(node)
    parent_name = _parent_class_name(source, node) if kind == "method" else None
    signature = _first_line(source, node)

    return ParsedSymbol(
        name=name,
        kind=kind,
        start_line=node.start_point[0] + 1,
        end_line=node.end_point[0] + 1,
        signature=signature,
        parent_name=parent_name,
    )


def _symbol_kind(node: Node) -> str:
    if node.type in METHOD_NODE_TYPES:
        return "method"
    if node.type in TYPE_NODE_TYPES:
        return "type"
    if node.type in CLASS_NODE_TYPES:
        return "class"
    if node.type == "function_definition":
        # Nested Python functions inside a class are methods.
        if _parent_class_node(node) is not None:
            return "method"
        return "function"
    return "function"


def _parent_class_node(node: Node) -> Node | None:
    current = node.parent
    while current is not None:
        if current.type in CLASS_NODE_TYPES:
            return current
        current = current.parent
    return None


def _parent_class_name(source: bytes, node: Node) -> str | None:
    class_node = _parent_class_node(node)
    if class_node is None:
        # Go methods attach the receiver type instead of a class body parent.
        if node.type == "method_declaration":
            return _go_receiver_type(source, node)
        return None

    for child in class_node.children:
        if child.type in {"identifier", "type_identifier"}:
            return _node_text(source, child).strip() or None
    return None


def _go_receiver_type(source: bytes, node: Node) -> str | None:
    for child in node.children:
        if child.type != "parameter_list":
            continue
        for parameter in child.children:
            if parameter.type != "parameter_declaration":
                continue
            type_name = _first_type_identifier(source, parameter)
            if type_name:
                return type_name
    return None


def _first_type_identifier(source: bytes, node: Node) -> str | None:
    if node.type == "type_identifier":
        return _node_text(source, node).strip() or None
    for child in node.children:
        found = _first_type_identifier(source, child)
        if found:
            return found
    return None


def _import_name(text: str) -> str:
    compact = " ".join(text.split())
    if len(compact) <= 120:
        return compact
    return compact[:117] + "..."


def _first_line(source: bytes, node: Node) -> str | None:
    text = _node_text(source, node)
    if not text:
        return None
    first = text.splitlines()[0].strip()
    return first[:500] if first else None


def _node_text(source: bytes, node: Node) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")
