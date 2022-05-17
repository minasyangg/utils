import json
import os

project_path = os.path.abspath('../').replace("\\", '/')
path_to_hosts = project_path + '/base_trading_configs/hosts/hosts.json'

exchange = input("write ex_name")
flappy_robots = []
ig_robots = []
with open(path_to_hosts) as f:
    hosts = json.load(f)

for item in hosts:
    try:
        host_name = item["name"]
        if exchange == host_name.split('-')[0]:
            for mid in item['runners']:
                if 'FLAPPY' in mid:
                    flappy_robots.append(mid)
                elif 'IG11' in mid:
                    ig_robots.append(mid)
                else:
                    print("Unknown robot type")


    except KeyError:
        pass

print(f'FLAPPY {len(flappy_robots)} || IG11 {len(ig_robots)} || sum: {len(flappy_robots) + len(ig_robots)} ')

