import numpy as np
from scipy.optimize import minimize
from platypus.algorithms import NSGAII, Problem
from platypus.core import nondominated
#from platypus.types import Real, Integer
from typing import List, Tuple, Callable

def multi_obj_optimization(fit_func: Callable[[np.ndarray, np.ndarray], Tuple[np.ndarray, ...]],
                           bounds: List[Tuple[float, float]],
                           weights: List[float],
                           maxNotMin: List[bool],
                           data: List[np.ndarray],
                           pop_size: int,
                           num_generations: int) -> List[Tuple[float, ...]]:   

    num_inputs = len(bounds)
    num_outputs = len(weights)
    num_datasets = len(data)

    # Define the problem for the optimization algorithm
    problem = Problem(num_inputs, num_outputs * num_datasets)
    problem.directions[:] = Problem.MAXIMIZE

    # Define the function to evaluate the fitness
    def evaluate_fitness(variables):
        objectives = []
        for d in data:
            # Evaluate the fitness for each dataset
            fitness = fit_func(variables, d)

            # Add the weighted objectives to the list
            for i in range(num_outputs):
                objectives.append(fitness[i] * weights[i])

        return tuple(objectives)
    
    # Define the function to evaluate the fitness
    def evaluate_fitness2(variables):
        objectives = []
        for d in data:
            # Evaluate the fitness for each dataset
            fitness = fit_func(variables, d)

            # Add the weighted objectives to the list
            for i in range(num_outputs):
                objectives.append(fitness[i] * weights[i])

        return tuple(objectives)

    for i in range(0, num_inputs):
        problem.types[i] = bounds[i]
        if maxNotMin[i]:
            problem.directions[i] = Problem.MAXIMIZE
        else:
            problem.directions[i] = Problem.MINIMIZE
    problem.function = evaluate_fitness

    # Use the NSGA-II algorithm for multi-objective optimization
    algorithm = NSGAII(problem)
    algorithm.population_size = pop_size
    algorithm.run(num_generations)
 
    return nondominated(algorithm.result)