"""Calculus regressions: known formulas, real domains and singular points."""
import sys
from pathlib import Path

import pytest
import sympy as s

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from solver import (L, parse_math, solve, x, real_domain,
                    numerical_derivative_check)


def derivative(expression, **values):
    result = solve({'mode': 'derivee', 'expression': expression, **values})
    assert result['ok'], result
    return result


@pytest.mark.parametrize(('expression', 'expected'), [
    ('sqrt(x)', '1/(2*sqrt(x))'),
    ('sqrt(3x+2)', '3/(2*sqrt(3*x+2))'),
    ('sqrt(x^2+1)', 'x/sqrt(x**2+1)'),
    ('sqrt(1-x^2)', '-x/sqrt(1-x**2)'),
    ('1/sqrt(x)', '-1/(2*x*sqrt(x))'),
    ('sqrt(x+1)/x', '-(x+2)/(2*x**2*sqrt(x+1))'),
    ('x/sqrt(x^2+1)', '1/((x**2+1)*sqrt(x**2+1))'),
    ('sqrt(x^2+1)/x', '-1/(x**2*sqrt(x**2+1))'),
    ('sqrt(x^2+1)/(x-2)', '-(2*x+1)/((x-2)**2*sqrt(x**2+1))'),
    ('sqrt(x-1)/(x-1)', '-1/(2*(x-1)*sqrt(x-1))'),
    ('sqrt(sqrt(x)+1)', '1/(4*sqrt(x)*sqrt(sqrt(x)+1))'),
    ('sqrt(ln(x))', '1/(2*x*sqrt(log(x)))'),
    ('ln(sqrt(x))', '1/(2*x)'),
    ('exp(sqrt(x))', 'exp(sqrt(x))/(2*sqrt(x))'),
    ('sin(sqrt(x))', 'cos(sqrt(x))/(2*sqrt(x))'),
    ('ln(x)/x^2', '(1-2*log(x))/x**3'),
    ('sin(x)*exp(x)', 'exp(x)*(sin(x)+cos(x))'),
    ('sqrt(x^4)', '2*x'),
    ('x*sqrt(x^2)', '2*Abs(x)'),
    ('sqrt(x^2)', 'sign(x)'),
    ('√(x^2+1)', 'x/sqrt(x**2+1)'),
    ('√x', '1/(2*sqrt(x))'),
    ('f(x) = sqrt(x^2+1)', 'x/sqrt(x**2+1)'),
    ('0.5x^2', 'x'),
])
def test_known_derivative_formulas(expression, expected):
    result = derivative(expression)
    actual = s.sympify(result['derivatives'][0]['expression'], locals={'x': x})
    wanted = s.sympify(expected, locals={'x': x})
    assert s.simplify(actual - wanted) == 0


@pytest.mark.parametrize(('expression', 'function_domain', 'derivative_domain'), [
    ('sqrt(x)', s.Interval(0, s.oo), s.Interval.open(0, s.oo)),
    ('sqrt(1-x^2)', s.Interval(-1, 1), s.Interval.open(-1, 1)),
    ('1/sqrt(x)', s.Interval.open(0, s.oo), s.Interval.open(0, s.oo)),
    ('sqrt(x^2)', s.S.Reals, s.S.Reals - s.FiniteSet(0)),
    ('sqrt(x)^2', s.Interval(0, s.oo), s.Interval.open(0, s.oo)),
    ('sqrt(x-1)/sqrt(x-1)', s.Interval.open(1, s.oo), s.Interval.open(1, s.oo)),
    ('1/(1/x)', s.S.Reals - s.FiniteSet(0), s.S.Reals - s.FiniteSet(0)),
    ('ln(x)-ln(x)', s.Interval.open(0, s.oo), s.Interval.open(0, s.oo)),
    ('sqrt(ln(x))', s.Interval(1, s.oo), s.Interval.open(1, s.oo)),
    ('sqrt(x^4+x^6)', s.S.Reals, s.S.Reals),
])
def test_domains_preserve_restrictions(expression, function_domain, derivative_domain):
    result = derivative(expression)
    assert real_domain(parse_math(expression, evaluate=False)) == function_domain
    assert s.sympify(result['derivatives'][0]['domain']) == derivative_domain
    assert result['derivatives'][0]['domain_complete']


@pytest.mark.parametrize(('expression', 'point'), [
    ('sqrt(x^2)', '0'),
    ('sqrt(x)', '0'),
    ('sqrt(x)', '-1'),
    ('sqrt(-x)', '1'),
    ('sqrt(x+1)', '-1'),
    ('sqrt(x-1)/sqrt(x-1)', '1'),
    ('1/(1/x)', '0'),
])
def test_tangent_rejects_invalid_real_or_nondifferentiable_points(expression, point):
    result = solve({'mode': 'derivee', 'expression': expression, 'point': point})
    assert result['ok'] is False
    assert result['error']


