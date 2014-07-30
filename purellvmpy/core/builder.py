from __future__ import print_function, absolute_import
import functools
from . import lltypes
from purellvmpy.core import llvalues

_CMP_MAP = {
    '>': 'gt',
    '<': 'lt',
    '==': 'eq',
    '!=': 'ne',
    '>=': 'ge',
    '<=': 'le',
}


def _binop(opname, cls=llvalues.Instruction):
    def wrap(fn):
        @functools.wraps(fn)
        def wrapped(self, lhs, rhs, name=''):
            assert lhs.type == rhs.type, "Operands must be the same type"
            instr = cls(self.function, lhs.type, opname, (lhs, rhs), name)
            self._insert(instr)
            return instr

        return wrapped

    return wrap


def _castop(opname, cls=llvalues.CastInstr):
    def wrap(fn):
        @functools.wraps(fn)
        def wrapped(self, val, typ, name=''):
            instr = cls(self.function, opname, val, typ, name)
            self._insert(instr)
            return instr

        return wrapped

    return wrap


class IRBuilder(object):
    def __init__(self, block=None):
        self._block = block
        self._anchor = len(block.instructions) if block else 0

    @property
    def block(self):
        return self._block

    @property
    def function(self):
        return self.block.parent

    def position_before(self, instr):
        self._anchor = max(0, self._block.instructions.find(instr) - 1)

    def position_after(self, instr):
        self._anchor = min(self._block.instructions.find(instr) + 1,
                           len(self._block.instructions))

    def position_at_start(self, block):
        self._block = block
        self._anchor = 0

    def position_at_end(self, block):
        self._block = block
        self._anchor = len(block.instructions)

    def constant(self, typ, val):
        return llvalues.Constant(typ, val)

    def _insert(self, instr):
        self._block.instructions.insert(self._anchor, instr)
        self._anchor += 1

    def _set_terminator(self, term):
        assert not self.block.is_terminated
        self.block.terminator = term
        return term

    #
    # Arithmetic APIs
    #

    @_binop('add')
    def add(self, lhs, rhs, name=''):
        pass

    @_binop('sub')
    def sub(self, lhs, rhs, name=''):
        pass

    @_binop('mul')
    def mul(self, lhs, rhs, name=''):
        pass

    @_binop('udiv')
    def udiv(self, lhs, rhs, name=''):
        pass

    @_binop('sdiv')
    def sdiv(self, lhs, rhs, name=''):
        pass

    #
    # Comparions APIs
    #

    def icmp_signed(self, cmpop, lhs, rhs, name=''):
        op = _CMP_MAP[cmpop]
        if cmpop not in ('==', '!='):
            op = 's' + op
        instr = llvalues.ICMPInstr(self.function, op, lhs, rhs, name=name)
        self._insert(instr)
        return instr

    def icmp_unsigned(self, cmpop, lhs, rhs, name=''):
        op = _CMP_MAP[cmpop]
        if cmpop not in ('==', '!='):
            op = 'u' + op
        instr = llvalues.ICMPInstr(self.function, op, lhs, rhs, name=name)
        self._insert(instr)
        return instr

    def fcmp_ordered(self, cmpop, lhs, rhs, name=''):
        if cmpop in _CMP_MAP:
            op = 'o' + _CMP_MAP[cmpop]
        else:
            op = cmpop
        instr = llvalues.FCMPInstr(self.function, op, lhs, rhs, name=name)
        self._insert(instr)
        return instr

    def fcmp_unordered(self, cmpop, lhs, rhs, name=''):
        if cmpop in _CMP_MAP:
            op = 'u' + _CMP_MAP[cmpop]
        else:
            op = cmpop
        instr = llvalues.FCMPInstr(self.function, op, lhs, rhs, name=name)
        self._insert(instr)
        return instr


    #
    # Cast APIs
    #

    @_castop('trunc')
    def trunc(self, value, typ, name=''):
        pass

    @_castop('zext')
    def zext(self, value, typ, name=''):
        pass

    @_castop('sext')
    def sext(self, value, typ, name=''):
        pass

    @_castop('fptrunc')
    def fptrunc(self, value, typ, name=''):
        pass

    @_castop('fpext')
    def fpext(self, value, typ, name=''):
        pass

    @_castop('bitcast')
    def bitcast(self, value, typ, name=''):
        pass

    @_castop('fptoui')
    def fptoui(self, value, typ, name=''):
        pass

    @_castop('uitofp')
    def uitofp(self, value, typ, name=''):
        pass

    @_castop('fptosi')
    def fptosi(self, value, typ, name=''):
        pass

    @_castop('sitofp')
    def sitofp(self, value, typ, name=''):
        pass

    #
    # Memory APIs
    #

    def alloca(self, typ, count=None, name=''):
        assert count is None or count > 0
        if count is None:
            pass
        elif not isinstance(count, llvalues.Value):
            # If it is not a Value instance,
            # assume to be a python number.
            count = llvalues.Constant(lltypes.IntType(32), int(count))

        al = llvalues.AllocaInstr(self.function, typ, count, name)
        self._insert(al)
        return al

    def load(self, ptr, name=''):
        ld = llvalues.LoadInstr(self.function, ptr, name)
        self._insert(ld)
        return ld

    def store(self, val, ptr):
        st = llvalues.StoreInstr(self.function, val, ptr)
        self._insert(st)
        return st

    #
    # Terminators APIs
    #

    def jump(self, target):
        """Jump to target
        """
        term = llvalues.Terminator(self.function, "br", [target])
        self._set_terminator(term)
        return term

    def branch(self, cond, truebr, falsebr):
        """Branch conditionally
        """
        term = llvalues.Terminator(self.function, "br", [cond, truebr,
                                                         falsebr])
        self._set_terminator(term)
        return term

    def ret_void(self):
        return self._set_terminator(llvalues.Terminator(self.function,
                                                        "ret void", ()))

    def ret(self, value):
        return self._set_terminator(llvalues.Terminator(self.function, "ret",
                                                        [value]))