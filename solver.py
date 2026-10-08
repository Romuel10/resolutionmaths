"""Moteur de résolution symbolique local. Entrées strictement limitées aux notations mathématiques.

Ce module s'exécute dans Pyodide (dans un Worker) ou dans CPython pour les tests.
"""
from __future__ import annotations

import json
import math
import re
from typing import Any

import sympy as s
from sympy.calculus.util import continuous_domain
from sympy.parsing.sympy_parser import (parse_expr, standard_transformations,
                                         implicit_multiplication_application, convert_xor, rationalize)

x, y, n, u = s.symbols('x y n u', real=True)
z = s.Symbol('z')
TRANSFORMS = tuple(t for t in standard_transformations if t.__name__ != 'auto_symbol') + (implicit_multiplication_application, convert_xor, rationalize)
ALLOWED = {
    'x': x, 'y': y, 'n': n, 'u': u, 'z': z, 'pi': s.pi, 'e': s.E, 'E': s.E,
    'i': s.I, 'I': s.I, 'oo': s.oo, 'inf': s.oo,
    'sin': s.sin, 'cos': s.cos, 'tan': s.tan, 'asin': s.asin, 'acos': s.acos,
    'atan': s.atan, 'sqrt': s.sqrt, 'exp': s.exp, 'ln': s.log,
    'log': s.log, 'abs': s.Abs, 'Abs': s.Abs,
    'factorial': s.factorial, 'floor': s.floor, 'ceiling': s.ceiling,
}
GLOBALS = {'__builtins__': {}, 'Integer': s.Integer, 'Float': s.Float,
           'Rational': s.Rational, 'Symbol': s.Symbol}
MODES = {'auto', 'equation', 'inequation', 'simplifier', 'factoriser', 'developper',
         'derivee', 'integrale', 'limite', 'fonction', 'systeme', 'suite',
         'statistiques', 'complexes', 'arithmetique', 'probabilites', 'finance'}


def parse_math(value: Any):
    if not isinstance(value, str) or not value.strip() or len(value) > 350:
        raise ValueError('Saisissez une expression mathématique de moins de 350 caractères.')
    expr = value.strip().replace('−', '-').replace('×', '*').replace('÷', '/')
    expr = expr.replace('π', 'pi').replace('∞', 'oo').replace('²', '^2').replace('³', '^3')
    expr = re.sub(r'\b(?:f|g)\(x\)\s*=', '', expr, count=1)
    # Refuser noms et tokens inconnus avant parse_expr (qui utilise eval en interne).
    if not re.fullmatch(r'[A-Za-z0-9+*/^().,\s-]+', expr):
        raise ValueError('Notation non reconnue. Utilisez x, ^, *, /, sqrt(), sin(), log(), etc.')
    for token in re.findall(r'[A-Za-z][A-Za-z0-9_]*', expr):
        if token not in ALLOWED:
            raise ValueError(f'Nom non autorisé : {token}. Consultez les exemples de saisie.')
    if re.search(r'(?<!\d)\.|\.(?!\d)|\*\*\*|//|\b\d{101,}\b', expr):
        raise ValueError('Notation non autorisée.')
    try:
        result = parse_expr(expr, local_dict=ALLOWED, global_dict=GLOBALS,
                            transformations=TRANSFORMS, evaluate=True)
    except (SyntaxError, TypeError, ValueError, NameError, AttributeError, ZeroDivisionError) as exc:
        raise ValueError('Expression non comprise. Vérifiez les parenthèses et les opérateurs.') from exc
    if not isinstance(result, s.Basic):
        raise ValueError('Une expression mathématique est attendue.')
    if result.count_ops() > 120:
        raise ValueError('Expression trop complexe : simplifiez la saisie.')
    return result


def L(value):
    return s.latex(value, mul_symbol='dot', fold_short_frac=True)


def step(label, latex, note=''):
    return {'label': label, 'latex': str(latex), 'note': note}


def result(title, steps, answers, *, description='', plot=None):
    return {'ok': True, 'title': title, 'description': description,
            'steps': steps, 'answers': [str(a) for a in answers],
            'plot': plot or []}


