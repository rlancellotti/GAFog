from deap import base, creator, tools, algorithms
import random
from ..fog_problem.problem_pwr import ProblemPwr


def init_ga(problem: ProblemPwr):
    # Initialization
    print('call to init_ga[pwr]')
    toolbox = base.Toolbox()
    try:
        del creator.FitnessMin
        del creator.Individual
    except AttributeError:
        pass
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMin)
    toolbox.register("individual", load_individuals, creator.Individual, problem=problem)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    toolbox.register("evaluate", obj_func, problem=problem)
    toolbox.register("mate", cx_solution_pwr, problem=problem)
    toolbox.register("mutate", mut_shuffle_pwr, indpb=0.05, problem=problem)
    toolbox.register("select", tools.selTournament, tournsize=7)
    return toolbox

def normalize_individual(ind, problem: ProblemPwr):
    """ Removes unneeded elements from chromosome. Modification occurs in place """
    # remove last gene if it is a fog
    ind_ok=check_individual_correct(ind, problem)
    old_individual=ind[:]
    nsrv=problem.get_nservice()
    to_remove=[] #NOTE: to_remove contains indexes!
    #print(ind)
    if is_fog(ind[-1], nsrv):
        to_remove.append(len(ind)-1)
    prv_fog=True
    for i in range(1, len(ind)):
        if ind[i] is None:
            to_remove.append(i)
        if is_fog(ind[i], nsrv) and prv_fog:
            to_remove.append(i-1)
        prv_fog = is_fog(ind[i], nsrv)
        #print(i, ind[i], to_remove)
    #print(ind, to_remove)
    for i in to_remove:
        ind.pop(i)
    if ind_ok and not check_individual_correct(ind, problem):
        print(f'*** normalize_individual generating error: {old_individual} -> {ind}')
    return ind

def check_individual_correct(individual, problem: ProblemPwr, print_warning=False):
    rv=True
    # check if first element is a fog
    nsrv=problem.get_nservice()
    if not is_fog(individual[0], nsrv):
        return False
    # check for none values
    if None in individual:
        rv=False
    # check for duplicates
    if len(individual) != len (set(individual)):
        rv=False
    for s in range(nsrv):
        if s not in individual:
            rv=False
    if not rv and print_warning:
        print(f'individual {individual} is not correct')
    return rv

def obj_func(individual, problem: ProblemPwr):
    sol = problem.get_solution(individual)
    return sol.obj_func(),

def find_none_in_child(child, start_idx):
    if start_idx >= len(child):
        return None
    for i in range(start_idx, len(child)):
        if child[i] is None:
            return i
    return None

def find_new_in_parent(parent, child, start_idx):
    if start_idx >= len(parent):
        return None
    for i in range(start_idx, len(parent)):
        if parent[i] not in child:
            return i
    return None

def cx_solution_pwr(ind1, ind2, problem: ProblemPwr):
    """
    Implements ordered crossover (OX2) for parents of different lengths, making sure that the first gene reimains a fog specifier
    """
    #
    # print(f'crossover {ind1}, {ind2}')
    size = min(len(ind1), len(ind2))  # Use the minimum length
    parents_ok=check_individual_correct(ind1, problem) and check_individual_correct(ind2, problem)
    # Choose random start/end position for crossover. First element is never touched
    start, end = sorted([random.randrange(size-1)+1 for _ in range(2)])
    start, end = min(start, end), max(start, end)
    #print(start, end)
    # Initialize children with placeholders
    child1, child2 = [None] * len(ind2), [None] * len(ind1)
    # Copy ind1's sequence for child1 and ind2's sequence for child2
    child1[start:end + 1] = ind1[start:end + 1]
    child2[start:end + 1] = ind2[start:end + 1]
    child1[0]=ind1[0]
    child2[0]=ind2[0]
    #print(child1, child2)
    # Fill remaining positions of child1 from parent2
    parent_idx=find_new_in_parent(ind2, child1, 0)
    child_idx=find_none_in_child(child1, 1)
    while parent_idx is not None:
        if child_idx is not None:
            child1[child_idx]=ind2[parent_idx]
            child_idx=find_none_in_child(child1, child_idx)
        else:
            child1.append(ind2[parent_idx])
        parent_idx=find_new_in_parent(ind2, child1, parent_idx)
    # Fill remaining positions of child1 from parent1
    parent_idx=find_new_in_parent(ind1, child1, 0)
    child_idx=find_none_in_child(child1, 1)
    while parent_idx is not None:
        if child_idx is not None:
            child1[child_idx]=ind1[parent_idx]
            child_idx=find_none_in_child(child1, child_idx)
        else:
            child1.append(ind1[parent_idx])
        parent_idx=find_new_in_parent(ind1, child1, parent_idx)
    # Fill remaining positions of child2 from parent1
    parent_idx=find_new_in_parent(ind1, child2, 0)
    child_idx=find_none_in_child(child2, 1)
    while parent_idx is not None:
        if child_idx is not None:
            child2[child_idx]=ind1[parent_idx]
            child_idx=find_none_in_child(child2, child_idx)
        else:
            child2.append(ind1[parent_idx])
        parent_idx=find_new_in_parent(ind1, child2, parent_idx)
    # Fill remaining positions of child2 from parent2
    parent_idx=find_new_in_parent(ind2, child2, 0)
    child_idx=find_none_in_child(child2, 1)
    while parent_idx is not None:
        if child_idx is not None:
            child2[child_idx]=ind2[parent_idx]
            child_idx=find_none_in_child(child2, child_idx)
        else:
            child2.append(ind2[parent_idx])
        parent_idx=find_new_in_parent(ind2, child2, parent_idx)

    # make changes in place
    if parents_ok and (not check_individual_correct(child1, problem) or not check_individual_correct(child2, problem)):
        print(f'*** cx generating error: {ind1}, {ind2} -> {child1}, {child2}')
    in_place_copy(child1, ind2)
    in_place_copy(child2, ind1)
    normalize_individual(ind1, problem)
    normalize_individual(ind2, problem)
    return ind1, ind2

