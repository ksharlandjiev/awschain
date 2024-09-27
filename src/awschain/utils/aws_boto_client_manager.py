import boto3
from botocore.config import Config
from .config_loader import ConfigLoader

class AWSBotoClientManager:
    _clients = {}

    @classmethod
    def get_client(cls, service_name, region=ConfigLoader.get_config('AWS_DEFAULT_REGION', 'us-east-1')):
        AWS_DEFAULT_REGION = region
        
        my_config = Config(region_name=AWS_DEFAULT_REGION)
                
        if service_name not in cls._clients:
            cls._clients[service_name] = boto3.client(service_name, config=my_config)
        return cls._clients[service_name]
