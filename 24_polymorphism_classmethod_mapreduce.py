import os
from tempfile import TemporaryDirectory
from threading import Thread
from random import randint

class GenericInputData:
    def read(self):
        raise NotImplementedError

    @classmethod
    def generate_inputs(cls, config):
        raise NotImplementedError

class PathInputData(GenericInputData):
    def __init__(self, path):
        self.path = path

    def read(self):
        return open(self.path).read()
    
    @classmethod
    def generate_inputs(cls, config):
        data_dir = config['data_dir']
        for name in os.listdir(data_dir):
            yield cls(os.path.join(data_dir, name))


class GenericWorker:
    def map(self):
        raise NotImplementedError
    def reduce(self, other):
        raise NotImplementedError

    @classmethod
    def create_worker(cls, input_class, config):
        workers = []
        for input_data in input_class.generate_inputs(config):
            workers.append(cls(input_data))
        return workers


class LineCountWorker(GenericWorker):
    def __init__(self, input_data):
        self.input_data = input_data
        self.result = None

    def map(self):
        data = self.input_data.read()        
        self.result = data.count('\n')

    def reduce(self, other):
        self.result += other.result


def execute(workers):
    threads = [Thread(target=w.map) for w in workers]
    for thread in threads: thread.start()
    for thread in threads: thread.join()

    first, rest = workers[0], workers[1:]
    for worker in rest:
        first.reduce(worker)
    return first.result

def mapreduce(worker_class, input_class, config):
    workers = worker_class.create_worker(input_class, config)
    return execute(workers)


def write_test_files(tmpdir, min_lines=0, max_lines=100, file_count=10000):
    for i in range(file_count):
        file = os.path.join(tmpdir, str(i) + '.txt')
        with open(file, 'a') as f:
            for j in range(randint(min_lines, max_lines)):
                f.write('LINE\n')


with TemporaryDirectory() as tmpdir:
    print('tmpdir', tmpdir)
    write_test_files(tmpdir)
    config =  {'data_dir': tmpdir}
    result = mapreduce(LineCountWorker, PathInputData, config)
    print('result', result)