def in_place_copy(src, dst):
    # adjust size
    if len(src) > len(dst):
        for _ in range(len(src)-len(dst)):
            dst.append(None)
    if len(dst) < len(src):
        for _ in range(len(dst)-len(src)):
            dst.pop()
    for i in range(len(src)):
        dst[i]=src[i]

def load_individuals(creator, problem: ProblemPwr):
    min_service=0
    max_service=problem.get_nservice()
    nfog=problem.get_nfog()
    services = list(range(min_service, max_service))
    #print(services)
    #print(list(range(max_service, max_service+nfog)))
    #FIXME: should extimate the ideal number of fog nodes!
    fogs=random.sample(list(range(max_service, max_service+nfog)), nfog)
    #print(fogs)
    # First chromosome must always be a fog ID
    rv=services+fogs[1:]
    random.shuffle(rv)
    individual=creator(fogs[0:1] + rv)
    if not check_individual_correct(individual, problem):
        print(f'*** load_individuals generating error: {individual}')
    return individual

def is_fog(g, nsrv):
    return g is not None and g>=nsrv

def individual_to_chains(individual, problem: ProblemPwr):
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

def mut_del_fog(individual, indpb, problem: ProblemPwr):
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

def mut_add_fog(individual, indpb, problem: ProblemPwr):
    pass
    # find list of off services
    # decide which fog to add
    # populate the fog

def mut_shuffle_pwr(individual, indpb, problem: ProblemPwr):
    """
    :param individual: Individual to be mutated.
    :param indpb: Independent probability for each attribute to be exchanged to
                  another position.
    :returns: A tuple of one individual.
    """
    size = len(individual)
    # mutate first element: it must be a fog node!
    old_individual=individual[:]
    ind_ok=check_individual_correct(individual, problem)
    nsrv = problem.get_nservice()
    if random.random() < indpb:
            idx_fogs=[i for i in range(size) if is_fog(individual[i], nsrv)]
            #print(f'mutation: {individual}, nservices: {nsrv} fog indexes: {idx_fogs}')
            if len(idx_fogs)>1:
                swap_indx = random.randint(0, len(idx_fogs)-1)
                individual[0], individual[idx_fogs[swap_indx]] = individual[idx_fogs[swap_indx]], individual[0]
    for i in range(1, size):
        if random.random() < indpb:
            swap_indx = random.randint(1, size - 2)
            if swap_indx >= i:
                swap_indx += 1
            individual[i], individual[swap_indx] = individual[swap_indx], individual[i]
    normalize_individual(individual, problem)
    if ind_ok and not check_individual_correct(individual, problem):
        print(f'mutation generating error: {old_individual} -> {individual}')
    return individual,


if __name__ == '__main__':
    import json
    from .ga import load_problem
    with open("sample/sample_input_pwr2.json") as f:
        problem=load_problem(json.load(f))
    cx_solution_pwr( [4, 1, 2, 0], [3, 4, 0, 2, 1], problem)    