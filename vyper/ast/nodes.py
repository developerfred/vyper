import ast as python_ast
import sys
import typing

from vyper.exceptions import (
    SyntaxException,
)
from vyper.settings import (
    VYPER_ERROR_CONTEXT_LINES,
    VYPER_ERROR_LINE_NUMBERS,
)
from vyper.utils import (
    annotate_source_code,
)

BASE_NODE_ATTRIBUTES = (
    'node_id',
    'source_code',
    'col_offset',
    'lineno',
    'end_col_offset',
    'end_lineno',
    'src',
    'ast_type',
)
DICT_AST_SKIPLIST = ('source_code', )


def get_node(node):
    if not isinstance(node, dict):
        node = node.__dict__

    vy_class = getattr(sys.modules[__name__], node['ast_type'], None)

    if vy_class is None:
        raise SyntaxException(
            f"Invalid syntax (unsupported '{node['ast_type']}'' Python AST node).", node
        )

    return vy_class(**node)


def _to_node(value):
    if isinstance(value, (dict, python_ast.AST)):
        return get_node(value)
    return value


def _to_dict(value):
    if isinstance(value, VyperNode):
        return value.to_dict()
    return value


class VyperNode:

    __slots__ = BASE_NODE_ATTRIBUTES
    _only_empty_fields: typing.Tuple = ()
    _translated_fields: typing.Dict = {}

    def __init__(self, **kwargs):

        for field_name, value in kwargs.items():
            if field_name in self._translated_fields:
                field_name = self._translated_fields[field_name]

            if field_name in self.get_slots():
                if isinstance(value, list):
                    value = [_to_node(i) for i in value]
                else:
                    value = _to_node(value)
                setattr(self, field_name, value)

            elif value and field_name in self._only_empty_fields:
                raise SyntaxException(
                    f'Unsupported non-empty value (valid in Python, but invalid in Vyper) \n'
                    f' field_name: {field_name}, class: {type(self)} value: {value}'
                )

    @classmethod
    def get_slots(cls):
        return set(x for i in cls.__mro__ for x in getattr(i, '__slots__', []))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        for field_name in (i for i in self.get_slots() if i not in BASE_NODE_ATTRIBUTES):
            if getattr(self, field_name, None) != getattr(other, field_name, None):
                return False
        return True

    def __repr__(self):
        cls = type(self)
        class_repr = f'{cls.__module__}.{cls.__qualname__}'

        source_annotation = annotate_source_code(
            self.source_code,
            self.lineno,
            self.col_offset,
            context_lines=VYPER_ERROR_CONTEXT_LINES,
            line_numbers=VYPER_ERROR_LINE_NUMBERS,
        )

        return f'{class_repr}:\n{source_annotation}'

    def to_dict(self):
        ast_dict = {}
        for key in [i for i in self.get_slots() if i not in DICT_AST_SKIPLIST]:
            value = getattr(self, key, None)
            if isinstance(value, list):
                ast_dict[key] = [_to_dict(i) for i in value]
            else:
                ast_dict[key] = _to_dict(value)
        return ast_dict


class Module(VyperNode):
    __slots__ = ('body', )


class Name(VyperNode):
    __slots__ = ('id', )


class Subscript(VyperNode):
    __slots__ = ('slice', 'value')


class Index(VyperNode):
    __slots__ = ('value', )


class arg(VyperNode):
    __slots__ = ('arg', 'annotation')


class Tuple(VyperNode):
    __slots__ = ('elts', )


class FunctionDef(VyperNode):
    __slots__ = ('args', 'body', 'returns', 'name', 'decorator_list', 'pos')


class arguments(VyperNode):
    __slots__ = ('args', 'defaults', 'default')
    _only_empty_fields = ('vararg', 'kwonlyargs', 'kwarg', 'kw_defaults')


class Import(VyperNode):
    __slots__ = ('names', )


class Call(VyperNode):
    __slots__ = ('func', 'args', 'keywords', 'keyword')


class keyword(VyperNode):
    __slots__ = ('arg', 'value')


class Str(VyperNode):
    __slots__ = ('s', )
    _translated_fields = {'value': 's'}


class Compare(VyperNode):
    __slots__ = ('comparators', 'ops', 'left', 'right')


class Num(VyperNode):
    __slots__ = ('n', )
    _translated_fields = {'value': 'n'}


class NameConstant(VyperNode):
    __slots__ = ('value', )


class Attribute(VyperNode):
    __slots__ = ('attr', 'value',)


class Op(VyperNode):
    __slots__ = ('op', 'left', 'right')


class BoolOp(Op):
    __slots__ = ('values', )


class BinOp(Op):
    __slots__ = ()


class UnaryOp(Op):
    __slots__ = ('operand', )


class List(VyperNode):
    __slots__ = ('elts', )


class Dict(VyperNode):
    __slots__ = ('keys', 'values')


class Bytes(VyperNode):
    __slots__ = ('s', )
    _translated_fields = {'value': 's'}


class Add(VyperNode):
    __slots__ = ()


class Sub(VyperNode):
    __slots__ = ()


class Mult(VyperNode):
    __slots__ = ()


class Div(VyperNode):
    __slots__ = ()


class Mod(VyperNode):
    __slots__ = ()


class Pow(VyperNode):
    __slots__ = ()


class In(VyperNode):
    __slots__ = ()


class Gt(VyperNode):
    __slots__ = ()


class GtE(VyperNode):
    __slots__ = ()


class LtE(VyperNode):
    __slots__ = ()


class Lt(VyperNode):
    __slots__ = ()


class Eq(VyperNode):
    __slots__ = ()


class NotEq(VyperNode):
    __slots__ = ()


class And(VyperNode):
    __slots__ = ()


class Or(VyperNode):
    __slots__ = ()


class Not(VyperNode):
    __slots__ = ()


class USub(VyperNode):
    __slots__ = ()


class UAdd(VyperNode):
    __slots__ = ()


class Expr(VyperNode):
    __slots__ = ('value', )


class Pass(VyperNode):
    __slots__ = ()


class AnnAssign(VyperNode):
    __slots__ = ('target', 'annotation', 'value', 'simple')


class Assign(VyperNode):
    __slots__ = ('targets', 'value')


class If(VyperNode):
    __slots__ = ('test', 'body', 'orelse')


class Assert(VyperNode):
    __slots__ = ('test', 'msg')


class For(VyperNode):
    __slots__ = ('iter', 'target', 'body')
    _only_empty_fields = ('orelse', )


class AugAssign(VyperNode):
    __slots__ = ('op', 'target', 'value')


class Break(VyperNode):
    __slots__ = ()


class Continue(VyperNode):
    __slots__ = ()


class Return(VyperNode):
    __slots__ = ('value', )


class Delete(VyperNode):
    __slots__ = ('targets', )


class stmt(VyperNode):
    __slots__ = ()


class ClassDef(VyperNode):
    __slots__ = ('class_type', 'name', 'body')


class Raise(VyperNode):
    __slots__ = ('exc', )


class Slice(VyperNode):
    _only_empty_fields = ('lower', )


class alias(VyperNode):
    __slots__ = ('name', 'asname')


class ImportFrom(VyperNode):
    __slots__ = ('level', 'module', 'names')
