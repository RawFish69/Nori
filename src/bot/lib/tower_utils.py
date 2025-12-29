"""
Tower calculation utility functions for Nori bot.

This module contains functions for calculating guild tower statistics
for both HQ (Headquarters) and regular towers.
"""
from typing import Tuple


def hq_stats(link: int, ext: int, dmg_level: int, attack_level: int, hp_level: int, def_level: int) -> str:
    """
    Calculate HQ tower statistics.

    Formula: stats * (1 + 0.3 * links) * (1.5 + 0.25 * externals)

    Args:
        link: Number of tower links
        ext: Number of externals
        dmg_level: Damage level (0-11)
        attack_level: Attack level (0-11)
        hp_level: Health level (0-11)
        def_level: Defense level (0-11)

    Returns:
        Formatted string with tower statistics
    """
    dmg_min = [1000, 1400, 1800, 2200, 2600, 3000, 3400, 3800, 4200, 4600, 5000, 5400]
    dmg_max = [1500, 2100, 2700, 3300, 3900, 4500, 5100, 5700, 6300, 6900, 7500, 8100]
    attack = [0.5, 0.75, 1.0, 1.25, 1.6, 2.0, 2.5, 3.0, 3.6, 3.8, 4.2, 4.7]
    health = [300000, 450000, 600000, 750000, 960000, 1200000, 1500000, 1860000, 2220000, 2580000, 2940000, 3300000]
    defense = [0.1, 0.4, 0.55, 0.625, 0.7, 0.75, 0.79, 0.82, 0.84, 0.86, 0.88, 0.9]
    
    final_dmg_min = dmg_min[dmg_level] * (1 + 0.3 * link) * (1.5 + 0.25 * ext)
    final_dmg_max = dmg_max[dmg_level] * (1 + 0.3 * link) * (1.5 + 0.25 * ext)
    final_health = health[hp_level] * (1 + 0.3 * link) * (1.5 + 0.25 * ext)
    final_dmg_avg = (final_dmg_min + final_dmg_max) / 2
    ehp = int(final_health / (1 - defense[def_level]))
    
    display = ''
    display += f'Damage: {int(final_dmg_min)} - {int(final_dmg_max)}, average: {round(final_dmg_avg, 2)} per hit\n'
    display += f'Attack: {attack[attack_level]}x per second, avg DPS: {round(final_dmg_avg * attack[attack_level], 2)}\n'
    display += f'Health: {int(final_health)}, EHP: {ehp} or {round(ehp / 1000000, 2)}M\n'
    display += f'Defense: {defense[def_level] * 100}%\n'
    
    print(display)
    return display


def tower_stats(link: int, dmg_level: int, attack_level: int, hp_level: int, def_level: int) -> str:
    """
    Calculate regular tower statistics.

    Formula: stats * (1 + 0.3 * links)

    Args:
        link: Number of tower links
        dmg_level: Damage level (0-11)
        attack_level: Attack level (0-11)
        hp_level: Health level (0-11)
        def_level: Defense level (0-11)

    Returns:
        Formatted string with tower statistics
    """
    dmg_min = [1000, 1400, 1800, 2200, 2600, 3000, 3400, 3800, 4200, 4600, 5000, 5400]
    dmg_max = [1500, 2100, 2700, 3300, 3900, 4500, 5100, 5700, 6300, 6900, 7500, 8100]
    attack = [0.5, 0.75, 1.0, 1.25, 1.6, 2.0, 2.5, 3.0, 3.6, 3.8, 4.2, 4.7]
    health = [300000, 450000, 600000, 750000, 960000, 1200000, 1500000, 1860000, 2220000, 2580000, 2940000, 3300000]
    defense = [0.1, 0.4, 0.55, 0.625, 0.7, 0.75, 0.79, 0.82, 0.84, 0.86, 0.88, 0.9]
    
    final_dmg_min = dmg_min[dmg_level] * (1 + 0.3 * link)
    final_dmg_max = dmg_max[dmg_level] * (1 + 0.3 * link)
    final_health = health[hp_level] * (1 + 0.3 * link)
    final_dmg_avg = (final_dmg_min + final_dmg_max) / 2
    ehp = int(final_health / (1 - defense[def_level]))
    
    display = ''
    display += f'Damage: {int(final_dmg_min)} - {int(final_dmg_max)}, average: {round(final_dmg_avg, 2)} per hit\n'
    display += f'Attack: {attack[attack_level]}x per second, avg DPS: {round(final_dmg_avg * attack[attack_level], 2)}\n'
    display += f'Health: {int(final_health)}, EHP: {ehp} or {round(ehp / 1000000, 2)}M\n'
    display += f'Defense: {defense[def_level] * 100}%\n'
    
    print(display)
    return display

