# Nori-Wynn Docs
## Intro to Guild Tower 

## Overview

How to calculate guild tower stats, including damage, attack rate, health, and defense, based on different upgrade levels and bonuses. The calculations consider the effects of links between territories and external connections to the headquarters.

## Base Stats

Each guild tower starts with a set of base stats:

- **Damage**: The amount of damage a tower deals per hit.
  - Base Damage Range: 1000 - 1500
- **Attack Rate**: The number of attacks per second.
  - Base Attack Rate: 0.5 attacks per second
- **Health**: The total health points of the tower.
  - Base Health: 300,000 HP
- **Defense**: The percentage of damage reduction.
  - Base Defense: 10%

## Upgrades and Their Effects

Upgrades improve the tower’s stats. Each upgrade level corresponds to a specific value increase. The values used in the calculations are:

- **Damage Upgrade Levels**: 0 to 4.4
- **Attack Rate Upgrade Levels**: 0 to 8.4
- **Health Upgrade Levels**: 0 to 10.0
- **Defense Upgrade Levels**: 0 to 8.0

Variables expression in JavaScript:
```javascript
const baseDmg = { low: 1000, high: 1500 };
const baseAtk = 0.5;
const baseHp = 300000;
const baseDef = 0.1;
const hqBonusBase = 0.5;
const hqBonusPerTerritory = 0.25;
const connectionBonus = 0.3;
const Dmg = [0, 0.4, 0.8, 1.2, 1.6, 2.0, 2.4, 2.8, 3.2, 3.6, 4.0, 4.4];
const Atk = [0, 0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.0, 6.2, 6.6, 7.4, 8.4];
const Hp = [0, 0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.2, 6.4, 7.6, 8.8, 10.0];
const Def = [0, 3, 4.50, 5.25, 6.00, 6.50, 6.90, 7.20, 7.40, 7.60, 7.80, 8.00];
```

## Bonuses

Two main bonuses affect the tower’s stats:

1. **Link Bonus**: Bonus gained from linking territories.
   - Each link adds a 30% increase to the base value.
2. **External Connection Bonus**: Bonus gained from connections to the headquarters.
   - Base Headquarters Bonus: 50%
   - Each external territory adds a 25% increase.

## Calculation Formulas

### Headquarters (HQ) Towers

The stats for headquarters towers are calculated by scaling the base stats with both link bonuses and external connection bonuses.

- **Damage Calculation**:
  - Minimum Damage:
    ```
    dmg_min = base_dmg_low * (1 + 0.3 * link) * (1.5 + 0.25 * ext)
    ```
  - Maximum Damage:
    ```
    dmg_max = base_dmg_high * (1 + 0.3 * link) * (1.5 + 0.25 * ext)
    ```
  - Average Damage:
    ```
    dmg_avg = (dmg_min + dmg_max) / 2
    ```

- **Health Calculation**:
    ```
    health = base_hp * (1 + 0.3 * link) * (1.5 + 0.25 * ext)
    ```

### Regular Towers

The stats for regular towers are calculated by scaling the base stats with link bonuses only.

- **Damage Calculation**:
    - Minimum Damage:
    ```
    dmg_min = base_dmg_low * (1 + 0.3 * link)
    ```
    - Maximum Damage:
    ```
    dmg_max = base_dmg_high * (1 + 0.3 * link)
    ```
    - Average Damage:
    ```
    dmg_avg = (dmg_min + dmg_max) / 2
    ```
    
- **Health Calculation**:
    ```
    health = base_hp * (1 + 0.3 * link)
    ```

### Attack Rate:
    atk_rate = base_atk_rate + valAtk[attackLevel]

### Defense Calculation:
    defense = defense[defLevel]

## Example Calculation

Consider a headquarters tower with the following parameters:
- **Links**: 2
- **External Connections**: 3
- **Damage Upgrade Level**: 5
- **Attack Rate Upgrade Level**: 4
- **Health Upgrade Level**: 6
- **Defense Upgrade Level**: 7

