import random
from collections import defaultdict
from typing import Callable

from pygoco.antlr4_base import GoParser
from pygoco.antlr4_base import GoParserVisitor
from llvmlite import ir

from pygoco.core import type_defs
from pygoco.core.type_defs import CONVERTABLE_INT_EXT
from pygoco.core.type_defs import CONVERTABLE_INT_TRUNC


class PygocoVisitor(GoParserVisitor):
    def __init__(self):
        self.module: ir.Module = None
        self.current_function: ir.Function = None
        self.current_block: ir.Block = None
        self.current_builder: ir.IRBuilder = None
        self.current_scope_name: str = None
        self.variables_scopes = defaultdict(dict)
        self.printf: Callable = None
        self.scanf: Callable = None

    def try_convert_to_one_type(self, lhs, rhs):
        rhs = self.get_variable_value(rhs)
        lhs = self.get_variable_value(lhs)
        if lhs.type.intrinsic_name == rhs.type.intrinsic_name:
            return lhs, rhs
        if lhs.type.intrinsic_name == 'i1' or rhs.type.intrinsic_name == 'i1':
            if lhs.type.intrinsic_name == 'i1':
                rhs = self.current_builder.icmp_signed('>', rhs, rhs.type(0))
            else:
                lhs = self.current_builder.icmp_signed('>', lhs, lhs.type(0))
            return lhs, rhs
        if lhs.type.intrinsic_name == 'f64' or rhs.type.intrinsic_name == 'f64':
            if lhs.type.intrinsic_name == 'f64':
                rhs = self.current_builder.sitofp(rhs, ir.DoubleType())
            else:
                lhs = self.current_builder.sitofp(lhs, ir.DoubleType())
            return lhs, rhs
        if lhs.type.intrinsic_name in CONVERTABLE_INT_EXT[rhs.type.intrinsic_name]:
            rhs = self.current_builder.sext(rhs, lhs.type)
            return lhs, rhs
        if rhs.type.intrinsic_name in CONVERTABLE_INT_EXT[lhs.type.intrinsic_name]:
            lhs = self.current_builder.sext(lhs, rhs.type)
            return lhs, rhs
        if lhs.type.intrinsic_name in CONVERTABLE_INT_TRUNC[rhs.type.intrinsic_name]:
            rhs = self.current_builder.trunc(rhs, lhs.type)
            return lhs, rhs
        if rhs.type.intrinsic_name in CONVERTABLE_INT_TRUNC[lhs.type.intrinsic_name]:
            lhs = self.current_builder.trunc(lhs, rhs.type)
            return lhs, rhs
        raise Exception('Filed to convert types')

    def maybe_convert_type(self, value, target_type):
        if isinstance(value, ir.Constant):
            value.type = target_type
            return value
        if isinstance(value, ir.AllocaInstr):
            value = self.current_builder.load(value, name=value.name)
        if value.type == target_type:
            return value
        if target_type.intrinsic_name == 'f64':
            value = self.current_builder.sitofp(value, ir.DoubleType())
            return value
        if target_type.intrinsic_name == 'i1':
            value = self.current_builder.icmp_signed('>', value, value.type(0))
            return value
        if target_type.intrinsic_name in CONVERTABLE_INT_EXT[value.type.intrinsic_name]:
            value = self.current_builder.sext(value, target_type)
            return value
        if target_type.intrinsic_name in CONVERTABLE_INT_TRUNC[value.type.intrinsic_name]:
            value = self.current_builder.trunc(value, target_type)
            return value
        raise Exception('Filed to convert type to target')

    def declare_printf_function(self):
        function_type = ir.FunctionType(ir.IntType(32), [ir.IntType(8).as_pointer()], var_arg=True)
        printf_function = ir.Function(self.module, function_type, name='printf')

        def printf(fmt: str, *args, builder: ir.IRBuilder) -> ir.Function:
            fmt_text = fmt
            fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt_text)), bytearray(fmt_text.encode()))
            fmt_name = f'{self.current_scope_name}_{str(hash(random.random()))[:5]}'
            fmt_arg = ir.GlobalVariable(self.module, fmt.type, name=fmt_name)
            fmt_arg.linkage = 'internal'
            fmt_arg.global_constant = True
            fmt_arg.initializer = fmt
            fmt_arg = builder.bitcast(fmt_arg, ir.IntType(8).as_pointer())
            res = builder.call(printf_function, [fmt_arg, *args])
            return res

        self.printf = printf

    def declare_scanf_function(self):
        function_type = ir.FunctionType(ir.IntType(32), [ir.IntType(8).as_pointer()], var_arg=True)
        scanf_function = ir.Function(self.module, function_type, name='scanf')

        def scanf(fmt: str, *args, builder: ir.IRBuilder) -> ir.Function:
            fmt_text = fmt
            fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt_text)), bytearray(fmt_text.encode()))
            fmt_name = f'{self.current_scope_name}_{str(hash(random.random()))[:5]}'
            fmt_arg = ir.GlobalVariable(self.module, fmt.type, name=fmt_name)
            fmt_arg.linkage = 'internal'
            fmt_arg.global_constant = True
            fmt_arg.initializer = fmt
            fmt_arg = builder.bitcast(fmt_arg, ir.IntType(8).as_pointer())
            res = builder.call(scanf_function, [fmt_arg, *args])
            return res

        self.scanf = scanf

    def visitSourceFile(self, ctx: GoParser.SourceFileContext):
        self.visitChildren(ctx)
        return self.module

    def visitPackageClause(self, ctx: GoParser.PackageClauseContext):
        package_name = ctx.IDENTIFIER().getText()
        self.module = ir.Module(name=package_name)
        self.declare_printf_function()
        self.declare_scanf_function()
        self.visitChildren(ctx)

    def visitDeclaration(self, ctx: GoParser.DeclarationContext):
        return self.visitChildren(ctx)

    def visitConstDecl(self, ctx: GoParser.ConstDeclContext):
        return self.visitChildren(ctx)

    def visitConstSpec(self, ctx: GoParser.ConstSpecContext):
        return self.visitChildren(ctx)

    def visitIdentifierList(self, ctx: GoParser.IdentifierListContext):
        return [identifier.getText() for identifier in ctx.children]

    def visitExpressionList(self, ctx: GoParser.ExpressionListContext):
        if len(ctx.children) == 1:
            return self.visitChildren(ctx)
        values = []
        expressions = ctx.getChildren(lambda c: isinstance(c, GoParser.ExpressionContext))
        for expression in expressions:
            values.append(self.visitExpression(expression))
        return values

    def visitTypeDecl(self, ctx: GoParser.TypeDeclContext):
        return self.visitChildren(ctx)

    def visitTypeSpec(self, ctx: GoParser.TypeSpecContext):
        return self.visitChildren(ctx)

    def visitFunctionDecl(self, ctx: GoParser.FunctionDeclContext):
        name = ctx.IDENTIFIER().getText()
        return_type = ir.VoidType()
        parameters = self.visitParameters(ctx.signature().parameters())
        parameters_names = [param[0] for param in parameters]
        parameters_types = [param[1] for param in parameters]
        if ctx.signature().result():
            return_type = self.visitType_(ctx.signature().result().type_())

        self.current_function = ir.Function(self.module, ir.FunctionType(return_type, parameters_types), name=name)
        self.current_block = self.current_function.append_basic_block(name='entry')
        self.current_builder = ir.IRBuilder(self.current_block)
        self.current_scope_name = f'function_{name}_{return_type.__class__.__name__}'

        args = self.current_function.args
        for arg_name, arg in zip(parameters_names, args):
            arg.name = arg_name
            self.variables_scopes[self.current_scope_name][arg_name] = self.replace_argument_with_variable(arg)

        result = self.visitBlock(ctx.block())
        if result is None:
            if isinstance(return_type, ir.VoidType):
                self.current_builder.ret_void()
            elif not self.current_builder.block.is_terminated:
                self.current_builder.unreachable()
        return self.current_function

    def visitVarDecl(self, ctx: GoParser.VarDeclContext):
        return self.visitChildren(ctx)

    def visitVarSpec(self, ctx: GoParser.VarSpecContext):
        variable_name = ctx.identifierList().getText()
        variable_type = self.visitType_(ctx.type_())
        variable = self.current_builder.alloca(variable_type, name=variable_name)
        self.variables_scopes[self.current_scope_name][variable_name] = variable
        if ctx.expressionList():
            value = self.visitExpressionList(ctx.expressionList())
            value = self.maybe_convert_type(value, variable.type.pointee)
            self.current_builder.store(value, variable)
        return variable

    def visitBlock(self, ctx: GoParser.BlockContext):
        return self.visitChildren(ctx)

    def visitStatementList(self, ctx: GoParser.StatementListContext):
        return self.visitChildren(ctx)

    def visitStatement(self, ctx: GoParser.StatementContext):
        return self.visitChildren(ctx)

    def visitSimpleStmt(self, ctx: GoParser.SimpleStmtContext):
        return self.visitChildren(ctx)

    def visitExpressionStmt(self, ctx: GoParser.ExpressionStmtContext):
        return self.visitChildren(ctx)

    def visitIncDecStmt(self, ctx: GoParser.IncDecStmtContext):
        lhs = self.visitExpression(ctx.expression())
        value = self.get_variable_value(lhs)
        if ctx.PLUS_PLUS():
            add = self.current_builder.add(value, value.type(1))
            self.current_builder.store(add, lhs)
            self.replace_variable(lhs)
            res = lhs
        else:
            sub = self.current_builder.sub(value, value.type(1))
            self.current_builder.store(sub, lhs)
            self.replace_variable(lhs)
            res = lhs
        return res

    def replace_variable(self, variable):
        name = variable.name.split('.')[0]
        self.variables_scopes[self.current_scope_name][name] = variable

    def get_variable_value(self, variable):
        if isinstance(variable, tuple):
            vector = self.get_variable_value(variable[0])
            index = self.get_variable_value(variable[1])
            element = self.current_builder.extract_element(vector, index, name=vector.name)
            return element
        if isinstance(variable, ir.AllocaInstr):
            return self.current_builder.load(variable, name=variable.name)
        return variable

    def replace_argument_with_variable(self, argument: ir.Argument) -> ir.AllocaInstr:
        variable = self.current_builder.alloca(argument.type, name=argument.name)
        self.current_builder.store(argument, variable)
        self.replace_variable(variable)
        return variable

    def add(self, lhs, rhs):
        if lhs.type.intrinsic_name == 'f64':
            return self.current_builder.fadd(lhs, rhs)
        return self.current_builder.add(lhs, rhs)

    def sub(self, lhs, rhs):
        if lhs.type.intrinsic_name == 'f64':
            return self.current_builder.fsub(lhs, rhs)
        return self.current_builder.sub(lhs, rhs)

    def mul(self, lhs, rhs):
        if lhs.type.intrinsic_name == 'f64':
            return self.current_builder.fmul(lhs, rhs)
        return self.current_builder.mul(lhs, rhs)

    def div(self, lhs, rhs):
        if lhs.type.intrinsic_name == 'f64':
            return self.current_builder.fdiv(lhs, rhs)
        return self.current_builder.sdiv(lhs, rhs)

    def assign_to_variable(self, lhs, ctx: GoParser.AssignmentContext):
        variable = lhs
        if isinstance(lhs, ir.Argument):
            variable = self.replace_argument_with_variable(lhs)
        operation = ctx.assign_op().getText()
        rhs = self.visitExpressionList(ctx.expressionList(1))
        rhs = self.get_variable_value(rhs)
        rhs = self.maybe_convert_type(rhs, variable.type.pointee)
        if operation == '=':
            self.current_builder.store(rhs, variable)
            self.replace_variable(variable)
            res = variable
        elif operation == '+=':
            add = self.add(self.get_variable_value(variable), rhs)
            self.current_builder.store(add, variable)
            self.replace_variable(variable)
            res = variable
        elif operation == '-=':
            sub = self.sub(self.get_variable_value(variable), rhs)
            self.current_builder.store(sub, variable)
            self.replace_variable(variable)
            res = variable
        elif operation == '*=':
            mul = self.mul(self.get_variable_value(variable), rhs)
            self.current_builder.store(mul, variable)
            self.replace_variable(variable)
            res = variable
        elif operation == '/=':
            div = self.div(self.get_variable_value(variable), rhs)
            self.current_builder.store(div, variable)
            self.replace_variable(variable)
            res = variable
        else:
            raise Exception(f'Unknown assigment operation {operation}')
        return res

    def assign_to_array_element(self, vector, index, ctx: GoParser.AssignmentContext):
        index = self.get_variable_value(index)
        if isinstance(vector, ir.Argument):
            vector = self.replace_argument_with_variable(vector)
        operation = ctx.assign_op().getText()
        rhs = self.visitExpressionList(ctx.expressionList(1))
        rhs = self.get_variable_value(rhs)
        rhs = self.maybe_convert_type(rhs, vector.type.pointee.element)
        if operation == '=':
            assign = self.current_builder.insert_element(self.get_variable_value(vector), rhs, index, name=vector.name)
            self.current_builder.store(assign, vector)
            self.replace_variable(vector)
            return vector
        element = self.get_variable_value((vector, index))
        if operation == '+=':
            add = self.add(self.get_variable_value(element), rhs)
            assign = self.current_builder.insert_element(self.get_variable_value(vector), add, index, name=vector.name)
            self.current_builder.store(assign, vector)
            self.replace_variable(vector)
        elif operation == '-=':
            sub = self.sub(self.get_variable_value(element), rhs)
            assign = self.current_builder.insert_element(self.get_variable_value(vector), sub, index, name=vector.name)
            self.current_builder.store(assign, vector)
            self.replace_variable(vector)
        elif operation == '*=':
            mul = self.mul(self.get_variable_value(element), rhs)
            assign = self.current_builder.insert_element(self.get_variable_value(vector), mul, index, name=vector.name)
            self.current_builder.store(assign, vector)
            self.replace_variable(vector)
        elif operation == '/=':
            div = self.div(self.get_variable_value(element), rhs)
            assign = self.current_builder.insert_element(self.get_variable_value(vector), div, index, name=vector.name)
            self.current_builder.store(assign, vector)
            self.replace_variable(vector)
        else:
            raise Exception(f'Unknown assigment operation {operation}')
        return vector

    def visitAssignment(self, ctx: GoParser.AssignmentContext):
        lhs = self.visitExpressionList(ctx.expressionList(0))
        if isinstance(lhs, tuple):
            self.assign_to_array_element(lhs[0], lhs[1], ctx)
        else:
            self.assign_to_variable(lhs, ctx)

    def visitAssign_op(self, ctx: GoParser.Assign_opContext):
        return self.visitChildren(ctx)

    def visitShortVarDecl(self, ctx: GoParser.ShortVarDeclContext):
        variable_name = ctx.identifierList().getText()
        variable_value = self.get_variable_value(self.visitExpressionList(ctx.expressionList()))
        variable = self.current_builder.alloca(variable_value.type, name=variable_name)
        self.current_builder.store(variable_value, variable)
        self.variables_scopes[self.current_scope_name][variable_name] = variable
        return variable

    def visitEmptyStmt(self, ctx: GoParser.EmptyStmtContext):
        return self.visitChildren(ctx)

    def visitLabeledStmt(self, ctx: GoParser.LabeledStmtContext):
        return self.visitChildren(ctx)

    def visitReturnStmt(self, ctx: GoParser.ReturnStmtContext):
        result = self.visitExpressionList(ctx.expressionList())
        result = self.maybe_convert_type(result, self.current_function.return_value.type)
        return self.current_builder.ret(result)

    def visitBreakStmt(self, ctx: GoParser.BreakStmtContext):
        return self.visitChildren(ctx)

    def visitContinueStmt(self, ctx: GoParser.ContinueStmtContext):
        return self.visitChildren(ctx)

    def visitIfStmt(self, ctx: GoParser.IfStmtContext):
        predicate = self.visitExpression(ctx.expression())
        if len(ctx.children) == 5:
            with self.current_builder.if_else(predicate) as (then, otherwise):
                with then:
                    self.visitBlock(ctx.block(0))
                with otherwise:
                    self.visitBlock(ctx.block(1))
        else:
            with self.current_builder.if_then(predicate):
                self.visitBlock(ctx.block(0))

    def visitTypeList(self, ctx: GoParser.TypeListContext):
        return self.visitChildren(ctx)

    def pop_variable(self, variable):
        var_name = variable.name.split('.')[0]
        self.variables_scopes[self.current_scope_name].pop(var_name)

    def visitForStmt(self, ctx: GoParser.ForStmtContext):
        idx, pred_ctx, iter_ctx = self.visitForClause(ctx.forClause())
        for_loop_block = self.current_builder.append_basic_block('for_loop')
        pred1 = self.visitExpression(pred_ctx)
        with self.current_builder.if_then(pred1) as then:
            self.current_builder.branch(for_loop_block)
        with self.current_builder.goto_block(for_loop_block):
            self.visitBlock(ctx.block())
            self.visitSimpleStmt(iter_ctx)
            pred = self.visitExpression(pred_ctx)
            with self.current_builder.if_then(pred):
                self.current_builder.branch(for_loop_block)
            self.current_builder.branch(then)
        self.pop_variable(idx)

    def visitForClause(self, ctx: GoParser.ForClauseContext):
        idx = self.visitSimpleStmt(ctx.simpleStmt(0))
        pred_expr = ctx.expression()
        iter_stmt = ctx.simpleStmt(1)
        return idx, pred_expr, iter_stmt

    def visitRangeClause(self, ctx: GoParser.RangeClauseContext):
        return self.visitChildren(ctx)

    def visitType_(self, ctx: GoParser.Type_Context):
        if ctx.typeName():
            type_name = ctx.typeName().IDENTIFIER().getText()
            if type_name in type_defs.INT_TYPES:
                return type_defs.INT_TYPES[type_name]
            if type_name in type_defs.BOOL_TYPES:
                return type_defs.BOOL_TYPES[type_name]
            if type_name in type_defs.FLOAT_TYPES:
                return type_defs.FLOAT_TYPES[type_name]
        elif ctx.typeLit():
            return self.visitTypeLit(ctx.typeLit())
        raise Exception('Unknown type')

    def visitTypeName(self, ctx: GoParser.TypeNameContext):
        return self.visitChildren(ctx)

    def visitTypeLit(self, ctx: GoParser.TypeLitContext):
        return self.visitChildren(ctx)

    def visitArrayType(self, ctx: GoParser.ArrayTypeContext):
        length = self.visitArrayLength(ctx.arrayLength()).constant
        element_type = self.visitElementType(ctx.elementType())
        return ir.VectorType(element_type, length)

    def visitArrayLength(self, ctx: GoParser.ArrayLengthContext):
        return self.visitChildren(ctx)

    def visitElementType(self, ctx: GoParser.ElementTypeContext):
        return self.visitChildren(ctx)

    def visitPointerType(self, ctx: GoParser.PointerTypeContext):
        return self.visitChildren(ctx)

    def visitSliceType(self, ctx: GoParser.SliceTypeContext):
        return self.visitChildren(ctx)

    def visitMapType(self, ctx: GoParser.MapTypeContext):
        return self.visitChildren(ctx)

    def visitMethodSpec(self, ctx: GoParser.MethodSpecContext):
        return self.visitChildren(ctx)

    def visitFunctionType(self, ctx: GoParser.FunctionTypeContext):
        return self.visitChildren(ctx)

    def visitSignature(self, ctx: GoParser.SignatureContext):
        return self.visitChildren(ctx)

    def visitResult(self, ctx: GoParser.ResultContext):
        return self.visitChildren(ctx)

    def visitParameters(self, ctx: GoParser.ParametersContext):
        if len(ctx.children) == 0:
            return []
        parameters = []
        for param_decl in ctx.getChildren(lambda c: isinstance(c, GoParser.ParameterDeclContext)):
            params = self.visitParameterDecl(param_decl)
            parameters.extend(params)
        return parameters

    def visitParameterDecl(self, ctx: GoParser.ParameterDeclContext):
        identifiers = self.visitIdentifierList(ctx.identifierList())
        type_ = self.visitType_(ctx.type_())
        parameters = [(identifier, type_) for identifier in identifiers]
        return parameters

    def visitExpression(self, ctx: GoParser.ExpressionContext):
        if ctx.add_op:
            lhs: ir.Constant = self.visitExpression(ctx.expression(0))
            rhs: ir.Constant = self.visitExpression(ctx.expression(1))
            lhs, rhs = self.try_convert_to_one_type(lhs, rhs)
            if ctx.add_op.text == '+':
                return self.add(lhs, rhs)
            elif ctx.add_op.text == '-':
                return self.sub(lhs, rhs)
            elif ctx.add_op.text == '|':
                return self.current_builder.or_(lhs, rhs)
            elif ctx.add_op.text == '^':
                return self.current_builder.xor(lhs, rhs)
        elif ctx.mul_op:
            lhs: ir.Constant = self.visitExpression(ctx.expression(0))
            rhs: ir.Constant = self.visitExpression(ctx.expression(1))
            lhs, rhs = self.try_convert_to_one_type(lhs, rhs)
            if ctx.mul_op.text == '*':
                return self.mul(lhs, rhs)
            elif ctx.mul_op.text == '/':
                return self.div(lhs, rhs)
            elif ctx.mul_op.text == '%':
                return self.current_builder.srem(lhs, rhs)
            elif ctx.mul_op.text == '<<':
                return self.current_builder.shl(lhs, rhs)
            elif ctx.mul_op.text == '>>':
                return self.current_builder.ashr(lhs, rhs)
            elif ctx.mul_op.text == '&':
                return self.current_builder.and_(lhs, rhs)
            elif ctx.mul_op.text == '&^':
                return self.current_builder.not_(self.current_builder.and_(lhs, rhs))
        elif ctx.rel_op:
            lhs: ir.Constant = self.visitExpression(ctx.expression(0))
            rhs: ir.Constant = self.visitExpression(ctx.expression(1))
            lhs, rhs = self.try_convert_to_one_type(lhs, rhs)
            res = self.current_builder.icmp_signed(ctx.rel_op.text, lhs, rhs)
            return res

        return self.visitChildren(ctx)

    def visitPrimaryExpr(self, ctx: GoParser.PrimaryExprContext):
        if not ctx.primaryExpr():
            value = self.visitChildren(ctx)
            return value
        left = self.visitPrimaryExpr(ctx.primaryExpr())
        if ctx.index():
            vector = left
            index = self.visitIndex(ctx.index())
            return vector, index
        arguments = self.visitArguments(ctx.arguments()) or []
        if not isinstance(arguments, list):
            arguments = [arguments]
        if left == 'printf':
            retyped_arguments = []
            for stock_arg in arguments:
                retyped_arguments.append(self.get_variable_value(stock_arg))
            return self.printf(*retyped_arguments, builder=self.current_builder)
        elif left == 'scanf':
            return self.scanf(*arguments, builder=self.current_builder)
        elif left:
            function = self.module.globals.get(left)
            retyped_arguments = []
            for stock_arg, arg in zip(arguments, function.args):
                retyped_arguments.append(self.maybe_convert_type(stock_arg, arg.type))
            function_call = self.current_builder.call(function, retyped_arguments)
            return function_call

    def visitConversion(self, ctx: GoParser.ConversionContext):
        return self.visitChildren(ctx)

    def visitNonNamedType(self, ctx: GoParser.NonNamedTypeContext):
        return self.visitChildren(ctx)

    def visitOperand(self, ctx: GoParser.OperandContext):
        if ctx.L_PAREN():
            return self.visitExpression(ctx.expression())
        return self.visitChildren(ctx)

    def visitLiteral(self, ctx: GoParser.LiteralContext):
        value = self.visitChildren(ctx)
        return value

    def visitBasicLit(self, ctx: GoParser.BasicLitContext):
        if ctx.integer():
            return self.visitInteger(ctx.integer())
        elif ctx.string_():
            return self.visitString_(ctx.string_())
        number = float(ctx.getText())
        return ir.DoubleType()(number)

    def visitInteger(self, ctx: GoParser.IntegerContext):
        number = int(ctx.getText())
        return ir.IntType(32)(number)

    def visitOperandName(self, ctx: GoParser.OperandNameContext):
        module_globals = list(self.module.globals.keys())
        name = ctx.getText()
        if name == 'true':
            return ir.IntType(1)(1)
        if name == 'false':
            return ir.IntType(1)(0)
        if name in module_globals:
            return name
        if name in self.variables_scopes[self.current_scope_name]:
            return self.variables_scopes[self.current_scope_name][name]
        raise Exception(f'Unknown operandName "{name}"')

    def visitCompositeLit(self, ctx: GoParser.CompositeLitContext):
        return self.visitChildren(ctx)

    def visitLiteralType(self, ctx: GoParser.LiteralTypeContext):
        return self.visitChildren(ctx)

    def visitLiteralValue(self, ctx: GoParser.LiteralValueContext):
        return self.visitChildren(ctx)

    def visitElementList(self, ctx: GoParser.ElementListContext):
        return self.visitChildren(ctx)

    def visitKeyedElement(self, ctx: GoParser.KeyedElementContext):
        return self.visitChildren(ctx)

    def visitKey(self, ctx: GoParser.KeyContext):
        return self.visitChildren(ctx)

    def visitElement(self, ctx: GoParser.ElementContext):
        return self.visitChildren(ctx)

    def visitString_(self, ctx: GoParser.String_Context):
        string = ctx.getText().replace('"', '').replace('\\n', '\n')
        return string

    def visitEmbeddedField(self, ctx: GoParser.EmbeddedFieldContext):
        return self.visitChildren(ctx)

    def visitFunctionLit(self, ctx: GoParser.FunctionLitContext):
        return self.visitChildren(ctx)

    def visitIndex(self, ctx: GoParser.IndexContext):
        return self.visitExpression(ctx.expression())

    def visitSlice_(self, ctx: GoParser.Slice_Context):
        return self.visitChildren(ctx)

    def visitArguments(self, ctx: GoParser.ArgumentsContext):
        if ctx.expressionList():
            value = self.visitExpressionList(ctx.expressionList())
            return value
        return self.visitChildren(ctx)

    def visitReceiverType(self, ctx: GoParser.ReceiverTypeContext):
        return self.visitChildren(ctx)

    def visitEos(self, ctx: GoParser.EosContext):
        return self.visitChildren(ctx)
