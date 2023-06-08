"""
Name: Forgery plot
Author: RawFish
Github: https://github.com/RawFish69
Description: To calculate forgery mythic chance and generate plot
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def calculate_threshold_runs(chance_base, bonus, chance_thresholds):
    runs = 0
    chances = []
    cumulative_chances = []
    chance = chance_base
    cumulative_chance = chance
    while chance < max(chance_thresholds):
        chance = chance_base * (bonus ** runs)
        cumulative_chance += chance
        runs += 1
        chances.append(chance)
        cumulative_chances.append(cumulative_chance)
    run_counts = [np.searchsorted(chances, threshold) for threshold in chance_thresholds]
    cumulative_at_thresholds = [cumulative_chances[i] for i in run_counts]
    return runs, chances, cumulative_chances, run_counts, cumulative_at_thresholds

def print_runs_to_thresholds(run_counts, chance_thresholds, cumulative_at_thresholds, time_per_run):
    print("Title: Forgery mythic %")
    print("Author: RawFish\n")
    print("{:<15} {:<10} {:<15} {:<20} {:<20}".format('Threshold (%)', 'Runs', 'Cumulative (%)', 'Minutes', 'Hours'))
    print("-"*80)
    for i, run_count in enumerate(run_counts):
        hours = int(time_per_run*run_count/60)
        minutes = time_per_run*run_count
        cumulative = round(cumulative_at_thresholds[i], 2)
        print("{:<15} {:<10} {:<15.2f} {:<20} {:<20}".format(chance_thresholds[i], run_count, cumulative, minutes, hours))

def print_runs_to_thresholds_chinese(run_counts, chance_thresholds, cumulative_at_thresholds, time_per_run):
    print("标题: Forgery神话出货概率")
    print("作者: RawFish\n")
    print("{:<14} {:<8} {:<12} {:<18} {:<19}".format('阈值 (%)', '次数', '期望值(%)', '分钟', '小时'))
    print("-"*80)
    for i, run_count in enumerate(run_counts):
        hours = int(time_per_run*run_count/60)
        minutes = time_per_run*run_count
        cumulative = round(cumulative_at_thresholds[i], 2)
        print("{:<15} {:<10} {:<15.2f} {:<20} {:<20}".format(chance_thresholds[i], run_count, cumulative, minutes, hours))

def plot_chances(runs, chances, run_counts, chance_thresholds):
    plt.style.use('ggplot')
    plt.figure(figsize=(10, 6))

    x = np.arange(0, runs)
    plt.plot(x, chances, color='blue', label='Chance per run %')

    for i, run_count in enumerate(run_counts):
        plt.axvline(x=run_count, color='C{}'.format(i+2), ls='--', label=f'{chance_thresholds[i]}%')

    plt.title('Forgery %')
    plt.xlabel('Runs count')
    plt.ylabel('Chance %')
    plt.legend(loc="upper left")
    plt.grid(True)
    plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    plt.show()

def forgery():
    chance_base = 1.5
    bonus = 1.01
    chance_thresholds = [2.5, 10.0, 20.0, 40.0, 60.0, 80.0, 100.0]
    time_per_run = 45

    runs, chances, cumulative_chances, run_counts, cumulative_at_thresholds = calculate_threshold_runs(chance_base, bonus, chance_thresholds)

    print_runs_to_thresholds(run_counts, chance_thresholds, cumulative_at_thresholds, time_per_run)
    print()
    print_runs_to_thresholds_chinese(run_counts, chance_thresholds, cumulative_at_thresholds, time_per_run)
    plot_chances(runs, chances, run_counts, chance_thresholds)

forgery()
