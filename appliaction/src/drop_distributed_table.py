import sys

from create_distributed_table import get_config, get_clickhouse_client


def drop_dist_and_shard_tables(db_drop_info_config, client_connection, node_number):
    shards_table_name = db_drop_info_config["TABLES"]["truncate_or_drop_shards_table_name"]
    cluster_name = db_drop_info_config["TABLES"]["truncate_or_drop_cluster_name"]
    db_name_drop_table = None
    match node_number:
        case 1:
            db_name_drop_table = db_drop_info_config["DATABASES"]["shard_1_db_name"]
            db_name_drop_dist_table = db_drop_info_config["DATABASES"]["db_name"]
            dist_table_name = db_drop_info_config["TABLES"]["truncate_or_drop_table_name"]
            query_of_drop_dist_table_on_cluster = f"DROP TABLE IF EXISTS {db_name_drop_dist_table}.{dist_table_name} ON CLUSTER {cluster_name} SYNC"
            client_connection.command(query_of_drop_dist_table_on_cluster)
            print(f"Drop {dist_table_name} on the cluster with dist engine")
        case 2:
            db_name_drop_table = db_drop_info_config["DATABASES"]["shard_2_db_name"]
        case 3:
            db_name_drop_table = db_drop_info_config["DATABASES"]["shard_3_db_name"]

    query_of_drop_shard_table = f"DROP TABLE IF EXISTS {db_name_drop_table}.{shards_table_name} ON CLUSTER {cluster_name} SYNC"
    client_connection.command(query_of_drop_shard_table)
    print(f"Drop {shards_table_name} in {db_name_drop_table}")


def check_data_status_in_target_table(infrastructure_config, db_drop_info_config):
    config_of_clickhouse = infrastructure_config[f"CLICKHOUSE-1"]
    clickhouse_client_for_cnt_data = get_clickhouse_client(config_of_clickhouse)

    db_name_dist_table = db_drop_info_config["DATABASES"]["db_name"]
    dist_table_name = db_drop_info_config["TABLES"]["truncate_or_drop_table_name"]
    query_of_count_in_dist_table = f"SELECT COUNT(*) FROM {db_name_dist_table}.{dist_table_name}"
    dist_table_cnt = clickhouse_client_for_cnt_data.command(query_of_count_in_dist_table)
    if dist_table_cnt == 0:
        table_empty = True
    else:
        table_empty = False
    return table_empty


def drop_dist_table_in_clickhouse():
    user_input = input("Enter your purpose (create, truncate, drop): ")
    if user_input == "drop":
        db_drop_info_cfg_address = "./db_truncate_and_drop_info.ini"
        infrastructure_cfg_file_address = "./infrastructure.ini"

        db_drop_info_config, infrastructure_config = get_config(
            db_info_config_address=db_drop_info_cfg_address,
            infrastructure_config_address=infrastructure_cfg_file_address)

        cluster_info = infrastructure_config["CLUSTER_INFO"]
        count_of_nodes = int(cluster_info["count_of_nodes"])

        dist_table_name = db_drop_info_config["TABLES"]["truncate_or_drop_table_name"]
        shards_table_name = db_drop_info_config["TABLES"]["truncate_or_drop_shards_table_name"]
        table_empty_status = check_data_status_in_target_table(infrastructure_config=infrastructure_config,
                                                               db_drop_info_config=db_drop_info_config)
        if table_empty_status:
            print(
                "------------------------------------------------------------------------------------------------------------------------------------------")
            double_check_user_input = input(
                f"This table is empty. Are you sure about drop this table in all shards and main db with distribute engine too?: \n**'{shards_table_name}'** \nanswer with yes or no:")
            yes_answer_list = ["yes", "YES", "Yes"]

            if double_check_user_input in yes_answer_list:
                for number_of_node in range(1, count_of_nodes + 1):
                    config_of_clickhosue = infrastructure_config[f"CLICKHOUSE-{number_of_node}"]
                    clichouse_client = get_clickhouse_client(config_of_clickhosue)

                    drop_dist_and_shard_tables(db_drop_info_config=db_drop_info_config,
                                               client_connection=clichouse_client,
                                               node_number=number_of_node)

                    print(f"Drop shard table from {config_of_clickhosue}")
                print("Drop all shard tables")

            else:
                print(
                    "------------------------------------------------------------------------------------------------------------------------------------------")
                print(
                    "To Drop the desired table, write its name in the db_truncate_and_drop_info.ini file and then type one of the items (YES, Yes, yes) in this step")
        else:
            print(
                "------------------------------------------------------------------------------------------------------------------------------------------")
            print(
                "This table is not empty!!! It cannot be Dropped")
            sys.exit(1)
    else:
        print("Invalid input")
        sys.exit(1)
