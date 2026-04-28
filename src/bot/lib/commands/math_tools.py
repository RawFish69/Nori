"""Math command group."""
import re
import hikari
import lightbulb
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp
from lib.config import USER_IMG_PATH
from lib.lightbulb_compat import lb_choices
loader = lightbulb.Loader()

def safe_math_expr(expr_str: str):
    """Pre-process and safely handle the math expression for better user input."""
    expr_str = expr_str.replace('^', '**')
    expr_str = re.sub('e\\*\\*([(][^)]+[)])', lambda match: 'exp' + match.group(1), expr_str)
    expr_str = re.sub('log\\(([^)]+)\\)', 'log(\\1, 10)', expr_str)
    expr_str = expr_str.replace('ln(', 'log(')
    expr_str = re.sub('([a-zA-Z])(\\d+)', '\\1*\\2', expr_str)
    expr_str = re.sub('(\\d)([a-zA-Z])', '\\1*\\2', expr_str)
    valid_chars = set('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+*-. /()**,')
    if any((char not in valid_chars for char in expr_str)):
        raise ValueError('Invalid characters in input!')
    return expr_str

def plot_function(expr, x_range, user_name):
    """Plot a function and return the generated file path."""
    x = sp.symbols('x')
    try:
        func = sp.lambdify(x, expr, modules=['numpy'])
    except Exception as error:
        print(f'Error during lambdification: {error}')
        return None
    x_vals = np.linspace(x_range[0], x_range[1], 400)
    try:
        y_vals = func(x_vals)
    except Exception as error:
        print(f'Error during function evaluation: {error}')
        return None
    plt.figure(figsize=(8, 7))
    plt.plot(x_vals, y_vals, label='Nori Bot - Plot', color='royalblue', linewidth=2)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.axhline(y=0, color='black', linewidth=0.5)
    plt.axvline(x=0, color='black', linewidth=0.5)
    title_str = f'{sp.pretty(expr, use_unicode=True)}'
    if len(title_str) > 50:
        title_str = title_str[:50] + '...'
    plt.title(title_str, fontsize=10, pad=15)
    plt.legend(loc='upper left')
    plt.xlabel(f'x-axis\nRequested by {user_name}')
    plt.ylabel('y-axis')
    math_path = USER_IMG_PATH / 'math'
    math_path.mkdir(parents=True, exist_ok=True)
    file_name = f'plot_{user_name}.png'
    full_path = math_path / file_name
    plt.savefig(full_path)
    plt.close()
    return full_path
math = lightbulb.Group('math', 'Mathematical operations')

@math.register
class PlotMake(lightbulb.SlashCommand, name='plot', description='Generate plot'):
    expr = lightbulb.string('expr', 'function')

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        user = await ctx.client.app.rest.fetch_user(ctx.user.id)
        username = user.username
        img_embed = hikari.Embed(title='Generating plot based on input')
        await ctx.respond(embed=img_embed)
        param_x = self.expr
        x = sp.symbols('x')
        try:
            expr = sp.sympify(safe_math_expr(param_x))
        except Exception as error:
            await ctx.respond(f'Error processing expression: {error}')
            return
        x_vals = np.linspace(-10, 10, 400)
        y_vals = [float(expr.subs(x, val)) if expr.subs(x, val).is_real else float('nan') for val in x_vals]
        abs_y_max = np.nanmax(np.abs(y_vals))
        if abs_y_max > 1000:
            x_min, x_max = (-100, 100)
        elif abs_y_max < 0.1:
            x_min, x_max = (-5, 5)
        else:
            x_min, x_max = (-10, 10)
        x_vals = np.linspace(x_min, x_max, 400)
        y_vals = [float(expr.subs(x, val)) if expr.subs(x, val).is_real else float('nan') for val in x_vals]
        y_min, y_max = (np.nanmin(y_vals), np.nanmax(y_vals))
        y_margin = 0.1 * (y_max - y_min) if y_max != y_min else 1
        plt.ylim(y_min - y_margin, y_max + y_margin)
        plt.title(f'Requested by {username}')
        plt.plot(x_vals, y_vals)
        math_path = USER_IMG_PATH / 'math'
        math_path.mkdir(parents=True, exist_ok=True)
        file_name = f'plot_{username}.png'
        full_path = math_path / file_name
        plt.savefig(full_path)
        plt.close()
        image_generated = hikari.files.File(str(full_path))
        img_embed = hikari.Embed(title='Plot generated', description=f'Equation: {param_x}', color='#3384FF')
        img_embed.set_image(image_generated)
        img_embed.set_footer('Nori Bot - Plot Generator')
        await ctx.edit_response(-1, embed=img_embed)
        plt.clf()

@math.register
class Calculate(lightbulb.SlashCommand, name='calculate', description='Evaluate a mathematical expression'):
    expr = lightbulb.string('expr', 'Mathematical expression')

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        expr_str = self.expr
        try:
            solution = sp.sympify(safe_math_expr(expr_str)).evalf()
            result = str(solution)
            await ctx.respond(f'`{expr_str} = {result}`')
        except Exception as error:
            await ctx.respond(f'Error: {str(error)}')

