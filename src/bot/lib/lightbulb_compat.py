"""Small helpers for lightbulb v3 command declarations."""

import lightbulb


def lb_choices(values):
    return [lightbulb.Choice(str(value), value) for value in values]
