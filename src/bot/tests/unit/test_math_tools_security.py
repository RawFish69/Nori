"""Security regression tests for the `/math` expression parser.

The `/math` commands parse user input with SymPy. SymPy's default ``sympify``
evaluates through Python's ``eval``, which previously allowed arbitrary code
execution (e.g. ``__import__('os').system(...)``). ``parse_math_expr`` must
keep normal math working while making code execution unreachable -- including
the ``chr()``-concatenation bypass that defeats a naive character filter.
"""
from __future__ import annotations

import pytest
import sympy as sp

from lib.commands import math_tools
from lib.commands.math_tools import parse_math_expr, safe_math_expr


DIRECT_PAYLOADS = [
    "__import__('os').system('id')",
    "__import__('urllib.request').request.urlopen('https://example.com', timeout=5).status",
    "open('/etc/passwd').read()",
    "getattr(__import__('os'), 'system')('id')",
]


def _chr_bypass_payload(command: str) -> str:
    """Rebuild a command at runtime via ``chr()`` so the char filter sees only
    harmless characters (letters, digits, ``+``, ``(``, ``)``, ``.``)."""
    inner = "+".join(f"chr({ord(char)})" for char in command)
    return f"eval({inner})"


class TestSafeMathExprFilter:
    @pytest.mark.parametrize("payload", DIRECT_PAYLOADS)
    def test_rejects_code_execution_metacharacters(self, payload):
        with pytest.raises(ValueError):
            safe_math_expr(payload)

    def test_keeps_normal_input(self):
        assert safe_math_expr("x^2 + 2x") == "x**2 + 2*x"


class TestParseMathExprSecurity:
    @pytest.mark.parametrize("payload", DIRECT_PAYLOADS)
    def test_direct_payloads_are_blocked_before_eval(self, payload):
        with pytest.raises(ValueError):
            parse_math_expr(payload)

    def test_chr_bypass_does_not_execute(self, tmp_path):
        canary = tmp_path / "pwned_chr"
        command = f"__import__('os').system('touch {canary}')"
        try:
            result = parse_math_expr(_chr_bypass_payload(command))
        except (ValueError, SyntaxError, sp.SympifyError):
            result = None
        assert not canary.exists(), "chr() bypass executed a shell command"
        assert result is None or isinstance(result, sp.Basic)

    def test_namespace_has_no_python_builtins(self):
        namespace = math_tools._MATH_GLOBAL_DICT
        assert namespace["__builtins__"] == {}
        for name in ("__import__", "eval", "exec", "open", "chr", "getattr"):
            assert name not in namespace

    def test_parsing_does_not_unlock_namespace(self):
        parse_math_expr("sin(x) + 1")
        assert math_tools._MATH_GLOBAL_DICT["__builtins__"] == {}


class TestLegitimateExpressions:
    @pytest.mark.parametrize(
        ("expr", "expected"),
        [
            ("x^2", sp.Symbol("x") ** 2),
            ("2x", 2 * sp.Symbol("x")),
            ("x^2+2x", sp.Symbol("x") ** 2 + 2 * sp.Symbol("x")),
            ("sin(x)", sp.sin(sp.Symbol("x"))),
            ("exp(x)", sp.exp(sp.Symbol("x"))),
            ("sqrt(x)", sp.sqrt(sp.Symbol("x"))),
        ],
    )
    def test_common_inputs_parse(self, expr, expected):
        assert parse_math_expr(expr) == expected

    def test_integrand_formatting_still_works(self):
        # `/math integral` previously did its own `x^2` / `2x` rewriting.
        x = sp.Symbol("x")
        assert parse_math_expr("2x^2") == 2 * x ** 2