@math.register
class Solve(lightbulb.SlashCommand, name='solve', description='Solve an equation'):
    equation = lightbulb.string('equation', 'Equation to solve')

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        equation_str = self.equation
        solve_embed = hikari.Embed(title=f'Evaluating equation: `{equation_str}`')
        await ctx.respond(embed=solve_embed)
        x = sp.symbols('x')
        try:
            if '=' not in equation_str:
                solve_embed = hikari.Embed(title="Needs to be an equation with an '=' sign.")
                await ctx.edit_response(-1, embed=solve_embed)
                return
            lhs, rhs = equation_str.split('=')
            equation = sp.Eq(sp.sympify(safe_math_expr(lhs)), sp.sympify(safe_math_expr(rhs)))
            solution = sp.nsolve(equation, x, 0)
            result = str(solution)
            solve_embed = hikari.Embed(title='Equation Solver', color='#3384FF')
            solve_embed.add_field('Given equation', f'`{equation_str}`\n**Solution**: `x = {result}`')
            solve_embed.set_footer('Nori Bot - Equation Solver')
            await ctx.edit_response(-1, embed=solve_embed)
        except Exception as error:
            print(f'Error in solve function: {error}')
            solve_embed = hikari.Embed(title=f'Error occurred while evaluating `{equation_str}`')
            await ctx.edit_response(-1, embed=solve_embed)

@math.register
class Integrate(lightbulb.SlashCommand, name='integral', description='Integrate a function'):
    function = lightbulb.string('function', 'Function to integrate')
    graph = lightbulb.string('graph', 'Show graph (beta)', choices=lb_choices(['Yes', 'No']), default=None)

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        function_str = self.function
        integral_embed = hikari.Embed(title=f'Evaluating integral: `{function_str}`')
        await ctx.respond(embed=integral_embed)
        x = sp.symbols('x')
        try:
            formatted_function = re.sub('(\\d*)x\\^(\\d+)', '\\1x**\\2', function_str)
            formatted_function = re.sub('(\\d+)x', '\\1*x', formatted_function)
            formatted_function = re.sub('x\\^(\\d+)', 'x**\\1', formatted_function)
            expr = sp.sympify(formatted_function)
            result = sp.integrate(expr, x)
            if isinstance(result, sp.Integral):
                integral_embed = hikari.Embed(title=f'Unable to evaluate the integral of `{function_str}`.', color='#3384FF')
                await ctx.edit_response(-1, embed=integral_embed)
                return
            result_str = sp.pretty(result, use_unicode=True)
            response = f'Integral of `{function_str}`'
            if self.graph and self.graph == 'Yes':
                file_path = plot_function(result, (-10, 10), ctx.user.username)
                if not file_path:
                    await ctx.edit_response(-1, 'Unable to generate graph.')
                    return
                image_generated = hikari.files.File(str(file_path))
                integral_embed = hikari.Embed(title=response, description=f'```{result_str}```', color='#3384FF')
                integral_embed.add_field('Text Format', f'`{result}`')
                integral_embed.set_image(image_generated)
                integral_embed.set_footer('Nori Bot - Integral Calculator')
                await ctx.edit_response(-1, embed=integral_embed)
            else:
                integral_embed = hikari.Embed(title=response, description=f'```{result_str}```', color='#3384FF')
                integral_embed.add_field('Text Format', f'`{result}`')
                integral_embed.set_footer('Nori Bot - Integral Calculator')
                await ctx.edit_response(-1, embed=integral_embed)
        except Exception as error:
            print(f'Error in integrate function: {error}')
            integral_embed = hikari.Embed(title=f'Error: Unable to evaluate {function_str}.')
            await ctx.edit_response(-1, embed=integral_embed)

@math.register
class Derivative(lightbulb.SlashCommand, name='derivative', description='Differentiate a function'):
    function = lightbulb.string('function', 'Function to differentiate')
    graph = lightbulb.string('graph', 'Show graph (beta)', choices=lb_choices(['Yes', 'No']), default=None)

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        function_str = self.function
        derivative_embed = hikari.Embed(title=f'Evaluating equation: `{function_str}`')
        await ctx.respond(embed=derivative_embed)
        x = sp.symbols('x')
        try:
            expr = sp.sympify(safe_math_expr(function_str))
            result = sp.diff(expr, x)
            result_str = sp.pretty(result, use_unicode=True)
            response = f'Derivative of `{function_str}`'
            if self.graph and self.graph == 'Yes':
                file_path = plot_function(result, (-10, 10), ctx.user.username)
                if not file_path:
                    await ctx.edit_response(-1, 'Unable to generate graph.')
                    return
                derivative_embed = hikari.Embed(title=response, description=f'```{result_str}```', color='#3384FF')
                derivative_embed.add_field('Text format', f'`{result}`')
                derivative_embed.set_footer('Nori Bot - Derivative Calculator')
                await ctx.edit_response(-1, embed=derivative_embed, attachment=hikari.files.File(str(file_path)))
            else:
                derivative_embed = hikari.Embed(title=response, description=f'```{result_str}```', color='#3384FF')
                derivative_embed.add_field('Text format', f'`{result}`')
                derivative_embed.set_footer('Nori Bot - Derivative Calculator')
                await ctx.edit_response(-1, embed=derivative_embed)
        except Exception as error:
            print(f'Error in derivative function: {error}')
            derivative_embed = hikari.Embed(title=f'Error: Unable to evaluate {function_str}.')
            await ctx.edit_response(-1, embed=derivative_embed)
loader.command(math)
