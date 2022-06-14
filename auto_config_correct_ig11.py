import json
import os

from pprint import pprint

project_path = os.path.abspath('../').replace("\\", '/')
path_to_robots = project_path + '/base_trading_configs/robots/flappy/okex_v5_futures'   #path to robots
path_to_hosts = project_path + '/base_trading_configs/hosts/hosts.json'


path_to_model = []

for address, dirs, files in os.walk(path_to_robots):
    for name in files:
        path = os.path.join(address, name)
        path_to_model.append(path)

def fix_indicatators(path_to_model, host_name):
    with open(path_to_hosts) as f:
        hosts = json.load(f)
        for host in hosts:
            try:
                if host["name"] == host_name:
                    model_list = host['runners']
            except KeyError:
                pass
    target_mid = []
    if model_list:
        for path in path_to_model:                                            #choose exchange_name or symbol
            with open(path) as f:
                cfg = json.load(f)
            robot_type = cfg["type"]
            if robot_type == 'ig11':
                model_id = cfg["model_id"]
                if model_id in model_list:
                    if 'MMP' not in model_id:
                        cfg['model']['indicators']['clickhouse']['enable'] = True
                        cfg['model']['indicators']['clickhouse']['black_list'] = []
                        cfg['model']['indicators']['clickhouse']['white_list'] = []
                        with open(path, 'w') as f:
                            json.dump(cfg, f, indent=2)
                    target_mid.append(model_id)
            elif robot_type == 'flappy':
                model_id = cfg["model_id"]
                if model_id in model_list:
                    if 'MMP' not in model_id:
                        cfg['model']['indicators']['clickhouse']['enable'] = True
                        cfg['model']['indicators']['clickhouse']['black_list'] = []
                        cfg['model']['indicators']['clickhouse']['white_list'] = []
                        with open(path, 'w') as f:
                            json.dump(cfg, f, indent=2)
                    target_mid.append(model_id)

    if len(target_mid) == len(model_list):
        print("Length equal")
    else:
        print("Not equal lenght")

def fix_fee(path_to_models):
    fee_configs = []
    for path in path_to_model:
        with open(path) as f:
            cfg = json.load(f)
            smb = cfg['model']['target']['symbol']
            if '_USD_' in smb:
                fee = {}
                fee["symbol"] = smb
                fee["maker_percent"] = -0.01
                fee["taker_percent"] = 0.02
                fee_configs.append(fee)
    print(len(fee_configs))
    with open('temp_files/fee_crypto_swap.json', 'w') as f:
        json.dump(fee_configs, f, indent=2)

fix_fee(path_to_model)