1. **Calculate Damage**:
 - Minimum Damage: `1000 * (1 + 0.3 * 2) * (1.5 + 0.25 * 3) = 1000 * 1.6 * 2.25 = 3600`

 - Maximum Damage: `1500 * (1 + 0.3 * 2) * (1.5 + 0.25 * 3) = 1500 * 1.6 * 2.25 = 5400`

 - Average Damage: `(3600 + 5400) / 2 = 4500`

2. **Calculate Health**:
    - health = `300000 * (1 + 0.3 * 2) * (1.5 + 0.25 * 3) = 300000 * 1.6 * 2.25 = 1,080,000 HP`

Now, consider a regular tower with the same parameters but without external connections:

3. **Calculate Damage**:
- Minimum Damage: `1000 * (1 + 0.3 * 2) = 1000 * 1.6 = 1600`
- Maximum Damage: `1500 * (1 + 0.3 * 2) = 1500 * 1.6 = 2400`
- Average Damage: `(1600 + 2400) / 2 = 2000`

4. **Calculate Health**:
health = `300000 * (1 + 0.3 * 2) = 300000 * 1.6 = 480,000 HP`

5. **Calculate Defense**:
defense = `defense[7] * 100 = 82%`

## Summary

By following the above steps, you can calculate the guild tower stats based on upgrades and bonuses. This process ensures that you accurately determine the tower’s damage, attack rate, health, and defense, taking into account the effects of links and external connections.

# Territory Tier (Difficulty) Calculation

How to calculate the rating and determine the tier for a given set of attributes (`dmg`, `atk`, `hp`, `def`, `aura`, and `volley`). The tier is determined based on the rating calculated from these attributes.

## Rating Calculation

The rating is calculated using the following formula:

rating = (dmg + atk + hp + def) + (aura + volley) + 5 * (aura > 0) + 3 * (volley > 0)

| Tier | Rating| Difficulty |
|----------|----------|----------|
| 1 | 0 - 5 | Very Low |
| 2 | 6 - 18 | Low |
| 3 | 19 - 30 | Medium |
| 4 | 31 - 48 | High |
| 5 | 49+ | Very High |

### Explanation:

- `dmg`, `atk`, `hp`, `def` are integer values ranging from 0 to 11.
- `aura`, `volley` are integer values ranging from 0 to 3.
- If `aura` is greater than 0, an additional 5 points are added to the rating.
- If `volley` is greater than 0, an additional 3 points are added to the rating.

## Tier Determination

The tier is determined based on the rating using the following equation:

tier = 1 + (rating > 5) + (rating > 18) + (rating > 30) + (rating > 48)

- Note: HQ will have an additional tier, the highest tier still caps at 5.

### Explanation:

- The term `(rating > 5)` is 1 if the rating exceeds 5, and 0 otherwise.
- The term `(rating > 18)` is 1 if the rating exceeds 18, and 0 otherwise.
- The term `(rating > 30)` is 1 if the rating exceeds 30, and 0 otherwise.
- The term `(rating > 48)` is 1 if the rating exceeds 48, and 0 otherwise.

### Full Equation:

rating = (dmg + atk + hp + def) + (aura + volley) + 5 * (aura > 0) + 3 * (volley > 0)
tier = 1 + (rating > 5) + (rating > 18) + (rating > 30) + (rating > 48)

Where `(rating > x)` is an indicator function that returns 1 if the condition inside is true, and 0 otherwise.

## Example

Given the following attribute values:
- `dmg = 10`
- `atk = 8`
- `hp = 7`
- `def = 6`
- `aura = 2`
- `volley = 1`
- `HQ = False`

### Calculation:

rating = (10 + 8 + 7 + 6) + (2 + 1) + 5 * (2 > 0) + 3 * (1 > 0)
rating = 31 + 3 + 5 + 3
rating = 42

### Tier Determination:

tier = 1 + (rating > 5) + (rating > 18) + (rating > 30) + (rating > 48)
tier = 1 + 1 + 1 + 1 + 0
tier = 4

The tier for these attribute values is 4 (High).

### Credits: RawFish, mahakadema, anAlarmingAlarm
