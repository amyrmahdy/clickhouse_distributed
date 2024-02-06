import sys

from create_distributed_table import get_config, get_clickhouse_client


def truncate_shard_tables(db_truncate_info_config, client_connection, node_number):
    shards_table_name = db_truncate_info_config["TABLES"]["truncate_or_drop_shards_table_name"]
    db_name_truncate_table = None
    match node_number:
        case 1:
            db_name_truncate_table = db_truncate_info_config["DATABASES"]["shard_1_db_name"]
        case 2:
            db_name_truncate_table = db_truncate_info_config["DATABASES"]["shard_2_db_name"]
        case 3:
            db_name_truncate_table = db_truncate_info_config["DATABASES"]["shard_3_db_name"]

    query_of_truncate_shard_table = f"TRUNCATE TABLE IF EXISTS {db_name_truncate_table}.{shards_table_name}"

    client_connection.command(query_of_truncate_shard_table)

    print(f"Truncate {shards_table_name} in {db_name_truncate_table}")


def truncate_dist_table_in_clickhouse():
    user_input = input("Enter your purpose (create, truncate, drop): ")
    if user_input == "truncate":
        db_truncate_info_cfg_address = "./db_truncate_and_drop_info.ini"
        infrastructure_cfg_file_address = "./infrastructure.ini"
        db_truncate_info_config, infrastructure_config = get_config(
            db_info_config_address=db_truncate_info_cfg_address,
            infrastructure_config_address=infrastructure_cfg_file_address)
        cluster_info = infrastructure_config["CLUSTER_INFO"]
        count_of_nodes = int(cluster_info["count_of_nodes"])
        shards_table_name = db_truncate_info_config["TABLES"]["truncate_or_drop_shards_table_name"]
        print(
            "------------------------------------------------------------------------------------------------------------------------------------------")
        double_check_user_input = input(
            f"Are you sure about truncating this table in all shards?: \n**'{shards_table_name}'** \nanswer with yes or no:")
        yes_answer_list = ["yes", "YES", "Yes"]

        if double_check_user_input in yes_answer_list:
            for number_of_node in range(1, count_of_nodes + 1):
                config_of_clickhosue = infrastructure_config[f"CLICKHOUSE-{number_of_node}"]
                clichouse_client = get_clickhouse_client(config_of_clickhosue)

                truncate_shard_tables(db_truncate_info_config=db_truncate_info_config,
                                      client_connection=clichouse_client,
                                      node_number=number_of_node)
                print(f"Truncate shard table from {config_of_clickhosue}")
            print("Truncate all shard tables")
        else:
            print(
                "------------------------------------------------------------------------------------------------------------------------------------------")
            print(
                "To truncate the desired table, write its name in the db_truncate_and_drop_info.ini file and then type one of the items (YES, Yes, yes) in this step")
    else:
        print("Invalid input")
        sys.exit(1)

