import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from solver import solve, parse_math


def check(mode,expression='',**values):
    result=solve({'mode':mode,'expression':expression,**values})
    assert result['ok'], result
    assert result['answers']
    assert result['steps']
    return result


def test_quadratic():
    r=check('equation','2x^2-5x+2=0')
    assert '1 / 2' in r['answers'][0]
    assert '2' in r['answers'][0]
    assert any('Discriminant' in step['label'] for step in r['steps'])


def test_linear_and_identity():
    assert check('equation','2x+4=0')['ok']
    assert 'mathbb{R}' in check('equation','0=0')['answers'][0]


def test_inequations():
    assert '2, 3' in check('inequation','x^2-5x+6<=0')['answers'][0]
    assert check('inequation','(x-1)/(x+2)>0')['ok']


def test_factor_and_expand():
    assert 'x - 3' in check('factoriser','x^2-9')['answers'][0]
    assert 'x^{2}' in check('developper','(x+1)^2')['answers'][0]
    assert 'x + 1' in check('simplifier','(x^2-1)/(x-1)')['answers'][0]


def test_derivative_tangent():
    r=check('derivee','x^2',point='2')
    assert any('tangente' in step['label'] for step in r['steps'])
    assert r['plot']


def test_integrals():
    assert 'x^{2}' in check('integrale','2x')['answers'][0]
    assert '=4' in check('integrale','2x',lower='0',upper='2')['answers'][0]


def test_limits():
    assert '=1' in check('limite','sin(x)/x',point='0')['answers'][0]
    assert 'existe pas' in check('limite','1/x',point='0')['answers'][0]
    assert check('limite','1/x',point='inf')['ok']


def test_function_study():
    r=check('fonction','x^3-3x^2+2')
    assert any('croissance' in item['label'] for item in r['steps'])
    assert r['plot']


def test_system():
    assert '2' in check('systeme','2x+y=5; x-y=1')['answers'][0]


def test_sequence():
    r=check('suite','(u+3)/4',start='5',count='3')
    assert r['answers']==['u_{0}=5','u_{1}=2','u_{2}=5 / 4']


def test_stats():
    r=check('statistiques','2;4;6;8')
    assert '\\bar x=5' in r['answers']
    assert 'V=5' in r['answers']


def test_complex():
    assert '|z|=5' in check('complexes','3+4i')['answers']


def test_arithmetic():
    assert 'PGCD=6' in check('arithmetique',first='18',second='24')['answers']


def test_probability():
    assert '15 / 128' in check('probabilites',first='10',second='3',point='0.5')['answers'][0]


def test_finance():
    assert check('finance',first='100000',point='5',second='3')['ok']


def test_auto_detection():
    assert check('auto','x^2=4')['ok']


def test_errors_are_structured():
    for data in [
        {'mode':'equation','expression':'hello(x)=0'},
        {'mode':'equation','expression':'x.__class__'},
        {'mode':'equation','expression':'x=1; y=2'},
        {'mode':'systeme','expression':'x+y=3'},
        {'mode':'suite','expression':'u+1','count':'100'},
        {'mode':'probabilites','first':'4','second':'5','point':'0.3'},
        {'mode':'statistiques','expression':'1'},
        {'mode':'limite','expression':'1/x','point':'Bonjour'},
        {'mode':'unknown','expression':'x'},
    ]:
        result=solve(data)
        assert result['ok'] is False, data
        assert isinstance(result['error'],str) and result['error']


def test_invalid_expression_not_executed():
    for bad in ["__import__('os')",'x.__class__','open(1)','x[0]','x; y', 'x\nimport os']:
        try:
            parse_math(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(bad)
