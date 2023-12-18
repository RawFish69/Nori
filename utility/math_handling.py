import lightbulb
import scipy as sp
import hikari
import re
import matplotlib.pyplot as plt
import numpy as np

# Previous code from math command group...
# Sample code segment for handling derivative calculation and plotting

@math.child()
@lightbulb.option("graph", "Show graph (beta)", required=False, choices=["Yes", "No"])
@lightbulb.option("function", "Function to differentiate")
@lightbulb.command("derivative", "Differentiate a function")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def derivative(ctx):
    print("Inside derivative function...")
    function_str = ctx.options.function
    derivative_embed = hikari.Embed(title=f"Evaluating equation: `{function_str}`")
    await ctx.respond(embed=derivative_embed)
    x = sp.symbols('x')
    try:
        expr = sp.sympify(safe_math_expr(function_str))
        result = sp.diff(expr, x)
        result_str = sp.pretty(result, use_unicode=True)
        response = f"Derivative of `{function_str}`"
        if ctx.options.graph and ctx.options.graph == "Yes":
            file_name = plot_function(result, (-10, 10), ctx.user.username)
            derivative_embed = hikari.Embed(title=response, description=f"```{result_str}```", color="#3384FF")
            derivative_embed.add_field("Text format", f"`{result}`")
            derivative_embed.set_footer("Nori Bot - Derivative Calculator")
            await ctx.edit_last_response(embed=derivative_embed, attachment=f"user_img/{file_name}")
        else:
            derivative_embed = hikari.Embed(title=response, description=f"```{result_str}```", color="#3384FF")
            derivative_embed.add_field("Text format", f"`{result}`")
            derivative_embed.set_footer("Nori Bot - Derivative Calculator")
            await ctx.edit_last_response(embed=derivative_embed)
    except Exception as e:
        print(f"Error in derivative function: {e}")
        response = f"Error: Unable to evaluate {function_str}."
        derivative_embed = hikari.Embed(title=response)
        await ctx.edit_last_response(embed=derivative_embed)


def safe_math_expr(expr_str: str):

    expr_str = expr_str.replace('^', '**')

    expr_str = re.sub(r'e\*\*([(][^)]+[)])', lambda m: 'exp' + m.group(1), expr_str)

    expr_str = re.sub(r'log\(([^)]+)\)', r'log(\1, 10)', expr_str)

    expr_str = expr_str.replace('ln(', 'log(')

    expr_str = re.sub(r'([a-zA-Z])(\d+)', r'\1*\2', expr_str)
    expr_str = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr_str)

    valid_chars = set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+*-. /()**,")
    if any(char not in valid_chars for char in expr_str):
        raise ValueError("Invalid characters in input!")

    return expr_str


def plot_function(expr, x_range, user_name):
    print(expr, x_range)
    x = sp.symbols('x')
    try:
        f = sp.lambdify(x, expr, modules=["numpy"])
    except Exception as e:
        print(f"Error during lambdification: {e}")
        return None
    x_vals = np.linspace(x_range[0], x_range[1], 400)
    try:
        y_vals = f(x_vals)
    except Exception as e:
        print(f"Error during function evaluation: {e}")
        return None

    # Plotting
    plt.figure(figsize=(8, 7))
    plt.plot(x_vals, y_vals, label=f"Nori Bot - Plot", color='royalblue', linewidth=2)
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.axhline(y=0, color='black', linewidth=0.5)
    plt.axvline(x=0, color='black', linewidth=0.5)

    # Title adjustment
    title_str = f"{sp.pretty(expr, use_unicode=True)}"
    if len(title_str) > 50:
        title_str = title_str[:50] + "..."
    plt.title(title_str, fontsize=10, pad=15)
    plt.legend(loc="upper left")
    plt.xlabel(f"x-axis\nRequested by {user_name}")
    plt.ylabel("y-axis")
    file_name = f"plot_{user_name}.png"
    plt.savefig(f"/home/ubuntu/nori-bot/data/output/user_img/{file_name}")
    plt.close()
    return file_name