def read_expr(data, key='expression'):
    return parse_math(data.get(key, ''))


def as_number(value, name, min_value=None, max_value=None):
    try:
        sym = parse_math(str(value))
        if sym.free_symbols or sym.is_real is not True or sym.is_finite is not True:
            raise ValueError()
        out = float(sym)
        if not math.isfinite(out) or (min_value is not None and out < min_value) or (max_value is not None and out > max_value):
            raise ValueError()
        return sym
    except (ValueError, TypeError, OverflowError):
        raise ValueError(f'{name} doit être un nombre réel valide.')


def as_int(value, name, low=0, high=10000):
    num = as_number(value, name, low, high)
    if num.is_integer is not True:
        raise ValueError(f'{name} doit être un entier.')
    return int(num)


def series_plot(expr, a=-8, b=8, count=280):
    if expr.free_symbols - {x}:
        return []
    try:
        fun = s.lambdify(x, expr, modules='math')
    except Exception:
        return []
    pts = []
    for k in range(count + 1):
        xx = a + (b-a)*k/count
        try:
            yy = float(fun(xx))
            if math.isfinite(yy) and abs(yy) < 1000:
                pts.append([round(xx, 5), round(yy, 6)])
            else:
                pts.append(None)
        except (ArithmeticError, ValueError, TypeError, OverflowError):
            pts.append(None)
    return pts


def solve_equation(data):
    raw = str(data.get('expression', ''))
    if raw.count('=') > 1:
        raise ValueError('Saisissez une seule équation ou choisissez « Système ».')
    lhs, rhs = raw.split('=') if '=' in raw else (raw, '0')
    f = s.factor(parse_math(lhs) - parse_math(rhs))
    if f.free_symbols - {x}:
        raise ValueError('La résolution des équations de ce module se fait en x.')
    steps = [step('Équation de départ', f'{L(parse_math(lhs))}={L(parse_math(rhs))}'),
             step('Tout ramener à zéro', f'{L(s.expand(f))}=0')]
    poly = f.as_poly(x)
    if poly is not None and poly.degree() == 2:
        a, b, c = poly.all_coeffs()
        delta = s.simplify(b*b-4*a*c)
        steps += [step('Coefficients', rf'a={L(a)},\quad b={L(b)},\quad c={L(c)}'),
                  step('Discriminant', rf'\Delta=b^2-4ac={L(delta)}')]
    elif poly is not None and poly.degree() > 4:
        steps.append(step('Méthode', L(s.factor(f)), 'Pour les polynômes de degré élevé, certaines racines restent sous forme exacte implicite.'))
    try:
        roots = s.solveset(f, x, domain=s.S.Reals)
    except (NotImplementedError, ValueError):
        roots = s.ConditionSet(x, s.Eq(f, 0), s.S.Reals)
    steps.append(step('Ensemble solution réel', rf'S={L(roots)}'))
    if isinstance(roots, s.FiniteSet) and len(roots) <= 12:
        for r in sorted(roots, key=s.default_sort_key):
            steps.append(step('Vérification', rf'f\left({L(r)}\right)={L(s.simplify(f.subs(x, r)))}'))
    return result('Résolution d’équation', steps, [rf'S={L(roots)}'],
                  description='Résolution dans l’ensemble des nombres réels.')


def solve_inequation(data):
    raw = str(data.get('expression', ''))
    match = re.fullmatch(r'(.+?)(<=|>=|<|>)(.+)', raw.strip())
    if not match:
        raise ValueError('Écrivez par exemple : x^2-5x+6 <= 0.')
    left, op, right = match.groups()
    f = s.factor(parse_math(left)-parse_math(right))
    if f.free_symbols - {x}:
        raise ValueError('Une seule inconnue x est acceptée pour les inéquations.')
    rel = {'<':s.Lt,'>':s.Gt,'<=':s.Le,'>=':s.Ge}[op](f, 0)
    try:
        solutions = s.solve_univariate_inequality(rel, x, relational=False)
    except (ValueError, NotImplementedError) as exc:
        raise ValueError('Cette inéquation nécessite une méthode non encore disponible.') from exc
    steps = [step('Expression réduite', L(rel)),
             step('Factorisation utile', rf'{L(f)}\;{op}\;0'),
             step('Ensemble solution', rf'S={L(solutions)}')]
    return result('Résolution d’inéquation', steps, [rf'S={L(solutions)}'])


