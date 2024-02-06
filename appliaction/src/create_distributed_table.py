import configparser
import sys
from pathlib import Path

import clickhouse_connect


def get_config(db_info_config_address, infrastructure_config_address):
    db_info_config_file_address = Path(db_info_config_address)
    infrastructure_config_file_address = Path(infrastructure_config_address)

    db_info_config = configparser.ConfigParser()
    db_info_config.read(db_info_config_file_address)

    infrastructure_config = configparser.ConfigParser()
    infrastructure_config.read(infrastructure_config_file_address)

    return db_info_config, infrastructure_config


def get_clickhouse_client(infrastructure_config):
    server_address = infrastructure_config["address"]
    db_port = infrastructure_config['port']
    # db_user = infrastructure_config['username']
    # password = infrastructure_config['password']

    client = None
    try:
        client = clickhouse_connect.get_client(host=server_address,
                                               port=db_port,
                                               # username=db_user,
                                               # password=password
                                               )
    except Exception as e:
        # logging.exception(f"ERROR: ClickHouse DataBase Connection Exception: \n {e}")
        print(f"ERROR: ClickHouse DataBase Connection Exception: \n {e}")

    return client


def generate_create_query(db_tb_creation_info_config):
    db_name = "amir_test"
    tb_name = "tb_test"
    tb_engine = "MergeTree"
    tb_order_by = "nn"
    query_for_create_db = f"CREATE DATABASE IF NOT EXISTS {db_name}"

    query_for_create_table = f"""CREATE TABLE IF NOT EXISTS {db_name}.{tb_name} (
                            `name` Nullable(String),
                            `nn` Int32)
                            ENGINE = {tb_engine}
                            ORDER BY {tb_order_by}
                            """

    return query_for_create_db, query_for_create_table


def generate_query_for_db_create(number_of_node, db_creation_info_config):
    list_of_create_db_query = list()
    match number_of_node:
        case 1:
            db_name = db_creation_info_config["db_name"]
            dist_database_query = f"CREATE DATABASE IF NOT EXISTS {db_name}"
            shard_db_name = db_creation_info_config["shard_1_db_name"]
            shard_database_query = f"CREATE DATABASE IF NOT EXISTS {shard_db_name}"
            replica_db_name = db_creation_info_config["shard_3_db_name"]
            replica_database_query = f"CREATE DATABASE IF NOT EXISTS {replica_db_name}"
        case 2:
            db_name = db_creation_info_config["db_name"]
            dist_database_query = f"CREATE DATABASE IF NOT EXISTS {db_name}"
            shard_db_name = db_creation_info_config["shard_2_db_name"]
            shard_database_query = f"CREATE DATABASE IF NOT EXISTS {shard_db_name}"
            replica_db_name = db_creation_info_config["shard_1_db_name"]
            replica_database_query = f"CREATE DATABASE IF NOT EXISTS {replica_db_name}"
        case 3:
            db_name = db_creation_info_config["db_name"]
            dist_database_query = f"CREATE DATABASE IF NOT EXISTS {db_name}"
            shard_db_name = db_creation_info_config["shard_3_db_name"]
            shard_database_query = f"CREATE DATABASE IF NOT EXISTS {shard_db_name}"
            replica_db_name = db_creation_info_config["shard_2_db_name"]
            replica_database_query = f"CREATE DATABASE IF NOT EXISTS {replica_db_name}"

    list_of_create_db_query.append(dist_database_query)
    list_of_create_db_query.append(shard_database_query)
    list_of_create_db_query.append(replica_database_query)
    return list_of_create_db_query


def generate_query_for_shard_table_create(number_of_node, database_creation_info_config, tables_creation_info_config,
                                          fields_table_creation_info_config, indexes_shard_table):
    table_name = tables_creation_info_config["table_name"]
    shards_table_name = tables_creation_info_config["shards_table_name"]
    shard_table_engine = tables_creation_info_config["shard_table_engine"]
    partition_by_shard_table = tables_creation_info_config["partition_by_shard_table"]
    order_by_shard_table = tables_creation_info_config["order_by_shard_table"]
    primary_key_shards = tables_creation_info_config["primary_key"]
    indexes_of_shards = indexes_shard_table["indexes_in_create_query"]
    db_name_number_shard_replica_key_value = {}

    match number_of_node:
        case 1:
            db_name_number_shard_replica_key_value["1"] = database_creation_info_config["shard_1_db_name"]
            db_name_number_shard_replica_key_value["2"] = database_creation_info_config["shard_3_db_name"]
        case 2:
            db_name_number_shard_replica_key_value["1"] = database_creation_info_config["shard_2_db_name"]
            db_name_number_shard_replica_key_value["2"] = database_creation_info_config["shard_1_db_name"]
        case 3:
            db_name_number_shard_replica_key_value["1"] = database_creation_info_config["shard_3_db_name"]
            db_name_number_shard_replica_key_value["2"] = database_creation_info_config["shard_2_db_name"]

    fields = fields_table_creation_info_config["fields_and_types"]
    list_of_create_shard_table_query = list()
    for key in db_name_number_shard_replica_key_value:
        input_replication_merge_tree_zookeeper_file_address = f"/clickhouse/{{cluster01}}/{{shard0{key}}}/tables/{table_name}"
        input_replication_merge_tree_replica_number = f"{{replica0{key}}}"
        if indexes_of_shards:
            query_for_create_table = f"""CREATE TABLE IF NOT EXISTS {db_name_number_shard_replica_key_value[key]}.{shards_table_name} 
                                    ({fields},
                                    {indexes_of_shards})
                                    ENGINE = {shard_table_engine}('{input_replication_merge_tree_zookeeper_file_address}', '{input_replication_merge_tree_replica_number}')
                                    PARTITION BY {partition_by_shard_table}
                                    PRIMARY KEY {primary_key_shards}
                                    ORDER BY {order_by_shard_table}
                                    """
        else:
            query_for_create_table = f"""CREATE TABLE IF NOT EXISTS {db_name_number_shard_replica_key_value[key]}.{shards_table_name} 
                                                ({fields})
                                                ENGINE = {shard_table_engine}('{input_replication_merge_tree_zookeeper_file_address}', '{input_replication_merge_tree_replica_number}')
                                                PARTITION BY {partition_by_shard_table}
                                                PRIMARY KEY {primary_key_shards}
                                                ORDER BY {order_by_shard_table}
                                                """
        list_of_create_shard_table_query.append(query_for_create_table)
    return list_of_create_shard_table_query


