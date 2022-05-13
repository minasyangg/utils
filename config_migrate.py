import json
import os

from pprint import pprint

project_path = os.path.abspath('../').replace("\\", '/')
path_to_robots = project_path + '/base_trading_configs/robots/'   #path to robots


path_to_model = []

for address, dirs, files in os.walk(path_to_robots):
    for name in files:
        path = os.path.join(address, name)
        path_to_model.append(path)

for path in path_to_model:
    if 'flappy' in path:
        with open(path) as infile:
            cfg = json.load(infile)

        model_src = cfg["model"]["sources"]
        trg_acc = cfg["model"]["accounts"]
        trg_ex_name = cfg["model"]["target"]["exchange"]
        trg_symbol = cfg["model"]["target"]["symbol"]
        depth_size = 200

        instruments = []
        instr = {}

        for i, src in enumerate(model_src):
            if (trg_ex_name != src["exchange"] or trg_symbol != src["symbol"]):
                instruments.append({
                    "exchange": src["exchange"],
                    "symbol": src["symbol"],
                    "depth_stream": True,
                    "trade_stream": True,
                    "can_trade": False,
                    "depth_size": depth_size
                })

        instruments.append({
            "exchange": trg_ex_name,
            "symbol": trg_symbol,
            "depth_stream": True,
            "trade_stream": True,
            "can_trade": True,
            "depth_size": depth_size,
            "accounts": trg_acc
        })

        cfg["model"]["instruments"] = instruments

        with open(path, 'w') as f:
            json.dump(cfg, f, indent=2)

    elif "ig11" in path:
        with open(path) as infile:
            cfg = json.load(infile)

        imut_instr = cfg['model']['target_kernel']['spread_model']['immutable_instruments']
        mut_instr = cfg['model']['target_kernel']['spread_model']['mutable_instruments']
        model_src = imut_instr + mut_instr
        trg_ex_name = cfg['model']['target'][0]['exchange']
        trg_symbol = cfg['model']['target'][0]['symbol']
        trg_acc = cfg['model']['target'][0]['accounts']
        depth_size = 200

        instruments = []
        instr = {}

        # pprint(model_src)


        for src in model_src:
            if (trg_ex_name != src["exchange"] or trg_symbol != src["symbol"]):
                instruments.append({
                    "exchange": src["exchange"],
                    "symbol": src["symbol"],
                    "depth_stream": True,
                    "trade_stream": True,
                    "can_trade": False,
                    "depth_size": depth_size
                })

        instruments.append({
            "exchange": trg_ex_name,
            "symbol": trg_symbol,
            "depth_stream": True,
            "trade_stream": True,
            "can_trade": True,
            "depth_size": depth_size,
            "accounts": trg_acc
        })

        cfg["model"]["instruments"] = instruments
        with open(path, 'w') as f:
            json.dump(cfg, f, indent=2)