def solve_algebra(data, action):
    f = read_expr(data)
    if action == 'factoriser':
        out = s.factor(f)
        label = 'Factorisation'
    elif action == 'developper':
        out = s.expand(f)
        label = 'Développement'
    else:
        out = s.simplify(f)
        label = 'Simplification'
    return result(label, [step('Expression initiale', L(f)), step(label, L(out)),
                          step('Contrôle par différence', rf'{L(s.simplify(f-out))}=0')], [L(out)])


def solve_derivative(data):
    f = read_expr(data)
    if f.free_symbols - {x}:
        raise ValueError('Saisissez une fonction de x uniquement.')
    d = s.simplify(s.diff(f, x))
    steps = [step('Fonction initiale', rf'f(x)={L(f)}'),
             step('Dérivation par rapport à x', rf'f\prime(x)={L(d)}')]
    extra = data.get('point', '')
    answers = [rf'f\prime(x)={L(d)}']
    if str(extra).strip():
        a = as_number(extra, 'Le point x₀')
        va, slope = s.simplify(f.subs(x, a)), s.simplify(d.subs(x, a))
        if not (va.is_finite and slope.is_finite):
            raise ValueError('La fonction ou sa dérivée n’est pas définie au point donné.')
        tangent = s.expand(slope*(x-a)+va)
        steps.extend([step('Valeur et pente au point', rf'f({L(a)})={L(va)},\quad f\prime({L(a)})={L(slope)}'),
                      step('Équation de la tangente', rf'y=f\prime({L(a)})(x-{L(a)})+f({L(a)})={L(tangent)}')])
        answers.append(rf'y={L(tangent)}')
    return result('Dérivée et tangente', steps, answers, plot=series_plot(f))


def solve_integral(data):
    f = read_expr(data)
    if f.free_symbols - {x}:
        raise ValueError('Saisissez une fonction de x uniquement.')
    antiderivative = s.integrate(f, x)
    if isinstance(antiderivative, s.Integral):
        raise ValueError('Aucune primitive élémentaire trouvée pour cette fonction.')
    steps = [step('Fonction à intégrer', L(f)),
             step('Primitive', rf'F(x)={L(antiderivative)}+C'),
             step('Vérification', rf'F\prime(x)={L(s.simplify(s.diff(antiderivative, x)))}')]
    answers = [rf'\int {L(f)}\,dx={L(antiderivative)}+C']
    lower, upper = str(data.get('lower','')).strip(), str(data.get('upper','')).strip()
    if lower or upper:
        if not lower or not upper:
            raise ValueError('Renseignez les deux bornes de l’intégrale.')
        a = as_number(lower, 'La borne inférieure')
        b = as_number(upper, 'La borne supérieure')
        v = s.integrate(f, (x,a,b))
        if v.is_finite is not True:
            raise ValueError('L’intégrale définie n’a pas de valeur finie sur cet intervalle.')
        steps.append(step('Calcul entre les bornes', rf'\int_{{{L(a)}}}^{{{L(b)}}}{L(f)}\,dx={L(v)}'))
        answers = [rf'\int_{{{L(a)}}}^{{{L(b)}}}{L(f)}\,dx={L(v)}']
    return result('Primitives et intégrales', steps, answers)


