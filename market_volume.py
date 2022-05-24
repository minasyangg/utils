import json
import os
import pandas as pd
import utils.SourceAggregator as sa
from pprint import pprint

def get_smb_info(base, quote, inst_type = 'swap'):
    trg_src = sa.SourcesAggregator()
    price = trg_src.okx_ccxt_client.fetch_ticker('/'.join((base, 'USDT')))['last']

    trg_info = list(filter(lambda x: (x['base'] == base and x['quote'] == quote and x["info"]["instType"] == inst_type.upper()), trg_src.okx_markets))
    try:
        ctr_size = float(trg_info[0]["info"]["ctVal"])
        min_size = float(trg_info[0]["info"]["minSz"])
    except ValueError:
        min_size = float(trg_info[0]["info"]["minSz"])
        ctr_size = min_size


    return  price, ctr_size, min_size

def smb_info_dict(symbol,idx):
    if len(symbol.split('-')) == 3:
        if symbol.split('-')[2] == 'SWAP':
            base, quote = symbol.split('-')[0], symbol.split('-')[1]
            info = get_smb_info(base, quote)
            smb_info = {'symbol': symbol, 'base': base, 'range_coef_24': RANGE_24_COEF[idx], 'info': {'price': info[0], 'cntr_size': info[1], 'min_size': info[2], "increase_coef": round((0.8 - RANGE_24_COEF[idx]), 1)}}
            return smb_info


project_path = os.path.abspath('../').replace("\\", '/')
path_to_robots = project_path + '/base_trading_configs/robots/'   #path to robots
path_to_hosts = project_path + '/base_trading_configs/hosts/hosts.json'

path_to_model = []



df_stats = pd.read_csv(project_path + '/utils/market_stats/24_05_usdt.csv')
df_stats_less_30 = df_stats[(df_stats['24h Range'] != '0%-10%') & (df_stats['24h Range'] != '10%-20%') & (df_stats['24h Range'] != '20%-30%') & (df_stats['Expiries'] == 'All')]
df_stats_less_30 = df_stats_less_30.dropna().reset_index().drop(['index', '24h Taker Vol.', '24h Total Vol.', '24h Percentage', 'Monthly Maker Vol.', 'Monthly Taker Vol.', 'Monthly Total Vol.', 'Monthly Percentage'], 1)

SYMBOL = df_stats_less_30['Pair'].astype(str).tolist()
RANGE_24_COEF = df_stats_less_30['24h Range'].astype(str).apply(lambda x: 1 - int(x.split('-')[1].split('%')[0])/100)

for address, dirs, files in os.walk(path_to_robots):
    for name in files:
        path = os.path.join(address, name)
        path_to_model.append(path)


def increase_usdt_margin(host_name, write_to_config):
    with open(f'market_stats/current_stat_{host_name}.txt', 'w') as outfile:
        outfile.write("USDT_MARGIN\n")

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
        for path in path_to_model:  # choose exchange_name or symbol
            with open(path) as f:
                cfg = json.load(f)
            robot_type = cfg["type"]
            if robot_type == 'ig11':
                model_id = cfg["model_id"]
                symbol = cfg["model"]['target'][0]['symbol'].replace('_', '-').replace('PERP', 'SWAP')
                if model_id in model_list:
                    if ('MMP' not in model_id) and (symbol in SYMBOL):
                        print(model_id)
                        smb_index = SYMBOL.index(symbol)
                        smb_dict = smb_info_dict(symbol, smb_index)

                        price = smb_dict["info"]['price']
                        cntr_size = smb_dict["info"]['cntr_size']
                        increase_coef = smb_dict['info']['increase_coef']

                        pos_step = cfg["model"]["pos_step"]
                        max_pos = cfg["model"]["max_pos"]

                        if smb_dict['info']['increase_coef'] > 0:
                            pos_step *= 1+increase_coef
                            max_pos *= 1+increase_coef
                            pos_step_usdt = round(pos_step*price, 0)
                            max_pos_usdt = round(max_pos*price, 0)
                            with open(f'market_stats/current_stat_{host_name}.txt', 'a') as outfile:
                                if max_pos % pos_step != 0:
                                    outfile.write(f"ATTENTION: pos_step/max_pos: {model_id}, {increase_coef}\n")
                                elif pos_step_usdt > 350 or pos_step_usdt < 100 or max_pos_usdt > 1000:
                                    outfile.write(f'{model_id}| pos_step_usdt: {pos_step_usdt}| max_pos_usdt: {max_pos_usdt}| price: {price}\n')
                                    if write_to_config:
                                        with open(path, 'w') as f:
                                            cfg["model"]["pos_step"] = pos_step
                                            cfg["model"]["max_pos"] = max_pos
                                            json.dump(cfg, f, indent=2)
                                    else: pass


            elif robot_type == 'flappy':
                model_id = cfg["model_id"]
                symbol = cfg["model"]["target"]["symbol"].replace('_', '-').replace('PERP', 'SWAP')
                if model_id in model_list:
                    if ('MMP' not in model_id) and (symbol in SYMBOL):
                        print(model_id)
                        smb_index = SYMBOL.index(symbol)
                        smb_dict = smb_info_dict(symbol, smb_index)

                        price = smb_dict["info"]['price']
                        cntr_size = smb_dict["info"]['cntr_size']
                        increase_coef = smb_dict['info']['increase_coef']
                        level_size = cfg["model"]["level_size"]
                        max_base_pos = cfg["model"]["max_base_pos"]

                        if smb_dict['info']['increase_coef'] > 0:
                            level_size *= 1+increase_coef
                            max_base_pos *= 1+increase_coef
                            level_size_usdt = round(level_size*cntr_size*price, 0)
                            max_base_usdt = round(max_base_pos*cntr_size*price, 0)

                            with open(f'market_stats/current_stat_{host_name}.txt', 'a') as outfile:
                                if max_base_pos % level_size != 0:
                                    outfile.write(f"ATTENTION: max_pos/level_size: {model_id}, {increase_coef}\n")
                                elif level_size_usdt > 250 or level_size_usdt < 80 or max_base_usdt > 800:
                                    outfile.write(f'{model_id}| level_size_usdt: {level_size_usdt}| max_pos_usdt: {max_base_usdt}| price: {price}\n')
                                    if write_to_config:
                                        with open(path, 'w') as f:
                                            cfg["model"]["level_size"] = level_size
                                            cfg["model"]["max_base_pos"] = max_base_pos
                                            json.dump(cfg, f, indent=2)
                                    else: pass


increase_usdt_margin('os-prod-6', True)



