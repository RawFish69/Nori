def hq_stats(link, ext):
    '''stats * (1 + 0.3 * links) * (1.5 + 0.25 * externals)'''
    # Assuming full 11 tower
    dmg_min = 5400
    dmg_max = 8100
    attack = 4.7
    health = 3300000
    defense = 0.9
    final_dmg_min = dmg_min * (1 + 0.3 * link) * (1.5 + 0.25 * ext)
    final_dmg_max = dmg_max * (1 + 0.3 * link) * (1.5 + 0.25 * ext)
    final_heatlh = health * (1 + 0.3 * link) * (1.5 + 0.25 * ext)
    final_dmg_avg = (final_dmg_min + final_dmg_max) / 2
    ehp = int(final_heatlh / (1 - defense))
    display = '```'
    display += 'Actual Tower Stats\n'
    display += f'Links: {link}, Externals: {ext}\n'
    display += f'Damage: {int(final_dmg_min)} - {int(final_dmg_max)}, average: {final_dmg_avg}\n'
    display += f'Attack: {attack}x per second\n'
    display += f'Health: {int(final_heatlh)}, EHP: {ehp} or {ehp/1000000}M\n'
    display += f'Defense: {defense * 100}%\n'
    display += '```'
    print(display)
    return display
