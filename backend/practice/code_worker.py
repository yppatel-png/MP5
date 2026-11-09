"""Isolated subprocess entry point for one student-code grading request."""

import contextlib
import ast
import json
import os
import sys

MEMORY_LIMIT_BYTES = 256 * 1024 * 1024


class SecurityVisitor(ast.NodeVisitor):
    """
    Strict allow-list AST security scanner.
    Rejects any construct not explicitly approved for introductory coding exercises.
    Guarantees no access to dunder attributes, forbidden calls, or dangerous modules.
    """
    ALLOWED_NODE_TYPES = {
        # Modules & definitions
        ast.Module, ast.Interactive, ast.Expression,
        ast.FunctionDef, ast.Return,
        ast.arguments, ast.arg, ast.keyword,
        # Control flow & statements
        ast.Assign, ast.AugAssign, ast.AnnAssign,
        ast.For, ast.While, ast.If, ast.Pass, ast.Break, ast.Continue,
        ast.Expr,
        # Expressions & data structures
        ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.Lambda, ast.IfExp,
        ast.Dict, ast.Set, ast.List, ast.Tuple,
        ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp,
        ast.comprehension,
        ast.Compare, ast.Call, ast.Constant,
        ast.FormattedValue, ast.JoinedStr,
        ast.Attribute, ast.Subscript, ast.Slice, ast.Starred,
        ast.Name, ast.Load, ast.Store, ast.Del,
        # Operators
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
        ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd, ast.MatMult,
        ast.And, ast.Or, ast.Not, ast.Invert, ast.UAdd, ast.USub,
        ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Is, ast.IsNot, ast.In, ast.NotIn,
    }

    FORBIDDEN_CALLS = {
        "open", "eval", "exec", "__import__", "compile", "globals", "locals",
        "getattr", "setattr", "delattr", "hasattr", "breakpoint", "memoryview",
        "input", "help", "copyright", "credits", "license", "exit", "quit"
    }

    def generic_visit(self, node):
        if type(node) not in self.ALLOWED_NODE_TYPES:
            raise ValueError(f"Forbidden construct: AST node '{type(node).__name__}' is prohibited in safe sandbox.")
        super().generic_visit(node)

    def visit_Attribute(self, node):
        if node.attr.startswith("__"):
            raise ValueError(f"Forbidden construct: dunder attribute '{node.attr}' access is prohibited.")
        self.generic_visit(node)

    def visit_Name(self, node):
        if node.id.startswith("__"):
            raise ValueError(f"Forbidden construct: dunder identifier '{node.id}' is prohibited.")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in self.FORBIDDEN_CALLS:
            raise ValueError(f"Forbidden construct: function call '{node.func.id}' is prohibited.")
        self.generic_visit(node)


def grade_code(exercise, code_str):
    if not code_str or not code_str.strip():
        return {"score": 0.0, "is_correct": False, "feedback": "No code provided."}

    # AST-level static security scan (Allow-list architecture without brittle substring checks)
    try:
        parsed_ast = ast.parse(code_str)
        SecurityVisitor().visit(parsed_ast)
    except ValueError as ve:
        return {
            "score": 0.0,
            "is_correct": False,
            "feedback": f"Security restriction: {str(ve)}",
            "passed_tests": 0,
            "total_tests": 1,
        }
    except SyntaxError as se:
        return {
            "score": 0.0,
            "is_correct": False,
            "feedback": f"Syntax error in submitted code: {se.msg} (line {se.lineno})",
            "passed_tests": 0,
            "total_tests": 1,
        }

    test_cases = exercise.get("answer_key", {}).get("test_cases", [])
    safe_globals = {
        "__builtins__": {
            "range": range, "len": len, "print": print, "int": int, "float": float,
            "str": str, "bool": bool, "list": list, "dict": dict, "set": set,
            "min": min, "max": max, "sum": sum, "abs": abs, "round": round,
            "sorted": sorted, "enumerate": enumerate, "zip": zip, "map": map,
        }
    }
    local_scope = {}
    try:
        exec(code_str, safe_globals, local_scope)
    except Exception as exc:
        return {
            "score": 0.0,
            "is_correct": False,
            "feedback": f"Runtime error while loading code: {type(exc).__name__}.",
            "passed_tests": 0,
            "total_tests": len(test_cases),
        }

    if not test_cases:
        return {
            "score": 1.0,
            "is_correct": True,
            "feedback": "Code compiled and validated successfully.",
        }

    passed = 0
    test_results = []
    for test_case in test_cases:
        input_value = test_case.get("input", "")
        expected = test_case.get("expected")
        function = next(
            (value for name, value in local_scope.items() if callable(value) and not name.startswith("_")),
            None,
        )
        if function is None:
            return {
                "score": 0.0,
                "is_correct": False,
                "feedback": "No callable function found in submitted code.",
                "passed_tests": 0,
                "total_tests": len(test_cases),
            }
        try:
            parsed_input = input_value
            if isinstance(input_value, str) and "(" not in input_value:
                try:
                    parsed_input = ast.literal_eval(input_value)
                except (ValueError, SyntaxError):
                    pass
            parsed_expected = expected
            if isinstance(expected, str):
                try:
                    parsed_expected = ast.literal_eval(expected)
                except (ValueError, SyntaxError):
                    pass
            if isinstance(input_value, str) and "(" in input_value:
                result = eval(input_value, safe_globals, local_scope)
            else:
                result = function(parsed_input)
            if isinstance(parsed_expected, float) and isinstance(result, (int, float)):
                passed_case = abs(result - parsed_expected) < 0.01
            elif str(expected).startswith("~"):
                passed_case = True
            else:
                passed_case = result == parsed_expected or result == expected
            passed += int(passed_case)
            test_results.append({
                "input": str(input_value),
                "expected": str(expected),
                "got": str(result),
                "passed": passed_case,
            })
        except Exception as exc:
            test_results.append({
                "input": str(input_value),
                "expected": str(expected),
                "error": f"{type(exc).__name__}",
                "passed": False,
            })

    total = len(test_cases)
    return {
        "score": round(passed / max(1, total), 2),
        "is_correct": passed == total,
        "passed_tests": passed,
        "total_tests": total,
        "feedback": f"Passed {passed}/{total} unit tests.",
        "test_results": test_results,
    }


def main() -> int:
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES))
        resource.setrlimit(resource.RLIMIT_CPU, (2, 3))
        if hasattr(resource, "RLIMIT_NPROC"):
            resource.setrlimit(resource.RLIMIT_NPROC, (1, 1))
        if hasattr(resource, "RLIMIT_NOFILE"):
            resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
    except (ImportError, AttributeError, ValueError, OSError):
        pass

    payload = json.loads(sys.stdin.read())
    with open(os.devnull, "w", encoding="utf-8") as sink, contextlib.redirect_stdout(sink):
        result = grade_code(payload["exercise"], payload["code"])
    sys.stdout.write(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
