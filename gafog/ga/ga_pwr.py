from deap import base, creator, tools, algorithms
import random
from ..fog_problem.problem_pwr import ProblemPwr
from .fogindividual import FogIndividual


def solve_problem_pwr(problem):
    cxbp = 0.5
    mutpb = 0.3
    problem.begin_solution()
    toolbox = init_ga_pwr(problem)
    sol = solve_ga_simple(toolbox, cxbp, mutpb, problem)
    problem.end_solution()
    sol.register_execution_time()
    return sol

def init_ga_pwr(problem):
    # Initialization
    toolbox = base.Toolbox()
    try:
        del creator.FitnessMin
        del creator.Individual
    except AttributeError:
        pass
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMin)
    toolbox.register("individual", init_pwr, creator.Individual, nfog=5, nfog_on=2, nservices=5, problem=problem)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    toolbox.register("evaluate", obj_func, problem=problem)
    toolbox.register("mate", cx_solution_pwr, indpb=0.5, problem=problem)
    toolbox.register("mutate", mut_shuffle_pwr, indpb=0.05, problem=problem)
    toolbox.register("select", tools.selTournament, tournsize=7)
    return toolbox

def normalize_individual(ind, problem: Problem):
    """ Removes unneeded elements from chromosome. Modification occurs in place """
    # remove last gene if it is a fog
    nsrv=problem.get_nservice()
    to_remove=[]
    #print(ind)
    if is_fog(ind[-1], nsrv):
        to_remove.append(len(ind)-1)
    prv_fog=True
    for i in range(1, len(ind)):
        if is_fog(ind[i], nsrv) and prv_fog:
            to_remove.append(i-1)
        prv_fog = is_fog(ind[i], nsrv)
        #print(i, ind[i], to_remove)
    print(ind, to_remove)
    for i in to_remove:
        ind.pop(i)
    return ind

def obj_func(individual, problem: ProblemPwr):
    sol = problem.get_solution(individual, problem)
    return sol.obj_func(),

def load_individuals(creator, problem: Problem):
    individual = list()
    for i in range(problem.get_nservice()):
        individual.append(random.randint(0, problem.get_nfog() - 1))
    return creator(individual)

def cx_solution_pwr(ind1, ind2, problem: Problem):
    """
    Implements ordered crossover (OX2) for parents of different lengths, making sure that the first elements reimains untouched
    """
    size = min(len(ind1), len(ind2))  # Use the minimum length
    
    # Choose random start/end position for crossover. First element is never touched
    start, end = sorted([random.randrange(size-1)+1 for _ in range(2)])
    
    # Initialize children with placeholders
    child1, child2 = [None] * len(ind2), [None] * len(ind1)
    
    # Copy ind1's sequence for child1 and ind2's sequence for child2
    child1[start:end + 1] = ind1[start:end + 1]
    child2[start:end + 1] = ind2[start:end + 1]
    child1[0]=ind2[0]
    child2[0]=ind1[0]
    # Fill remaining positions of child1
    for i in range(1,len(ind2)):
        if i < start or i > end:
            # Avoid repetitions
            if ind2[i] not in child1:
                child1[i] = ind2[i]
            else:
                # Find the next available value from dad
                for j in range(len(ind2)):
                    if ind2[j] not in child1:
                        child1[i] = ind2[j]
                        break

    # Fill remaining positions of child2
    for i in range(1,len(ind1)):            
            if ind1[i] not in child2:
                child2[i] = ind1[i]
            else:
                # Find the next available value from mum
                for j in range(len(ind1)):
                    if ind1[j] not in child2:
                        child2[i] = ind1[j]
                        break
    # make changes in place
    for i in range(len(child1)):
        ind2[i]=child1[i]
    for i in range(len(child2)):
        ind1[i]=child2[i]
    normalize_individual(ind1, problem)
    normalize_individual(ind2, problem)
    return ind1, ind2

def init_pwr(nfog=5, nfog_on=2, nservices=5):
    min_service=0
    max_service=nservices
    services = list(range(min_service, max_service))
    #print(services)
    #print(list(range(max_service, max_service+nfog)))
    fogs=random.sample(list(range(max_service, max_service+nfog)), nfog_on)
    #print(fogs)
    # First chromosome must always be a fog ID
    rv=services+fogs[1:]
    random.shuffle(rv)
    return fogs[0:1] + rv

def is_fog(g, nsrv):
    return g>=nsrv

def individual_to_chains(individual, problem: Problem):
    chains=[]
    size = len(individual)
    nsrv = problem.get_nservice()
    for i in range(size):
        if is_fog(individual[i], nsrv):
            ch={'fog': individual[i], 'services': []}
            chains.append(ch)
        else:
            ch['services'].append(individual[i])
    return chains

def chains_to_individual(chains):
    individual = []
    for ch in chains:
        individual += [ch['fog']]+ch['services']
    return individual

def mut_del_fog(individual, indpb, problem: Problem):
    chains=individual_to_chains(individual, problem)
    ch_to_remove=[]
    for i, ch in enumerate(chains):
        if random.random() < indpb:
            ch_to_remove.append(i)
            # FIXME: move microservices to other fog ndoes
            for s in ch['services']:
                newfog = random.randint(0,len(chains))
                while newfog in ch_to_remove:
                    newfog = random.randint(0,len(chains))
                chains[i]['services'].append(s)
    for i in ch_to_remove:
        chains.pop(i)
    return individual,    

def mut_add_fog(individual, indpb, problem: Problem):
    pass
    # find list of off services
    # decide which fog to add
    # populate the fog

def mut_shuffle_pwr(individual, indpb, problem: Problem):
    """
    :param individual: Individual to be mutated.
    :param indpb: Independent probability for each attribute to be exchanged to
                  another position.
    :returns: A tuple of one individual.
    """

    size = len(individual)
    # mutate first element: it must be a fog node!
    nsrv = problem.get_nservice()
    if random.random() < indpb:
            idx_fogs=[i for i in range(size) if is_fog(individual[i], nsrv)]
            swap_indx = random.randint(1, len[idx_fogs]-1)
            individual[0], individual[swap_indx] = individual[swap_indx], individual[0]
    for i in range(1, size):
        if random.random() < indpb:
            swap_indx = random.randint(0, size - 2)
            if swap_indx >= i:
                swap_indx += 1
            individual[i], individual[swap_indx] = individual[swap_indx], individual[i]

    return normalize_individual(individual),
