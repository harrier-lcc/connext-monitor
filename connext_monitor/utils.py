import json

def chain_id_to_name(id: int) -> str:
    match id:
        case 1:
            return "ethereum"
        case 137:
            return "polygon"
        case 42161:
            return "arbitrum-one"
        case _:
            return ""

def get_deployment_config(path: str):
    with open(path) as deployment:
        return json.load(deployment)
