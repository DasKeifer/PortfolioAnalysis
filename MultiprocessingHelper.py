import time
import multiprocess
from queue import Empty, Full
import traceback

def workerWrapper(fn, data, inq, outq):
    print("starting worker")
    from queue import Empty
    try:
        while True:
            print(inq.qsize())
            args = inq.get(True, 2)
            outq.put(fn(data, args), True, 2)
    except Empty:
        print("Queue empty - all work done")
    except Exception as e:
        print("Unknown error", str(e))
        
def runFunctionMultiprocess(fn, num_proc, data, args, out_list):
    start = time.perf_counter()
    
    manager = multiprocess.Manager()
    args_queue, output_queue = manager.Queue(len(args)), manager.Queue(len(args))
    for params in args: 
        args_queue.put(params)

    processes = []
    #with suppress_stdout():
    for i in range(num_proc):
        print("starting", i)
        processes.append(multiprocess.Process(target=workerWrapper, args=(fn, data, args_queue, output_queue)))
        processes[-1].start()

    for i, process in enumerate(processes):
        print("joining", i)
        process.join()
        process.close()

    stop = time.perf_counter()
    elapsed = (stop - start)
    print("All processes stopped:", elapsed)

    print("Copying results...")
    start = time.perf_counter()
    try:
        while True: 
            out_list.append(output_queue.get(True, 2))
    except Empty:
        pass
    
    stop = time.perf_counter()
    print("Finished copy results:", (stop - start))