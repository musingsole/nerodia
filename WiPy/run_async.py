import _thread
from time import sleep_us


def no_log(*args, **kwargs):
    return


def run_async(func,
              arg_sets,
              log=no_log,
              sleep_duration_us=1000):
    results = {}

    log("Beginning Asynchronous Execution for {} argument sets".format(len(arg_sets)))

    def stored_result(identifier, arg_set):
        log("{} Starting".format(identifier))
        if type(arg_set) == list:
            result = func(*arg_set)
        elif type(arg_set) == dict:
            result = func(**arg_set)
        else:
            raise Exception("Unrecognized arg_set")
        results[identifier] = result
        log("{} Complete".format(identifier))

    for index, arg_set in enumerate(arg_sets):
        _thread.start_new_thread(stored_result, (str(index), arg_set))

    while len(results) < len(arg_sets):
        sleep_us(sleep_duration_us)
    log("Returning {} results".format(len(results)))
    results = [(arg_set, results[str(index)]) for index, arg_set in enumerate(arg_sets)]
    return results
