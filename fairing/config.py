from fairing.preprocessors.base import BasePreProcessor
from fairing.preprocessors.converted_notebook import ConvertNotebookPreprocessor
from fairing.preprocessors.full_notebook import FullNotebookPreProcessor

from fairing.builders.append.append import AppendBuilder
from fairing.builders.docker.docker import DockerBuilder
from fairing.builders.cluster.cluster import ClusterBuilder
from fairing.builders.builder import BuilderInterface

from fairing.deployers.job.job import Job
from fairing.deployers.tfjob.tfjob import TfJob
from fairing.deployers.deployer import DeployerInterface

from fairing.notebook import notebook_util

import logging
logging.basicConfig(format='%(message)s')

DEFAULT_PREPROCESSOR = 'python'
DEFAULT_BUILDER = 'append'
DEFAULT_DEPLOYER = 'job'

preprocessor_map = {
    'python': BasePreProcessor,
    'notebook': ConvertNotebookPreprocessor,
    'full_notebook': FullNotebookPreProcessor,
}

builder_map = {
    'append': AppendBuilder,
    'docker': DockerBuilder,
    'cluster': ClusterBuilder,
}

deployer_map = {
    'job': Job,
    'tfjob': TfJob
}


class Config(object):
    def __init__(self):
        self._preprocessor = None
        self._builder = None
        self._deployer = None
        self._model = None

    def set_preprocessor(self, name=None, **kwargs):
        if name is None:
            if notebook_util.is_in_notebook():
                name = 'notebook'
            else:
                name = DEFAULT_PREPROCESSOR
        preprocessor = preprocessor_map.get(name)
        self._preprocessor = preprocessor(**kwargs)
    
    def get_preprocessor(self):
        if self._preprocessor is None:
            self.set_preprocessor()
        return self._preprocessor

    def set_builder(self, name=DEFAULT_BUILDER, **kwargs):
        builder = builder_map.get(name)
        self._builder = builder(preprocessor=self.get_preprocessor(), **kwargs)
        if not isinstance(self._builder, BuilderInterface):
            raise TypeError(
                'builder must be a BuilderInterface, but got %s' 
                % type(self._builder))
    
    def get_builder(self):
        if self._builder is None:
            self.set_builder()
        return self._builder
        
    def set_deployer(self, name=DEFAULT_DEPLOYER, **kwargs):
        deployer = deployer_map.get(name)
        self._deployer = deployer(**kwargs)
        if not isinstance(self._deployer, DeployerInterface):
            raise TypeError(
                'backend must be a DeployerInterface, but got %s' 
                % type(self._deployer))

    def get_deployer(self):
        if self._deployer is None:
            self.set_deployer()
        return self._deployer
        
    def set_model(self, model):
        self._model = model
    
    def get_model(self):
        return self._model

    def run(self):
        self.get_builder().build()
        pod_spec = self._builder.generate_pod_spec()
        self.get_deployer().deploy(pod_spec)
        self.reset()

    def reset(self):
        self._builder = None
        self._deployer = None
        self._model = None
        self._preprocessor = None


config = Config()
