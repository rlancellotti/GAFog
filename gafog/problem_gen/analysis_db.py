import sqlite3
from copy import deepcopy
from collections import OrderedDict

from ..ga import ga_perf, ga_pwr

PROBLEM_CONF_COLLISION_PREFIX = 'problem_'
OPTIMIZER_CONF_COLLISION_PREFIX = 'optimizer_'


def _handle_config_collisions(config1: dict, config2: dict, collision_prefix1: str, collision_prefix2: str):
    """
    Given two configuration dictionaries it finds all common keys and it renames them using a specific
    prefix for each dictionary.
    """
    config1_cpy = deepcopy(config1)
    config2_cpy = deepcopy(config2)

    collisions = config1_cpy.keys() & config2_cpy.keys()
    for coll in collisions:
        config1_cpy[collision_prefix1+coll] = config1_cpy[coll]
        config2_cpy[collision_prefix2+coll] = config2_cpy[coll]
        config1_cpy.pop(coll)
        config2_cpy.pop(coll)

    return config1_cpy, config2_cpy


def _get_defaults_GA(problem_type: str, funct_type: str):
    """
    Given a specific problem type and a function type (crossover, mutation)
    it returns the dictionary containing the default parameters of that
    function for that specific problem
    """
    defaults_dict = dict()

    if problem_type == 'power':

        if funct_type == 'mutation':
            defaults_dict = ga_pwr.mut_pwr.__kwdefaults__
        elif funct_type == 'crossover':
            defaults_dict = ga_pwr.cx_solution_pwr.__kwdefaults__

    elif problem_type == 'performace':

        if funct_type == 'mutation':
            defaults_dict = ga_perf.mut_uniform_fog.__kwdefaults__
        elif funct_type == 'crossover':
            defaults_dict = ga_perf.cx_uniform_fog.__kwdefaults__

    return defaults_dict


def _get_default_parameter(problem_type: str, optimizer_type: str, structured_key: str):
    """
    Given a specific problem type, optimizer type and a structured key (generated
    by the function "flatten_multilevel_config") it returns the default value
    setted for that specific parameter
    """

    default_value = None

    key_components = structured_key.split('__')

    if optimizer_type == 'GA':
        if key_components[0] == 'mutation_params':
            default_value = _get_defaults_GA(problem_type, 'mutation').get(key_components[1], None)
        elif key_components[0] == 'crossover_params':
            default_value = _get_defaults_GA(problem_type, 'crossover').get(key_components[1], None)

    return default_value


def _flatten_multilevel_config(config: dict, value_modifier=lambda x:x, prefix: str=''):
        """
        Given a multilevel dictionary representing the configuration of the
        problem or the optimizer it generates a single level dictionary which
        encodes the lost strucural info as structured dict keys
        """
        config_schema = dict()

        for key,value in config.items():
            if type(value) is not dict:
                config_schema[prefix + key] = value_modifier(value)
            else:
                config_schema |= _flatten_multilevel_config(config[key], prefix=prefix + key + '__')

        return config_schema


def create_schema(problem_config: dict, optimizer_config:dict, experiment_result: dict):
    """
    Generates a database table schema using an instance of problem config,
    optimizer config and the results of a specific experiment
    """

    def native_datatype(value):
        return type(value.item()) if hasattr(value, 'dtype') and hasattr(value, 'item') else type(value)

    def to_schema_dict(dictionary: dict):
        return {key: (native_datatype(value) if native_datatype(value) is not bool else int) for key,value in dictionary.items()}

    def to_ordered_dict(dictionary: dict):
        return OrderedDict((key, dictionary[key]) for key in sorted(dictionary.keys()))
    
    problem_config_cpy = deepcopy(problem_config)
    optimizer_config_cpy = deepcopy(optimizer_config)

    try:
        problem_config_cpy.pop('response')
    except KeyError:
        pass
    
    # Adding possible missing parameters relative to the crossover and mutation functions
    if optimizer_config_cpy['type'] == 'GA':

        def handle_GA_fun_parameters(problem_type, optimizer_config: dict, fun_type):

            optimizer_config_cpy = deepcopy(optimizer_config)

            params_key = fun_type + '_params'

            if (optimizer_config_cpy.get(params_key, None) is not None 
                and (defs := _get_defaults_GA(problem_type, fun_type)) is not None):

                optimizer_config_cpy[params_key] |= to_schema_dict(defs)

            elif optimizer_config_cpy.get(params_key, None) is None:

                try:
                    optimizer_config_cpy.pop(params_key)
                except KeyError:
                    pass

            return optimizer_config_cpy
        

        optimizer_config_cpy = handle_GA_fun_parameters(problem_config_cpy['type'], optimizer_config_cpy, 'mutation')
        optimizer_config_cpy = handle_GA_fun_parameters(problem_config_cpy['type'], optimizer_config_cpy, 'crossover')
    
    problem_columns = _flatten_multilevel_config(problem_config_cpy, value_modifier=native_datatype)
    optimizer_columns = _flatten_multilevel_config(optimizer_config_cpy, value_modifier=native_datatype)
    problem_columns, optimizer_columns = _handle_config_collisions(problem_columns, optimizer_columns, 
                                                                   PROBLEM_CONF_COLLISION_PREFIX, OPTIMIZER_CONF_COLLISION_PREFIX)
    result_columns = to_schema_dict(experiment_result)

    return to_ordered_dict(problem_columns) | to_ordered_dict(optimizer_columns) | to_ordered_dict(result_columns)


