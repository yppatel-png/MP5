"""Isolated subprocess entry point for one student-code grading request."""

import contextlib
import ast
import json
import os
import sys

MEMORY_LIMIT_BYTES = 512 * 1024 * 1024


class SecurityVisitor(ast.NodeVisitor):
    FORBIDDEN_MODULES = {
        "os", "sys", "subprocess", "socket", "shutil", "pathlib", "importlib",
        "requests", "urllib", "http", "socketserver", "pty", "posix", "_posixsubprocess",
        "ctypes", "winreg", "msvcrt", "builtins", "signal", "threading", "multiprocessing"
    }
    FORBIDDEN_CALLS = {
        "open", "eval", "exec", "__import__", "compile", "globals", "locals",
        "getattr", "setattr", "delattr", "hasattr", "breakpoint", "memoryview"
    }
    FORBIDDEN_ATTRS = {
        "__class__", "__subclasses__", "__bases__", "__globals__", "__code__",
        "__builtins__", "__mro__", "__dict__", "__closure__", "__func__"
    }

    def visit_Import(self, node):
        for alias in node.names:
            base_mod = alias.name.split('.')[0]
            if base_mod in self.FORBIDDEN_MODULES:
                raise ValueError(f"Forbidden construct: module import '{alias.name}' is prohibited.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            base_mod = node.module.split('.')[0]
            if base_mod in self.FORBIDDEN_MODULES:
                raise ValueError(f"Forbidden construct: module import '{node.module}' is prohibited.")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in self.FORBIDDEN_CALLS:
            raise ValueError(f"Forbidden construct: call '{node.func.id}' is prohibited.")
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if node.attr in self.FORBIDDEN_ATTRS:
            raise ValueError(f"Forbidden construct: attribute '{node.attr}' access is prohibited.")
        self.generic_visit(node)


def grade_code(exercise, code_str):
    if not code_str or not code_str.strip():
        return {"score": 0.0, "is_correct": False, "feedback": "No code provided."}

    # 1. Text token fast check
    forbidden = [
        "import os", "import sys", "import subprocess", "import socket",
        "open(", "eval(", "exec(", "__import__",
    ]
    for token in forbidden:
        if token in code_str:
            return {
                "score": 0.0,
                "is_correct": False,
                "feedback": f"Security restriction: Forbidden construct '{token}' detected.",
                "passed_tests": 0,
                "total_tests": 1,
            }

    # 2. AST-level static security scan
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
    payload = json.loads(sys.stdin.read())
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES))
        resource.setrlimit(resource.RLIMIT_CPU, (2, 3))
    except ImportError:
        pass

    with open(os.devnull, "w", encoding="utf-8") as sink, contextlib.redirect_stdout(sink):
        result = grade_code(payload["exercise"], payload["code"])
    sys.stdout.write(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
