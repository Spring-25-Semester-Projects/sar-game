### Search & Rescue Game

## Overview

The game forms a hexagonal map, in which traversal is affected by several factors that are not predetermined, and are also supposed to be free in nature. The survivors and the rescue teams, are both limited in resources.

## Non-Deterministic Behavior

Survivors are expected to act as rational agents, but not consistently. It is supposed that some survivors act as non-rational agents for some actions that they take, greatly influenced by the conditions in their enviroment. The behavior itself is non-deterministic, and as such not easily predictable.

## Search Path

Rescue teams will follow a path that is dependent on a depth-first algorithm, which will allow them to search the area with limited resources. They will not be able to readily survey any one portion of the map they have not traversed.

## Rescue Path

Rescuers must also take into account that survivors’ actions will determine how easily they can evacuate them, and as such the rescue path that they will assume will not be dependent on the search algorithm, but rather a weighted path-finding algorithm.

## Simulation

This game should be taken as a snapshot into the real-world considerations that a rescue team might take into account when attempting to rescue a potential survivor who has fought environmental conditions to be await their chance at being evacuated. The different environments will present different challenges, but each considerate or inconsiderate act has a disproportionate effect often on the chances of survival, regardless of how great an effort the rescue teams might endeavor to take.