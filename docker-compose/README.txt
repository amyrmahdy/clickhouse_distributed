Instalation

Run following command for automate installation

```
make config up
```

-----

######################
#                    #
#    test-dist_tb    #
#                    #
######################


- Node1:

CREATE DATABASE IF NOT EXISTS raya;
CREATE DATABASE IF NOT EXISTS dwh01;
CREATE DATABASE IF NOT EXISTS dwh03;


CREATE TABLE dwh01.test_shard
(
	`nn` Int8,
	`name` String
)
ENGINE = ReplicatedMergeTree('/clickhouse/{cluster01}/{shard01}/tables/test_DISTRIBUTE',
 '{replica01}')
PARTITION BY nn
PRIMARY KEY name
ORDER BY (name);



CREATE TABLE dwh03.test_shard
(
	`nn` Int8,
	`name` String
)
ENGINE = ReplicatedMergeTree('/clickhouse/{cluster01}/{shard02}/tables/test_DISTRIBUTE',
 '{replica02}')
PARTITION BY nn
PRIMARY KEY name
ORDER BY (name);




CREATE TABLE raya.test_DISTRIBUTE
(
	`nn` Int8,
	`name` String
)
ENGINE = Distributed('dwh_3s_2r', '', 'test_shard', rand());

--------------------------------------------------------------------------------

- Node2:

CREATE DATABASE IF NOT EXISTS raya;
CREATE DATABASE IF NOT EXISTS dwh02;
CREATE DATABASE IF NOT EXISTS dwh01;



CREATE TABLE dwh02.test_shard
(
	`nn` Int8,
	`name` String
)
ENGINE = ReplicatedMergeTree('/clickhouse/{cluster01}/{shard01}/tables/test_DISTRIBUTE',
 '{replica01}')
PARTITION BY nn
PRIMARY KEY name
ORDER BY (name);


CREATE TABLE dwh01.test_shard
(
	`nn` Int8,
	`name` String
)
ENGINE = ReplicatedMergeTree('/clickhouse/{cluster01}/{shard02}/tables/test_DISTRIBUTE',
 '{replica02}')
PARTITION BY nn
PRIMARY KEY name
ORDER BY (name);


CREATE TABLE raya.test_DISTRIBUTE
(
	`nn` Int8,
	`name` String
)
ENGINE = Distributed('dwh_3s_2r', '', 'test_shard', rand());

--------------------------------------------------------------------------------

- Node3:

CREATE DATABASE IF NOT EXISTS raya;
CREATE DATABASE IF NOT EXISTS dwh03;
CREATE DATABASE IF NOT EXISTS dwh02;


CREATE TABLE dwh03.test_shard
(
	`nn` Int8,
	`name` String
)
ENGINE = ReplicatedMergeTree('/clickhouse/{cluster01}/{shard01}/tables/test_DISTRIBUTE',
 '{replica01}')
PARTITION BY nn
PRIMARY KEY name
ORDER BY (name);


CREATE TABLE dwh02.test_shard
(
	`nn` Int8,
	`name` String
)
ENGINE = ReplicatedMergeTree('/clickhouse/{cluster01}/{shard02}/tables/test_DISTRIBUTE',
 '{replica02}')
PARTITION BY nn
PRIMARY KEY name
ORDER BY (name);


CREATE TABLE raya.test_DISTRIBUTE
(
	`nn` Int8,
	`name` String
)
ENGINE = Distributed('dwh_3s_2r', '', 'test_shard', rand());

--------------------------------------------------------------------------------

## check replicate tables in all nodes:

SELECT * FROM system.replicas r ;

## check name of cluster in  db or os:
SELECT * FROM system.clusters c;

--------------------------------------------------------------------------------
- insert in dist table test in node-1

INSERT INTO raya.test_DISTRIBUTE (nn, name)
VALUES (1, 'amirhossein'), (2, 'saeed'), (3, 'mohammadreza'), (4, 'sajad'), (5, 'amir');

select * from raya.test_DISTRIBUTE;
--------------------------------------------------------------------------------

- node1:
select * from dwh01.test_shard;
- node2:
select * from dwh02.test_shard;
- node3:
select * from dwh03.test_shard;
--------------------------------------------------------------------------------