def solve_limit(data):
    f = read_expr(data)
    rawpoint = str(data.get('point', '0')).strip()
    if rawpoint.lower() in ('+inf','inf','+oo','oo','infty'):
        at = s.oo
    elif rawpoint.lower() in ('-inf','-oo'):
        at = -s.oo
    else:
        at = as_number(rawpoint, 'Le point de limite')
    side = data.get('side', '+-')
    if side not in ('+', '-', '+-'):
        side = '+-'
    if side == '+-' and at not in (s.oo, -s.oo):
        left = s.limit(f,x,at,dir='-')
        right = s.limit(f,x,at,dir='+')
        steps = [step('Limite à gauche', rf'\lim_{{x\to {L(at)}^-}}{L(f)}={L(left)}'),
                 step('Limite à droite', rf'\lim_{{x\to {L(at)}^+}}{L(f)}={L(right)}')]
        if left != right:
            steps.append(step('Conclusion', r'\text{Les limites unilatérales sont différentes.}'))
            return result('Calcul de limite',steps,[r'\text{La limite bilatérale n\'existe pas}'])
        val = left
    else:
        val = s.limit(f,x,at,dir=side if side != '+-' else '+')
        steps = []
    steps.insert(0, step('Fonction étudiée', rf'f(x)={L(f)}'))
    steps.append(step('Résultat', rf'\lim_{{x\to {L(at)}}}{L(f)}={L(val)}'))
    return result('Calcul de limite', steps, [rf'\lim_{{x\to {L(at)}}}{L(f)}={L(val)}'])


def solve_function(data):
    f = read_expr(data)
    if f.free_symbols - {x}:
        raise ValueError('L’étude nécessite une fonction de x.')
    try:
        domain = continuous_domain(f, x, s.S.Reals)
    except (ValueError, NotImplementedError):
        domain = s.S.Reals
    d = s.factor(s.diff(f,x))
    try:
        critical = s.solveset(d, x, domain=domain)
    except Exception:
        critical = s.ConditionSet(x,s.Eq(d,0),domain)
    try:
        growing = s.solve_univariate_inequality(s.Gt(d,0), x, relational=False).intersect(domain)
        falling = s.solve_univariate_inequality(s.Lt(d,0), x, relational=False).intersect(domain)
    except (ValueError, NotImplementedError, TypeError):
        growing = falling = None
    steps = [step('Fonction',rf'f(x)={L(f)}'),
             step('Domaine de définition',rf'D_f={L(domain)}'),
             step('Dérivée factorisée',rf'f\prime(x)={L(d)}'),
             step('Points critiques',rf'f\prime(x)=0\;\Rightarrow\;x\in {L(critical)}')]
    if growing is not None:
        steps.append(step('Intervalles de croissance',rf'f\prime(x)>0\;\text{{sur}}\;{L(growing)}'))
        steps.append(step('Intervalles de décroissance',rf'f\prime(x)<0\;\text{{sur}}\;{L(falling)}'))
    if isinstance(critical,s.FiniteSet) and len(critical)<=8:
        for c in sorted(critical, key=s.default_sort_key):
            fc=s.simplify(f.subs(x,c))
            if fc.is_finite:
                steps.append(step('Valeur au point critique',rf'f({L(c)})={L(fc)}'))
    answers = [rf'D_f={L(domain)}',rf'f\prime(x)={L(d)}']
    if growing is not None:
        answers += [rf'\nearrow:\;{L(growing)}', rf'\searrow:\;{L(falling)}']
    return result('Étude de fonction', steps,answers,plot=series_plot(f))


def solve_system(data):
    raw = str(data.get('expression',''))
    parts=[p.strip() for p in raw.split(';') if p.strip()]
    if len(parts) not in (2,3):
        raise ValueError('Séparez 2 ou 3 équations par un point-virgule, par exemple : 2x+y=5; x-y=1')
    equations=[]
    for part in parts:
        if part.count('=') != 1:
            raise ValueError('Chaque équation doit contenir le signe =.')
        lhs,rhs=part.split('=')
        equations.append(s.Eq(parse_math(lhs),parse_math(rhs)))
    symbols=sorted(set().union(*(eq.free_symbols for eq in equations)), key=s.default_sort_key)
    if not set(symbols).issubset({x,y,z}) or len(symbols)>3:
        raise ValueError('Utilisez les inconnues x, y et éventuellement z.')
    sol=s.linsolve(equations,symbols) if all(s.Poly((eq.lhs-eq.rhs),*symbols).total_degree()<=1 for eq in equations) else s.nonlinsolve(equations,symbols)
    return result('Système d’équations',[
        step('Système',r'\begin{cases}'+r'\\'.join(L(eq) for eq in equations)+r'\end{cases}'),
        step('Ensemble des solutions', L(sol))], [L(sol)])