def generate_query_for_dist_table_create(database_creation_info_config, tables_creation_info_config,
                                         fields_table_creation_info_config, ):
    table_name = tables_creation_info_config["table_name"]
    table_engine = tables_creation_info_config["table_engine"]
    db_name = database_creation_info_config["db_name"]
    shards_table_name = tables_creation_info_config["shards_table_name"]
    fields = fields_table_creation_info_config["fields_and_types"]
    sharding_key = tables_creation_info_config["sharding_key_of_dist_table"]
    cluster_name = tables_creation_info_config['cluster_name_conf']
    database_for_create_dist = ''

    query_for_create_table = f"""CREATE TABLE IF NOT EXISTS {db_name}.{table_name} 
                                    ({fields})
                                    ENGINE = {table_engine}({cluster_name},
                                                     '{database_for_create_dist}',
                                                     '{shards_table_name}',
                                                     {sharding_key})"""

    return query_for_create_table


def create_db(db_creation_info_config, client_connection, node_number):
    # dist_db_query, shard_db_query, replica_db_query = generate_query_for_db_create(number_of_node=node_number, db_creation_info_config=db_creation_info_config)
    list_create_db_query = generate_query_for_db_create(number_of_node=node_number,
                                                        db_creation_info_config=db_creation_info_config)
    for create_db_query in list_create_db_query:
        # print(create_db_query)
        client_connection.command(create_db_query)


def create_shard_table(database_creation_info_config, tables_creation_info_config, fields_table_creation_info_config,
                       indexes_shard_table, client_connection, node_number):
    list_create_shard_table_query = generate_query_for_shard_table_create(number_of_node=node_number,
                                                                          database_creation_info_config=database_creation_info_config,
                                                                          tables_creation_info_config=tables_creation_info_config,
                                                                          fields_table_creation_info_config=fields_table_creation_info_config,
                                                                          indexes_shard_table=indexes_shard_table)

    for create_shard_table_query in list_create_shard_table_query:
        client_connection.command(create_shard_table_query)


def create_dist_table(database_creation_info_config, tables_creation_info_config, fields_table_creation_info_config,
                      client_connection, node_number):
    create_dist_table_query = generate_query_for_dist_table_create(
        database_creation_info_config=database_creation_info_config,
        tables_creation_info_config=tables_creation_info_config,
        fields_table_creation_info_config=fields_table_creation_info_config)

    client_connection.command(create_dist_table_query)


def create_dist_table_in_clickhouse():
    user_input = input("Enter your purpose (create, truncate, drop): ")
    if user_input == "create":
        db_creation_info_cfg_address = "./db_creation_info.ini"
        infrastructure_cfg_file_address = "./infrastructure.ini"
        db_creation_info_config, infrastructure_config = get_config(
            db_info_config_address=db_creation_info_cfg_address,
            infrastructure_config_address=infrastructure_cfg_file_address)
        cluster_info = infrastructure_config["CLUSTER_INFO"]
        count_of_nodes = int(cluster_info["count_of_nodes"])

        # address = "localhost"
        # port = 3218
        # username = "default"
        # password = "example"

        # create_db_query, create_table_query = generate_create_query(db_tb_creation_info_config=db_creation_info_config)
        for number_of_node in range(1, count_of_nodes + 1):
            config_of_clickhosue = infrastructure_config[f"CLICKHOUSE-{number_of_node}"]
            clichouse_client = get_clickhouse_client(config_of_clickhosue)
            # clichouse_client = clickhouse_connect.get_client(host=address,
            #                                                  port=port)

            database_name_creation_info_config = db_creation_info_config["DATABASES"]
            tables_creation_info_config = db_creation_info_config["TABLES"]
            fields_table_creation_info_config = db_creation_info_config["FIELDS"]
            indexes_shard_table = db_creation_info_config["INDEXES"]

            # db_names = db_creation_info_config["DATABASES"]
            create_db(db_creation_info_config=database_name_creation_info_config,
                      client_connection=clichouse_client,
                      node_number=number_of_node)
            print("created dbs")
            # clichouse_client.command(create_db_query)

            # table_names = db_creation_info_config["TABLES"]
            create_shard_table(database_creation_info_config=database_name_creation_info_config,
                               tables_creation_info_config=tables_creation_info_config,
                               fields_table_creation_info_config=fields_table_creation_info_config,
                               indexes_shard_table = indexes_shard_table,
                               client_connection=clichouse_client,
                               node_number=number_of_node)
            # clichouse_client.command(create_table_query)
            print("created shard tables")

            create_dist_table(database_creation_info_config=database_name_creation_info_config,
                              tables_creation_info_config=tables_creation_info_config,
                              fields_table_creation_info_config=fields_table_creation_info_config,
                              client_connection=clichouse_client,
                              node_number=number_of_node)
            print("created dist tables")
    else:
        print("Invalid input")
        sys.exit(1)
