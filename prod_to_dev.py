import sys
import json
import os


def preprocess_kernel_config(kernel_config, last_feature_idx):
    kernel_config["spread_model"]["time_step_us"] = kernel_config["spread_model"]["mutable_instruments"][0][
        "time_step_us"]

    for mutable_instrument in kernel_config["spread_model"]["mutable_instruments"]:
        mutable_instrument["aggregate"]["type"] = mutable_instrument["aggregate"]["aggregate_type"]
        del mutable_instrument["aggregate"]["aggregate_type"]
        del mutable_instrument["time_step_us"]

    kernel_config["fair_price_model"] = kernel_config["weight_model"]

    kernel_config["fair_price_model"]["weight_model"] = {}
    kernel_config["fair_price_model"]["weight_model"]["target"] = kernel_config["weight_model"]["target"]

    kernel_config["fair_price_model"]["weight_model"]["target"]["aggregate"]["type"] = \
    kernel_config["fair_price_model"]["weight_model"]["target"]["aggregate"]["aggregate_type"]

    del kernel_config["fair_price_model"]["weight_model"]["target"]["aggregate"]["aggregate_type"]

    kernel_config["fair_price_model"]["weight_model"]["target"]["aggregate"]["name"] = "weight_model_target"

    kernel_config["fair_price_model"]["weight_model"]["fit_step_us"] = kernel_config["weight_model"]["fit_step_us"]
    kernel_config["fair_price_model"]["weight_model"]["normalize"] = kernel_config["weight_model"]["normalize"]
    kernel_config["fair_price_model"]["weight_model"]["min_weights_sum"] = kernel_config["weight_model"][
        "min_weights_sum"]
    kernel_config["fair_price_model"]["weight_model"]["learning_rate"] = kernel_config["weight_model"]["learning_rate"]
    kernel_config["fair_price_model"]["weight_model"]["return_barrier"] = kernel_config["weight_model"][
        "return_barrier"]

    del kernel_config["fair_price_model"]["fit_step_us"]
    del kernel_config["fair_price_model"]["normalize"]
    del kernel_config["fair_price_model"]["min_weights_sum"]
    del kernel_config["fair_price_model"]["learning_rate"]
    del kernel_config["fair_price_model"]["return_barrier"]

    del kernel_config["fair_price_model"]["target"]

    last_feature_idx = last_feature_idx

    for feature in kernel_config["fair_price_model"]["features"]:
        for aggregate in feature["aggregates"]:
            aggregate["type"] = aggregate["aggregate_type"]
            del aggregate["aggregate_type"]

            aggregate["name"] = "feature_" + str(last_feature_idx)
            last_feature_idx += 1

    for feature in kernel_config["fair_price_model"]["merged_orderbooks_features"]:
        for aggregate in feature["aggregates"]:
            aggregate["type"] = aggregate["aggregate_type"]
            del aggregate["aggregate_type"]

            aggregate["name"] = "feature_" + str(last_feature_idx)
            last_feature_idx += 1

    del kernel_config["weight_model"]

    return last_feature_idx




project_path = os.path.abspath('../').replace("\\", '/')
path_to_robots = project_path + '/base_trading_configs/robots/ig11'   #path to robots


path_to_model = []

for address, dirs, files in os.walk(path_to_robots):
    for name in files:
        path = os.path.join(address, name)
        path_to_model.append(path)

for path in path_to_model:
    if 'ig11_eth' in path:
        with open(path, "r") as input_file:
            config = json.load(input_file)

        last_feature_idx = preprocess_kernel_config(config["model"]["target_kernel"], 0)
        for kernel_config in config["model"]["additional_kernels"]:
            last_feature_idx = preprocess_kernel_config(kernel_config, last_feature_idx)

        config["model"]["indicate_step_us"] = 0
        config["model"]["feature_generation_mode"] = False

        for idx, string in enumerate(config["model"]["indicators"]["clickhouse"]["black_list"]):
            string = string.replace(".*", "%")
            config["model"]["indicators"]["clickhouse"]["black_list"][idx] = string

        for idx, string in enumerate(config["model"]["indicators"]["clickhouse"]["white_list"]):
            string = string.replace(".*", "%")
            config["model"]["indicators"]["clickhouse"]["white_list"][idx] = string

        for idx, string in enumerate(config["model"]["metrics"]["prometheus"]["black_list"]):
            string = string.replace(".*", "%")
            config["model"]["metrics"]["prometheus"]["black_list"][idx] = string

        for idx, string in enumerate(config["model"]["metrics"]["prometheus"]["white_list"]):
            string = string.replace(".*", "%")
            config["model"]["metrics"]["prometheus"]["white_list"][idx] = string

        for idx, string in enumerate(config["model"]["metrics"]["clickhouse"]["black_list"]):
            string = string.replace(".*", "%")
            config["model"]["metrics"]["clickhouse"]["black_list"][idx] = string

        for idx, string in enumerate(config["model"]["metrics"]["clickhouse"]["white_list"]):
            string = string.replace(".*", "%")
            config["model"]["metrics"]["clickhouse"]["white_list"][idx] = string

        with open(path, "w") as output_file:
            json.dump(config, output_file, indent=4)