def solve_sequence(data):
    start=as_number(data.get('start','0'),'Le terme initial')
    rule=read_expr(data)
    if rule.free_symbols - {u}:
        raise ValueError('La récurrence doit utiliser u. Exemple : (u+3)/4')
    count=as_int(data.get('count', '6'),'Le nombre de termes',1,30)
    current=start
    steps=[step('Récurrence',rf'u_{{n+1}}={L(rule)},\quad u_0={L(start)}')]
    terms=[start]
    for k in range(1,count):
        current=s.simplify(rule.subs(u,current))
        if current.is_finite is not True or s.count_ops(current)>150:
            raise ValueError('La récurrence devient non définie ou trop volumineuse.')
        terms.append(current)
        steps.append(step(f'Terme u{k}',rf'u_{{{k}}}={L(rule.subs(u,terms[-2]))}={L(current)}'))
    return result('Suite définie par récurrence', steps, [rf'u_{{{i}}}={L(v)}' for i,v in enumerate(terms)])


def solve_statistics(data):
    text=str(data.get('expression',''))
    pieces=[p.strip() for p in re.split(r'[;,\s]+',text) if p.strip()]
    if not 2<=len(pieces)<=100:
        raise ValueError('Saisissez de 2 à 100 nombres séparés par des virgules ou points-virgules.')
    nums=[as_number(v,'Chaque donnée') for v in pieces]
    count=len(nums); mean=s.simplify(sum(nums)/count)
    variance=s.simplify(sum((v-mean)**2 for v in nums)/count)
    sorted_nums=sorted(nums, key=lambda v: float(v))
    median=(sorted_nums[(count-1)//2] if count%2 else s.simplify((sorted_nums[count//2-1]+sorted_nums[count//2])/2))
    steps=[step('Effectif',rf'N={count}'),step('Moyenne',rf'\bar x=\frac{{\sum x_i}}{{N}}={L(mean)}'),
           step('Variance (population)',rf'V=\frac{{\sum (x_i-\bar x)^2}}{{N}}={L(variance)}'),
           step('Écart-type',rf'\sigma=\sqrt{{V}}={L(s.sqrt(variance))}'),
           step('Médiane',rf'M_e={L(median)}')]
    return result('Statistiques descriptives',steps,[rf'\bar x={L(mean)}',rf'V={L(variance)}',rf'\sigma={L(s.sqrt(variance))}',rf'M_e={L(median)}'])


def solve_complex(data):
    f=read_expr(data)
    if f.free_symbols:
        raise ValueError('Saisissez un nombre complexe sans inconnue (ex : 3+4i).')
    f=s.simplify(s.expand_complex(f))
    a=s.simplify(s.re(f)); b=s.simplify(s.im(f)); modulus=s.simplify(s.Abs(f))
    arg=s.simplify(s.arg(f))
    steps=[step('Forme algébrique',rf'z={L(a)}+({L(b)})i'),
           step('Parties réelle et imaginaire',rf'\Re(z)={L(a)},\quad\Im(z)={L(b)}'),
           step('Module',rf'|z|=\sqrt{{({L(a)})^2+({L(b)})^2}}={L(modulus)}')]
    if f != 0:
        steps.append(step('Argument principal',rf'\arg(z)={L(arg)}'))
    return result('Nombres complexes',steps,[rf'z={L(f)}',rf'|z|={L(modulus)}'] + ([rf'\arg(z)={L(arg)}'] if f!=0 else []))


def solve_arithmetic(data):
    a=as_int(data.get('first','0'),'a',0,10**12)
    b=as_int(data.get('second','0'),'b',0,10**12)
    if a==0 and b==0:
        raise ValueError('Le PGCD de 0 et 0 est indéfini.')
    gcd=s.gcd(a,b); lcm=s.ilcm(a,b)
    steps=[step('Données',rf'a={a},\quad b={b}'),
           step('PGCD',rf'\operatorname{{PGCD}}({a},{b})={gcd}'),
           step('PPCM',rf'\operatorname{{PPCM}}({a},{b})={lcm}'),
           step('Identité',rf'\operatorname{{PGCD}}(a,b)\times\operatorname{{PPCM}}(a,b)=a\times b')]
    return result('Arithmétique',steps,[rf'PGCD={gcd}',rf'PPCM={lcm}'])


def solve_probability(data):
    nn=as_int(data.get('first','10'),'n',0,1000)
    kk=as_int(data.get('second','3'),'k',0,nn)
    p=as_number(data.get('point','0.5'),'La probabilité p',0,1)
    combination=s.binomial(nn,kk)
    prob=s.simplify(combination*p**kk*(1-p)**(nn-kk))
    steps=[step('Paramètres de la loi binomiale',rf'X\sim\mathcal{{B}}({nn},{L(p)})'),
           step('Nombre de combinaisons',rf'\binom{{{nn}}}{{{kk}}}={L(combination)}'),
           step('Probabilité ponctuelle',rf'P(X={kk})=\binom{{{nn}}}{{{kk}}}p^{{{kk}}}(1-p)^{{{nn-kk}}}={L(prob)}'),
           step('Espérance',rf'E(X)=np={L(nn*p)}')]
    return result('Loi binomiale',steps,[rf'P(X={kk})={L(prob)}',rf'E(X)={L(nn*p)}'])


def solve_finance(data):
    principal=as_number(data.get('first','100000'),'Capital initial',0)
    rate=as_number(data.get('point','5'),'Taux annuel (en %)',0,1000)
    years=as_int(data.get('second','3'),'Durée en années',0,100)
    t=rate/100
    simple=s.simplify(principal*(1+years*t))
    compound=s.simplify(principal*(1+t)**years)
    steps=[step('Données',rf'C_0={L(principal)},\quad t={L(t)},\quad n={years}'),
           step('Intérêts simples',rf'C_n=C_0(1+nt)={L(simple)}'),
           step('Intérêts composés',rf'C_n=C_0(1+t)^n={L(compound)}')]
    return result('Mathématiques financières', steps, [rf'C_{{simple}}={L(simple)}',rf'C_{{composé}}={L(compound)}'])


def solve(payload):
    if not isinstance(payload,dict):
        return {'ok':False,'error':'Données invalides.'}
    mode=str(payload.get('mode','auto'))
    if mode not in MODES:
        return {'ok':False,'error':'Mode de calcul non reconnu.'}
    try:
        if mode=='auto':
            raw=str(payload.get('expression',''))
            mode='inequation' if any(c in raw for c in ['<=','>=','<','>']) else ('equation' if '=' in raw and not re.match(r'\s*[fg]\(x\)\s*=',raw) else 'simplifier')
        handlers={'equation':solve_equation,'inequation':solve_inequation,
                  'derivee':solve_derivative,'integrale':solve_integral,
                  'limite':solve_limit,'fonction':solve_function,'systeme':solve_system,
                  'suite':solve_sequence,'statistiques':solve_statistics,
                  'complexes':solve_complex,'arithmetique':solve_arithmetic,
                  'probabilites':solve_probability,'finance':solve_finance}
        if mode in ('simplifier','factoriser','developper'):
            return solve_algebra(payload, mode)
        return handlers[mode](payload)
    except (ValueError, TypeError, s.SympifyError, ZeroDivisionError, OverflowError) as exc:
        return {'ok':False,'error':str(exc) or 'Impossible de résoudre cette saisie.'}
    except Exception:
        return {'ok':False,'error':'Ce problème dépasse les méthodes prises en charge. Essayez de préciser ou de simplifier la saisie.'}


def solve_json(payload_json):
    return json.dumps(solve(json.loads(payload_json)),ensure_ascii=False)