def _create_columns_str(schema: dict, separator=', '):
    """
    Generates the columns string used to create a table through SQL queries
    """

    columns_str = ''

    def type_str(col_type):
        ret = None

        if col_type in (int, bool):
            ret = 'INTEGER'
        elif col_type is float:
            ret = 'REAL'
        elif col_type is str:
            ret = 'TEXT'
            
        return ret

    for column, col_type in schema.items():
        col_type_str = type_str(col_type)
        if col_type_str is not None:
            columns_str += f'{column} {col_type_str}' + separator
        else:
            raise TypeError(f'ERROR: Unrecognized/unsupported type for column {column} ({col_type})')

    return columns_str[:-2]


def init_db(connection: sqlite3.Connection, schema: dict):
    """
    Initializes the database by creating (if not present) the necessary "experiment" table
    """
    cursor = connection.cursor()

    columns_str = _create_columns_str(schema)
    unique_str = ', '.join(schema.keys())

    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS experiment (
                    id INTEGER PRIMARY KEY, 
                    {columns_str},
                    UNIQUE ({unique_str}) ON CONFLICT IGNORE
    ) 
    '''
    )
    cursor.close()


def insert_experiment(connection: sqlite3.Connection, problem_config: dict, optimizer_config: dict, experiment_result: dict, schema: dict):
    """
    Inserts the results of an experiment and the respective configuration into 
    the experiment table in the database
    """
    cursor = connection.cursor()
    
    def get_entry_values_str(schema, entry, separator = ', '):
        values_str = ''

        for key, value_type in schema.items():
            entry_val = entry.get(key, None)
            entry_val = entry_val if entry_val is not None else 'NULL'

            if entry_val == 'NULL':
                values_str += entry_val + separator
            elif value_type is not str:
                values_str += str(entry_val) + separator
            else:
                values_str += f"'{entry_val}'" + separator
    
        return values_str[:-2]

    flattened_problem_config = _flatten_multilevel_config(problem_config)
    flattened_optimizer_config = _flatten_multilevel_config(optimizer_config)

    flattened_problem_config, flattened_optimizer_config = _handle_config_collisions(flattened_problem_config, 
                                                                                     flattened_optimizer_config, 
                                                                                     PROBLEM_CONF_COLLISION_PREFIX, 
                                                                                     OPTIMIZER_CONF_COLLISION_PREFIX
                                                                                     )

    entry_values = flattened_problem_config | flattened_optimizer_config | experiment_result

    for key in schema.keys():
        if key not in entry_values.keys():
            entry_values[key] = _get_default_parameter(problem_config['type'], optimizer_config['type'], key)

    query = f'''
    INSERT INTO experiment ({', '.join(schema.keys())}) VALUES ({get_entry_values_str(schema, entry_values)})
    '''
    print(query)
    cursor.execute(query)
    cursor.close()


def print_table(connection: sqlite3.Connection, table_name: str):
    """
    Given a db connection it prints all content present in a table identified by 
    the parameter 'table name'
    """

    cursor = connection.cursor()

    cursor.execute(f"SELECT * FROM {table_name}")

    entries = cursor.fetchall()

    for col in [col_tupl[0] for col_tupl in cursor.description]:
        print(col, end=' ')
    print('\n')

    for entry in entries:
        for value in entry:
            print(value, end=' ')
        print('\n')

    cursor.close()


def get_experiments_by_scenario(connection: sqlite3.Connection, scenario_config: dict):
    cursor = connection.cursor()

    flattened_problem_scenario = _flatten_multilevel_config(scenario_config.get('problem', None))
    flattened_optimizer_scenario = _flatten_multilevel_config(scenario_config.get('optimizer', None))

    flattened_problem_scenario, flattened_optimizer_scenario = _handle_config_collisions(flattened_problem_scenario, 
                                                                                         flattened_optimizer_scenario, 
                                                                                         PROBLEM_CONF_COLLISION_PREFIX, 
                                                                                         OPTIMIZER_CONF_COLLISION_PREFIX
                                                                                         )
    flattened_scenario_config = flattened_problem_scenario | flattened_optimizer_scenario
    
    where_clause = ' AND '.join([f'{key} = {value}' for key, value in flattened_scenario_config.items()])

    query = f"""SELECT * 
                FROM experiment
                WHERE {where_clause}
    """

    cursor.execute(query)

    return cursor.fetchall()