@pytest.mark.parametrize(('expression', 'point', 'answer'), [
    ('sqrt(x)', '4', r'y=\frac{x}{4} + 1'),
    ('sqrt(x^2)', '-2', 'y=- x'),
    ('sqrt(x^2)', '2', 'y=x'),
    ('x*sqrt(x^2)', '0', 'y=0'),
    ('sqrt(x^4+x^6)', '0', 'y=0'),
])
def test_tangent_values_including_removable_derivative_singularities(expression, point, answer):
    result = derivative(expression, point=point)
    assert answer in result['answers']


@pytest.mark.parametrize(('expression', 'order', 'expected'), [
    ('sqrt(x)', '2', '-1/(4*x*sqrt(x))'),
    ('sqrt(x^2+1)', '2', '1/((x**2+1)*sqrt(x**2+1))'),
    ('sqrt(x^2+1)', '3', '-3*x/((x**2+1)**2*sqrt(x**2+1))'),
    ('x^5', '5', '120'),
    ('sqrt(x^2)', '2', '0'),
])
def test_higher_derivatives(expression, order, expected):
    result = derivative(expression, order=order)
    assert len(result['derivatives']) == int(order)
    actual = s.sympify(result['derivatives'][-1]['expression'], locals={'x': x})
    assert s.simplify(actual - s.sympify(expected, locals={'x': x})) == 0
    if expression == 'sqrt(x^2)':
        assert s.sympify(result['derivatives'][-1]['domain']) == s.S.Reals - s.FiniteSet(0)


def test_tangent_uses_first_derivative_even_when_higher_order_requested():
    result = derivative('x^3', order='3', point='2')
    assert 'y=12 x - 16' in result['answers']


def test_successive_derivatives_of_a_root_of_a_polynomial_square():
    result = derivative('sqrt((x^2-1)^2)', order='3')
    second = result['derivatives'][1]
    actual = s.sympify(second['expression'], locals={'x': x})
    for point, expected in [(-2, 2), (0, -2), (2, 2)]:
        assert actual.subs(x, point) == expected
    domain = s.S.Reals - s.FiniteSet(-1, 1)
    assert s.sympify(second['domain']) == domain
    assert s.sympify(result['derivatives'][2]['domain']) == domain
    assert second['domain_complete']
    assert 'sign' not in result['derivatives'][0]['latex']


@pytest.mark.parametrize('order', ['0', '-1', '6', '1.5', 'hello'])
def test_invalid_derivative_orders(order):
    assert not solve({'mode': 'derivee', 'expression': 'x^2', 'order': order})['ok']


@pytest.mark.parametrize('expression', ['sqrt(x^2+1)', 'sqrt(x-1000)', 'sqrt(x-50)*sqrt(51-x)'])
def test_numerical_check_samples_inside_actual_domain(expression):
    result = derivative(expression)
    assert result['verification']['status'] == 'passed'
    assert result['verification']['samples']
    assert max(v['relative_error'] for v in result['verification']['samples']) < 1e-7


def test_independent_numerical_check_detects_wrong_derivative():
    check = numerical_derivative_check(s.sqrt(x), s.Integer(3), s.Interval.open(0, s.oo))
    assert check['status'] == 'inconclusive'
    assert any(v['relative_error'] > 1e-3 for v in check['samples'])


def test_school_notation_uses_fractions_radicals_and_french_intervals():
    result = derivative('x/sqrt(x^2+1)')
    formula = result['derivatives'][0]['latex']
    assert r'\frac{' in formula and r'\sqrt{' in formula
    assert r'\frac{3}{2}' not in formula
    assert ' / ' not in formula
    assert L(s.Interval.open(0, s.oo)) == r'\left]0\,;\,\infty\right['
    assert L(s.Rational(1, 2)) == r'\frac{1}{2}'
    assert r'\ln' in L(s.log(x))


def test_root_chain_rule_explains_the_inner_derivative():
    result = derivative('sqrt(3x+2)')
    assert any('sous la racine' in v['label'] and '=3' in v['latex'] for v in result['steps'])
    assert any('racine composée' in v['label'] for v in result['steps'])


def test_function_study_uses_the_same_real_derivative_domain():
    result = solve({'mode': 'fonction', 'expression': 'sqrt(x^2)'})
    assert result['ok'], result
    critical = next(v for v in result['steps'] if v['label'] == 'Points critiques')
    assert r'\emptyset' in critical['latex']


def test_unknown_domains_are_not_reported_as_all_reals():
    assert real_domain(s.floor(x)) is None
    assert not solve({'mode': 'fonction', 'expression': 'floor(x)'})['ok']


@pytest.mark.parametrize('bad', ['__import__(x)', 'x.__class__', 'sqrt(x)[0]', 'x; y'])
def test_unevaluated_parser_keeps_input_validation(bad):
    with pytest.raises(ValueError):
        parse_math(bad, evaluate=False)
