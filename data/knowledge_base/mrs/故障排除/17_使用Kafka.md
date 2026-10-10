

## 17.1 Kafka 连接 ZooKeeper 客户端时发生断连

### 问题现象

Kafka客户端连接ZooKeeper客户端时发生断连。

客户端日志出现报错“Received event :disconnected::none: with disconnectedWriter Zookeeper”。

### 原因分析

在Kafka客户端连接Zookeeper客户端过程中，fsync操作时间过长，导致超时。

### 处理步骤

步骤1 登录ZooKeeper客户端所在节点。

cd 客户端安装目录

source bigdata_env

kinit 组件业务用户（未开启Kerberos认证集群跳过此步骤）

步骤2 执行以下命令修改文件。vim 客户端安装目录/zookeeper/conf/zoo.cfg调大文件中参数“tickTime”，“syncLimit”的值。例如调整“tickTime”为“3000”， “syncLimit”为“7”。

步骤3 保存文件，重新连接ZooKeeper客户端。

----结束

## 17.2 使用 Kafka Shell 命令无法操作 Kafka 集群

### 问题背景与现象

用户执行Kafka命令查看当前Topic信息，但发现业务执行失败。

具体信息如下：

root@Slave2bin]#./kafka-topics.sh --describe --topic example-metric1 --zookeeper
192.119.147.231:2181,192.119.147.228:2181,192.119.147.227:2181
Error while executing topic command:org.apache.zookeeper.KeeperException
$AuthFailedException:KeeperErrorCode=AuthFailedfor/brokers/topics
[2016-09-2616:58:59,873]ERRORorg.I0Itec.zkclient.exception.ZkException:org.apache.zookeeper.KeeperExcept
ion$AuthFailedException:KeeperErrorCode=AuthFailedfor/brokers/topics
atorg.I0Itec.zkclient.exception.ZkException.create(ZkException.java:68)
atorg.I0Itec.zkclient.ZkClient.retryUntilConnected(ZkClient.java:995)
atorg.I0Itec.zkclient.ZkClient.getChildren(ZkClient.java:675)
atorg.I0Itec.zkclient.ZkClient.getChildren(ZkClient.java:671)
atkafka.utils.ZkUtils.getChildrenParentMayNotExist(ZkUtils.scala:548)
atkafka.utils.ZkUtils.getAllTopics(ZkUtils.scala:798)
atkafka.admin.TopicCommand$.getTopics(TopicCommand.scala:82)
atkafka.admin.TopicCommand$.describeTopic(TopicCommand.scala:183)
atkafka.admin.TopicCommand$.main(TopicCommand.scala:66)
atkafka.admin.TopicCommand.main(TopicCommand.scala)
Causedby:org.apache.zookeeper.KeeperException$AuthFailedException:KeeperErrorCode=AuthFailedfor/
brokers/topics
atorg.apache.zookeeper.KeeperException.create(KeeperException.java:127)
atorg.apache.zookeeper.KeeperException.create(KeeperException.java:51)
atorg.apache.zookeeper.ZooKeeper.getChildren(ZooKeeper.java:2256)
atorg.apache.zookeeper.ZooKeeper.getChildren(ZooKeeper.java:2284)
atorg.I0Itec.zkclient.ZkConnection.getChildren(ZkConnection.java:114)
atorg.I0Itec.zkclient.ZkClient$4.call(ZkClient.java:678)
atorg.I0Itec.zkclient.ZkClient$4.call(ZkClient.java:675)
atorg.I0Itec.zkclient.ZkClient.retryUntilConnected(ZkClient.java:985)
...8more
(kafka.admin.TopicCommand$)

### 原因分析

用户反馈已经排查了执行此命令的账号权限，此账号具有操作Kafka组件的最高权限，不应该仍然会有权限不足的问题。

经确认执行命令有问题，访问ZooKeeper上所存放的Kafka信息，其路径（Znode）应该加上/kafka，完整的查询命令应该是：

root@Slave2bin]#./kafka-topics.sh --describe --topic example-metric1 --zookeeper 192.168.147.231:2181,192.168.147.228:2181,192.168.147.227:2181/kafka

### 解决办法

该故障属于命令操作有误，具体细节请参考Kafka Shell命令章节。
----结束

## 17.3 创建 Kafka Topic 时报错“NoAuthException”

### 问题背景与现象

在使用Kafka客户端命令创建Topic时，发现Topic无法被创建。

```batch
kafka-topics.sh --create --zookeeper 192.168.234.231:2181/kafka --replication-factor 1 --partitions 2 --
topic test
```

提示错误NoAuthException，KeeperErrorCode = NoAuth for /config/topics。

具体如下：

Error while executing topic command org.apache.zookeeper.KeeperException$NoAuthException:
KeeperErrorCode = NoAuth for /config/topics
org.I0Itec.zkclient.exception.ZkException: org.apache.zookeeper.KeeperException$NoAuthException:
KeeperErrorCode = NoAuth for /config/topics
at org.I0Itec.zkclient.exception.ZkException.create(ZkException.java:68)
at org.I0Itec.zkclient.ZkClient.retryUntilConnected(ZkClient.java:685)
at org.I0Itec.zkclient.ZkClient.create(ZkClient.java:304)
at org.I0Itec.zkclient.ZkClient.createPersistent(ZkClient.java:213)
at kafka.utils.ZkUtils$.createParentPath(ZkUtils.scala:215)
at kafka.utils.ZkUtils$.updatePersistentPath(ZkUtils.scala:338)
at kafka.admin.AdminUtils$.writeTopicConfig(AdminUtils.scala:247)

### 可能原因

用户不属于kafkaadmin组，Kafka提供安全访问接口，kafkaadmin组用户才可以进行topic删除操作。

### 原因分析

1. 使用客户端命令，打印NoAuthException异常。 使用客户端命令，打印NoAuthException异常。

Error while executing topic command org.apache.zookeeper.KeeperException$NoAuthException:
KeeperErrorCode = NoAuth for /config/topics
org.I0Itec.zkclient.exception.ZkException: org.apache.zookeeper.KeeperException$NoAuthException:
KeeperErrorCode = NoAuth for /config/topics
at org.I0Itec.zkclient.exception.ZkException.create(ZkException.java:68)
at org.I0Itec.zkclient.ZkClient.retryUntilConnected(ZkClient.java:685)
at org.I0Itec.zkclient.ZkClient.create(ZkClient.java:304)
at org.I0Itec.zkclient.ZkClient.createPersistent(ZkClient.java:213)
at kafka.utils.ZkUtils$.createParentPath(ZkUtils.scala:215)
at kafka.utils.ZkUtils$.updatePersistentPath(ZkUtils.scala:338)
at kafka.admin.AdminUtils$.writeTopicConfig(AdminUtils.scala:247)

2. 通过客户端命令klist查询当前认证用户：

[root@10-10-144-2 client]# klist
Ticket cache: FILE:/tmp/krb5cc_0
Default principal: test@HADOOP.COM

Valid starting Expires Service principal
01/25/17 11:06:48 01/26/17 11:06:45 krbtgt/HADOOP.COM@HADOOP.COM

如上例中当前认证用户为test。

3. 通过命令id查询用户组信息。
[root@10-10-144-2 client]# id test
uid=20032(test) gid=10001(hadoop) groups=10001(hadoop),9998(ficommon),10003(kafka)

### 解决办法

MRS 2.x及之前版本集群：

步骤1 登录MRS Manager。

步骤2 选择“系统设置 > 用户管理”。

步骤3 在操作用户对应的“操作”列，单击“修改”。

步骤4 为用户加入kafkaadmin组。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/d6c7d40b-b4f0-4687-9da4-937721e1f554/e327eae695c0a8833cad8aa067579364d839e54241ef47eea703477fbdc7f61c.jpg)

图 17-1 为用户加入 kafkaadmin 组

步骤5 通过命令id查询用户组信息。

```ini
[root@10-10-144-2 client]# id test
uid=20032(test) gid=10001(hadoop) groups=10001(hadoop),9998(ficommon),10002(kafkaadmin)，
10003(kafka)
```

----结束

MRS 3.x及之后版本集群：

步骤1 登录FusionInsight Manager。

步骤2 选择“系统 > 权限 > 用户”。

步骤3 在使用的用户所在行单击“修改”。

步骤4 为用户添加kafkaadmin组。单击“确定”完成修改操作。

```diff
步骤5 通过命令id查询用户组信息。
[root@10-10-144-2 client]# id test
uid=20032(test) gid=10001(hadoop) groups=10001(hadoop),9998(ficommon),10002(kafkaadmin)，
10003(kafka)
----结束
```
----结束

## 17.4 创建 Kafka Topic 时报错“NoNode for /brokers/ids”

### 问题背景与现象

在使用Kafka客户端命令创建Topic时，发现Topic无法被创建。

kafka-topics.sh --create --replication-factor 1 --partitions 2 --topic test --zookeeper
192.168.234.231:2181

提示错误NoNodeException: KeeperErrorCode = NoNode for /brokers/ids。

具体如下：

Error while executing topic command : org.apache.zookeeper.KeeperException$NoNodeException:
KeeperErrorCode = NoNode for /brokers/ids

[2017-09-17 16:35:28,520] ERROR org.I0Itec.zkclient.exception.ZkNoNodeException:
org.apache.zookeeper.KeeperException$NoNodeException: KeeperErrorCode = NoNode for /brokers/ids at org.I0Itec.zkclient.exception.ZkException.create(ZkException.java:47) at org.I0Itec.zkclient.ZkClient.retryUntilConnected(ZkClient.java:995) at org.I0Itec.zkclient.ZkClient.getChildren(ZkClient.java:675) at org.I0Itec.zkclient.ZkClient.getChildren(ZkClient.java:671) at kafka.utils.ZkUtils.getChildren(ZkUtils.scala:541) at kafka.utils.ZkUtils.getSortedBrokerList(ZkUtils.scala:176) at kafka.admin.AdminUtils$.createTopic(AdminUtils.scala:235) at kafka.admin.TopicCommand$.createTopic(TopicCommand.scala:105) at kafka.admin.TopicCommand$.main(TopicCommand.scala:60) at kafka.admin.TopicCommand.main(TopicCommand.scala)
Caused by: org.apache.zookeeper.KeeperException$NoNodeException: KeeperErrorCode = NoNode for /
brokers/ids at org.apache.zookeeper.KeeperException.create(KeeperException.java:115) at org.apache.zookeeper.KeeperException.create(KeeperException.java:51) at org.apache.zookeeper.ZooKeeper.getChildren(ZooKeeper.java:2256) at org.apache.zookeeper.ZooKeeper.getChildren(ZooKeeper.java:2284) at org.I0Itec.zkclient.ZkConnection.getChildren(ZkConnection.java:114) at org.I0Itec.zkclient.ZkClient$4.call(ZkClient.java:678) at org.I0Itec.zkclient.ZkClient$4.call(ZkClient.java:675) at org.I0Itec.zkclient.ZkClient.retryUntilConnected(ZkClient.java:985) ... 8 more
(kafka.admin.TopicCommand$)

### 可能原因

● Kafka服务处于停止状态。

● 客户端命令中ZooKeeper地址参数配置错误。

### 原因分析

使用客户端命令，打印NoNodeException异常。
Error while executing topic command : org.apache.zookeeper.KeeperException$NoNodeException:
KeeperErrorCode = NoNode for /brokers/ids
[2017-09-17 16:35:28,520] ERROR org.I0Itec.zkclient.exception.ZkNoNodeException:
org.apache.zookeeper.KeeperException$NoNodeException: KeeperErrorCode = NoNode for /brokers/ids
at org.I0Itec.zkclient.exception.ZkException.create(ZkException.java:47)
at org.I0Itec.zkclient.ZkClient.retryUntilConnected(ZkClient.java:995)
at org.I0Itec.zkclient.ZkClient.getChildren(ZkClient.java:675)
at org.I0Itec.zkclient.ZkClient.getChildren(ZkClient.java:671)
at kafka.utils.ZkUtils.getChildren(ZkUtils.scala:541)
at kafka.utils.ZkUtils.getSortedBrokerList(ZkUtils.scala:176)
at kafka.admin.AdminUtils$.createTopic(AdminUtils.scala:235)
at kafka.admin.TopicCommand$.createTopic(TopicCommand.scala:105)
at kafka.admin.TopicCommand$.main(TopicCommand.scala:60)
at kafka.admin.TopicCommand.main(TopicCommand.scala)

2. 通过Manager查看Kafka服务是否处于正常状态。

3. 检查客户端命令中ZooKeeper地址是否正确，访问ZooKeeper上所存放的Kafka信息，其路径（Znode）应该加上/kafka，发现配置中缺少/kafka：[root@10-10-144-2 client]#kafka-topics.sh --create --replication-factor 1 --partitions 2 --topic test --zookeeper192.168.234.231:2181

### 解决办法

步骤1 保证Kafka服务处于正常状态。

步骤2 创建命令中ZooKeeper地址信息需要添加/kafka。[root@10-10-144-2 client]#kafka-topics.sh --create --replication-factor 1 --partitions 2 --topic test --zookeeper192.168.234.231:2181/kafka

----结束

## 17.5 创建 Kafka Topic 时报错“replication factor largerthan available brokers”

### 问题背景与现象

在使用Kafka客户端命令创建Topic时，发现Topic无法被创建。

kafka-topics.sh --create --replication-factor 2 --partitions 2 --topic test --zookeeper 192.168.234.231:2181

提示错误replication factor larger than available brokers。

具体如下：

Error while executing topic command : replication factor: 2 larger than available brokers: 0
[2017-09-17 16:44:12,396] ERROR kafka.admin.AdminOperationException: replication factor: 2 larger than
available brokers: 0 at kafka.admin.AdminUtils$.assignReplicasToBrokers(AdminUtils.scala:117) at kafka.admin.AdminUtils$.createTopic(AdminUtils.scala:403) at kafka.admin.TopicCommand$.createTopic(TopicCommand.scala:110) at kafka.admin.TopicCommand$.main(TopicCommand.scala:61) at kafka.admin.TopicCommand.main(TopicCommand.scala)
(kafka.admin.TopicCommand$)

### 可能原因

● Kafka服务处于停止状态。

● Kafka服务当前可用Broker小于设置的replication-factor。

● 客户端命令中ZooKeeper地址参数配置错误。

### 原因分析

1. 使用客户端命令，打印replication factor larger than available brokers异常。Error while executing topic command : replication factor: 2 larger than available brokers: 0[2017-09-17 16:44:12,396] ERROR kafka.admin.AdminOperationException: replication factor: 2 largerthan available brokers: 0at kafka.admin.AdminUtils$.assignReplicasToBrokers(AdminUtils.scala:117)at kafka.admin.AdminUtils$.createTopic(AdminUtils.scala:403)at kafka.admin.TopicCommand$.createTopic(TopicCommand.scala:110)at kafka.admin.TopicCommand$.main(TopicCommand.scala:61)at kafka.admin.TopicCommand.main(TopicCommand.scala)(kafka.admin.TopicCommand$)

2. 通过Manager参看Kafka服务是否处于正常状态，当前可用Broker是否小于设置的replication-factor。

3. 检查客户端命令中ZooKeeper地址是否正确，访问ZooKeeper上所存放的Kafka信息，其路径（Znode）应该加上/kafka，发现配置中缺少/kafka。[root@10-10-144-2 client]#kafka-topics.sh --create --replication-factor 2 --partitions 2 --topic test --zookeeper192.168.234.231:2181

### 解决办法

步骤1 保证Kafka服务处于正常状态，且可用Broker不小于设置的replication-factor。

步骤2 创建命令中ZooKeeper地址信息需要添加/kafka。

[root@10-10-144-2 client]#
kafka-topics.sh --create --replication-factor 1 --partitions 2 --topic test --zookeeper
192.168.234.231:2181/kafka

----结束

## 17.6 创建 Kafka Topic 时，发现 Partition 的 Leader 显示为 none

### 问题背景与现象

在使用Kafka客户端命令创建Topic时，发现创建Topic Partition的Leader显示为none。

[root@10-10-144-2 client]#
kafka-topics.sh --create --replication-factor 1 --partitions 2 --topic test --zookeeper 10.6.92.36:2181/
kafka

Created topic "test".

[root@10-10-144-2 client]# kafka-topics.sh --describe --zookeeper 10.6.92.36:2181/kafka

Topic:test PartitionCount:2 ReplicationFactor:2 Configs: Topic: test Partition: 0 Leader: none Replicas: 2,3 Isr: Topic: test Partition: 1 Leader: none Replicas: 3,1 Isr:

### 可能原因

● Kafka服务处于停止状态。

● 找不到用户组信息。

### 原因分析

1. 查看Kafka服务状态：

MRS Manager界面操作：登录MRS Manager，依次选择“服务管理 >Kafka”，查看当前Kafka状态，发现状态为良好，且监控指标内容显示正确。

FusionInsight Manager界面操作：登录FusionInsight Manager，选择“集群 > 服务 > Kafka”，查看当前Kafka状态，发现状态为良好，且监控指标内容显示正确。

2. 在Kafka概览页面获取Controller节点信息。

3. 登录Controller所在节点，通过cd /var/log/Bigdata/kafka/broker命令进入节点日志目录，在state-change.log发现存在ZooKeeper权限异常，提示NoAuthException。

```csv
2018-05-31 09:20:42,436 | ERROR | [ZkClient-
EventThread-34-10.6.92.36:24002,10.6.92.37:24002,10.6.92.38:24002/kafka] | Controller 4 epoch 6
initiated state change for partition [test,1] from NewPartition to OnlinePartition failed |
state.change.logger (Logging.scala:103)
```

org.I0Itec.zkclient.exception.ZkException: org.apache.zookeeper.KeeperException$NoAuthException:
KeeperErrorCode = NoAuth for /brokers/topics/test/partitions
at org.I0Itec.zkclient.exception.ZkException.create(ZkException.java:68)
at org.I0Itec.zkclient.ZkClient.retryUntilConnected(ZkClient.java:1000)
at org.I0Itec.zkclient.ZkClient.create(ZkClient.java:527)
at org.I0Itec.zkclient.ZkClient.createPersistent(ZkClient.java:293)

4. 查看对应时间段ZooKeeper审计日志，权限异常。

2018-05-31 09:20:42,421 | ERROR | CommitProcWorkThread-1 | session=0xc3000007015d5a18
user=10.6.92.39,kafka/hadoop.hadoop.com@HADOOP.COM,kafka/
hadoop.hadoop.com@HADOOP.COM ip=10.6.92.39 operation=create znode
target=ZooKeeperServer znode=/kafka/brokers/topics/test/partitions/0/state result=failure
2018-05-31 09:20:42,423 | ERROR | CommitProcWorkThread-1 | session=0xc3000007015d5a18
user=10.6.92.39,kafka/hadoop.hadoop.com@HADOOP.COM,kafka/
hadoop.hadoop.com@HADOOP.COM ip=10.6.92.39 operation=create znode
target=ZooKeeperServer znode=/kafka/brokers/topics/test/partitions/0 result=failure
2018-05-31 09:20:42,435 | ERROR | CommitProcWorkThread-1 | session=0xc3000007015d5a18
user=10.6.92.39,kafka/hadoop.hadoop.com@HADOOP.COM,kafka/
hadoop.hadoop.com@HADOOP.COM ip=10.6.92.39 operation=create znode
target=ZooKeeperServer znode=/kafka/brokers/topics/test/partitions result=failure
2018-05-31 09:20:42,439 | ERROR | CommitProcWorkThread-1 | session=0xc3000007015d5a18
user=10.6.92.39,kafka/hadoop.hadoop.com@HADOOP.COM,kafka/
hadoop.hadoop.com@HADOOP.COM ip=10.6.92.39 operation=create znode
target=ZooKeeperServer znode=/kafka/brokers/topics/test/partitions/1/state result=failure
2018-05-31 09:20:42,441 | ERROR | CommitProcWorkThread-1 | session=0xc3000007015d5a18
user=10.6.92.39,kafka/hadoop.hadoop.com@HADOOP.COM,kafka/
hadoop.hadoop.com@HADOOP.COM ip=10.6.92.39 operation=create znode
target=ZooKeeperServer znode=/kafka/brokers/topics/test/partitions/1 result=failure
2018-05-31 09:20:42,453 | ERROR | CommitProcWorkThread-1 | session=0xc3000007015d5a18
user=10.6.92.39,kafka/hadoop.hadoop.com@HADOOP.COM,kafka/
hadoop.hadoop.com@HADOOP.COM ip=10.6.92.39 operation=create znode
target=ZooKeeperServer znode=/kafka/brokers/topics/test/partitions result=failure

5. 在ZooKeeper各个实例节点上执行id -Gn kafka命令，发现有一个节点无法查询用户组信息。

6. MRS集群中的用户管理由LDAP服务管理提供，又依赖于操作系统的sssd或nscd服务，用户的建立到同步到sssd服务需要一定时间，如果此时用户没有生效，或者sssd版本存在bug的情况下，某些情况下在ZooKeeper节点会出现用户无效的情况，导致创建Topic异常。

### 解决办法

步骤1 重启sssd/nscd服务。

● Red Hat/Euler

service sssd restart

● SUSE service nscd restart

步骤2 重启相关服务后，在节点通过id username命令查看相应用户信息是否已有效。

----结束

## 17.7 获取 Kafka Topic 时报错“InvalidReplicationFactorException”

### 问题现象

运行Kafka客户端获取Topic时报错，报错内容如下：

ERROR org.apache.kafka.common.errors.InvalidReplicationFactorException: Replication factor: 2 larger than available brokers: 0.

### 原因分析

由特殊字符导致获取的ZooKeeper地址变量错误。

### 处理步骤

步骤1 登录任意一个Master节点。

步骤2 执行以下命令，查看ZooKeeper地址的变量信息。

cat 客户端安装目录/Kafka/kafka/config/server.properties |grep '^zookeeper.connect ='

步骤3 重新运行Kafka获取Topic，其中从步骤2中获取的变量不要添加任何字符。

----结束

## 17.8 删除 Kafka Topic 时发现无法删除

### 问题描述

在使用以下Kafka客户端命令删除Topic时（例如Topic名称为“test”），发现Topic无法被删除。

kafka-topics.sh --delete --topic test --zookeeper x.x.x.x:port/kafka

### 可能原因

Kafka服务异常，Kafka部分节点处于停止或故障状态。具体处理步骤请参考Kafka节点状态异常。

客户端命令连接ZooKeeper地址错误，报错“ZkTimeoutException”。具体处理步骤请参考客户端命令连接ZooKeeper地址错误。

Kafka服务端配置禁止删除（“delete.topic.enable”参数值配置为“false”）。
具体处理步骤请参考Kafka服务端配置禁止删除。

Kafka配置自动创建（“auto.create.topics.enable”参数值配置为“true”），且Producer未停止。具体处理步骤请参考Kafka配置自动创建，且Producer未停止。

### 处理步骤

出现该问题的可能原因及处理步骤有以下几种：

Kafka 节点状态异常

- 原因分析

Topic进行删除必须保证该Topic的所有Partition所在的Broker必须处于正常状态。

a. 登录MRS集群Manager页面，选择“集群 > 服务 > Kafka > 实例”，查看Broker实例状态。

发现其中一个Broker处于停止或者故障状态。

b. 客户端查询命令：

kafka-topics.sh --describe -topic test --zookeeper x.x.x.x:port/kafka

<table><tr><td colspan="2">Topic:test</td><td colspan="2">PartitionCount:10 Partition: 0</td><td colspan="2">ReplicationFactor:2 Configs: Replicas: 1,2 Isr:</td></tr><tr><td>Topic: test Topic: test Topic: test Topic: test Topic: test Topic: test</td><td>Topic: test Topic: test Topic: test</td><td>Partition: 1 Partition: 2 Partition: 3 Partition: 4 Partition: 5 Partition: 6 Partition: 7 Partition: 8</td><td>Leader: -1 Leader: -1 Leader: -1 Leader: -1 Leader: -1 Leader: -1 Leader: -1 Leader: -1 Leader: -1</td><td>Replicas: 2,3 Isr: Replicas: 3,1 Isr: Replicas: 1,3 Isr: Replicas: 2,1 Isr: Replicas: 3,2 Isr: Replicas: 1,2 Isr: Replicas: 2,3 Isr: Replicas: 3,1 Isr:</td></tr></table>

进入RunningAsController节点日志目录，在controller.log发现markedineligible for deletion。

2016-03-10 11:11:17,989 | INFO | [delete-topics-thread-3] | [delete-topics-thread-3], Handling deletion for topics test | kafka.controller.TopicDeletionManager$DeleteTopicsThread (Logging.scala:68)

2016-03-10 11:11:17,990 | INFO | [delete-topics-thread-3] | [delete-topics-thread-3], Not retrying deletion of topic test at this time since it is marked ineligible for deletion | kafka.controller.TopicDeletionManager$DeleteTopicsThread (Logging.scala:68)

- 处理步骤

a. 启动停止的Broker实例。

b. 执行客户端查询命令，无Topic:test。

kafka-topics.sh --list --zookeeper x.x.x.x:port/kafka

c. 进入RunningAsController节点日志目录，在controller.log发现Deletion oftopic test successfully，表示已删除成功。 topic test successfully，表示已删除成功。

2016-03-10 11:17:56,463 | INFO | [delete-topics-thread-3] | [Partition state machine on
Controller 3]: Invoking state change to NonExistentPartition for partitions [test,4],[test,1],
[test,8],[test,2],[test,5],[test,9],[test,7],[test,6],[test,0],[test,3] |
kafka.controller.PartitionStateMachine (Logging.scala:68)
2016-03-10 11:17:56,726 | INFO | [delete-topics-thread-3] | [delete-topics-thread-3], Deletion
of topic test successfully completed | kafka.controller.TopicDeletionManager$DeleteTopicsThread
(Logging.scala:68)

客户端命令连接 ZooKeeper 地址错误

- 原因分析

执行客户端命令后，打印ZkTimeoutException异常，例如报错如下：

[2016-03-09 10:41:45,773] WARN Can not get the principle name from server 192.168.234.231 (org.apache.zookeeper.ClientCnxn)

Exception in thread "main" org.I0Itec.zkclient.exception.ZkTimeoutException: Unable to connect to zookeeper server within timeout: 30000

at org.I0Itec.zkclient.ZkClient.connect(ZkClient.java:880)

at org.I0Itec.zkclient.ZkClient.<init>(ZkClient.java:98)

at org.I0Itec.zkclient.ZkClient.<init>(ZkClient.java:84)

at kafka.admin.TopicCommand$.main(TopicCommand.scala:51)

at kafka.admin.TopicCommand.main(TopicCommand.scala)

- 处理步骤

Kafka客户端连接ZooKeeper服务超时。检查客户端到ZooKeeper的网络连通性。

a. 通过登录Manager界面，选择“集群 > 服务 > ZooKeeper > 实例”，查看ZooKeeper角色实例的业务IP地址。

b. 发现客户端命令中的IP地址配置错误，修改客户端命令中ZooKeeper地址。

c. 再次执行delete操作。

Kafka服务端配置禁止删除

- 原因分析

a. 在客户端执行以下查询命令。

kafka-topics.sh --list --zookeeper x.x.x.x:port/kafka

cd /var/log/Bigdata/kafka/broker

通过Manager查看Kafka Broker实例的运行状态。

执行以下命令进入RunningAsController节点日志目录：

2016-03-09 11:11:26,228 | INFO | [main] | [Controller 1]: List of topics to be deleted: |
kafka.controller.KafkaController (Logging.scala:68)
2016-03-09 11:11:26,229 | INFO | [main] | [Controller 1]: List of topics ineligible for deletion:
test | kafka.controller.KafkaController (Logging.scala:68)

b. 登录MRS集群Manager页面，选择“集群 > 服务 > Kafka > 配置 > 全部配置”，搜索并查看“delete.topic.enable”参数，发现参数配置值为“false”，表示服务端配置了禁止删除。

- 处理步骤

a. 登录MRS集群Manager页面，选择“集群 > 服务 > Kafka > 配置 > 全部配置”，搜索“delete.topic.enable”参数。

修改参数取值为“true”保存配置后，重启Kafka服务。

b. 通过客户端执行以下查询命令，无Topic:test。kafka-topics.sh --list --zookeeper x.x.x.x:port/kafka

进入RunningAsController节点日志目录，在controller.log发现Deletion oftopic test successfully，表示已删除成功。

```csv
2016-03-10 10:39:40,665 | INFO | [delete-topics-thread-3] | [Partition state machine on
Controller 3]: Invoking state change to OflinePartition for partitions [test,2],[test,15],[test,6],
[test,16],[test,12],[test,7],[test,10],[test,13],[test,9],[test,19],[test,3],[test,5],[test,1],[test,0],
[test,17],[test,8],[test,4],[test,11],[test,14],[test,18] | kafka.controller.PartitionStateMachine
(Logging.scala:68)
2016-03-10 10:39:40,668 | INFO | [delete-topics-thread-3] | [Partition state machine on
Controller 3]: Invoking state change to NonExistentPartition for partitions [test,2],[test,15],
[test,6],[test,16],[test,12],[test,7],[test,10],[test,13],[test,9],[test,19],[test,3],[test,5],[test,1],
[test,0],[test,17],[test,8],[test,4],[test,11],[test,14],[test,18] |
kafka.controller.PartitionStateMachine (Logging.scala:68)
2016-03-10 10:39:40,977 | INFO | [delete-topics-thread-3] | [delete-topics-thread-3], Deletion
of topic test successfully completed | kafka.controller.TopicDeletionManager$DeleteTopicsThread
(Logging.scala:68)
```

Kafka 配置自动创建，且 Producer 未停止

- 原因分析

a. 执行以下命令进入RunningAsController节点日志目录：cd /var/log/Bigdata/kafka/broker

在controller.log发现Deletion successfully，然后又出现New topics:[Set(test)]，表明被再次创建。

2016-03-10 11:33:35,208 | INFO | [delete-topics-thread-3] | [delete-topics-thread-3], Deletion of topic test successfully completed | kafka.controller.TopicDeletionManager$DeleteTopicsThread (Logging.scala:68)

2016-03-10 11:33:38,501 | INFO | [ZkClient-
EventThread-19-192.168.0.122:2181,160.172.0.52:2181,160.172.0.51:2181/kafka] |
[TopicChangeListener on Controller 3]: New topics: [Set(test)], deleted topics: [Set()], new
partition replica assignment

b. 登录MRS集群Manager页面，选择“集群 > 服务 > Kafka > 配置 > 全部配置”，搜索并查看“auto.create.topics.enable”参数，发现参数配置值为“true”，表示Kafka配置了自动创建。

c. 经确认，对该Topic操作的应用没有停止。

- 处理步骤

a. 停止相关应用。

b. 登录MRS集群Manager页面，选择“集群 > 服务 > Kafka > 配置 > 全部配置”，搜索“auto.create.topics.enable”参数。

修改参数取值为“false”保存配置后，重启Kafka服务。
----结束

## 17.9 删除 Kafka Topic 时报错“AdminOperationException” 7

### 问题描述

在使用以下Kafka客户端命令删除Topic时报错。

kafka-topics.sh --delete --topic test4 --zookeeper 10.5.144.2:2181/kafka

提示错误ERROR kafka.admin.AdminOperationException: Error while deleting topictest4。

具体如下：

Error while executing topic command : Error while deleting topic test4
[2017-01-25 14:00:20,750] ERROR kafka.admin.AdminOperationException: Error while deleting topic test4
at kafka.admin.TopicCommand$$anonfun$deleteTopic$1.apply(TopicCommand.scala:177)
at kafka.admin.TopicCommand$$anonfun$deleteTopic$1.apply(TopicCommand.scala:162)
at scala.collection.mutable.ResizableArray$class.foreach(ResizableArray.scala:59)
at scala.collection.mutable.ArrayBufer.foreach(ArrayBufer.scala:47)
at kafka.admin.TopicCommand$.deleteTopic(TopicCommand.scala:162)
at kafka.admin.TopicCommand$.main(TopicCommand.scala:68)
at kafka.admin.TopicCommand.main(TopicCommand.scala)
(kafka.admin.TopicCommand$)

### 可能原因

用户不属于kafkaadmin组，Kafka提供安全访问接口，kafkaadmin组用户才可以进行topic删除操作。

### 原因分析

1. 使用客户端命令，打印AdminOperationException异常。

2. 通过客户端命令klist查询当前认证用户：[root@10-10-144-2 client]# klistTicket cache: FILE:/tmp/krb5cc_0Default principal: test@HADOOP.COMValid starting Expires Service principal01/25/17 11:06:48 01/26/17 11:06:45 krbtgt/HADOOP.COM@HADOOP.COM如上例中当前认证用户为test。

3. 通过命令id查询用户组信息[root@10-10-144-2 client]# id testuid=20032(test) gid=10001(hadoop) groups=10001(hadoop),9998(ficommon),10003(kafka)

### 处理步骤

MRS 2.x及之前版本：

步骤1 登录MRS Manager。

步骤2 选择“系统设置 > 用户管理”。

步骤3 在操作用户对应的“操作”列，单击“修改”。

步骤4 为用户加入kafkaadmin组。单击“确定”完成修改操作。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/d6c7d40b-b4f0-4687-9da4-937721e1f554/19cd39f54e8704e831d9b7727a3390ca06688d2917b826e1119a953eb20c26e6.jpg)

图17-2 修改用户信息

步骤5 通过命令id查询用户组信息。

```ini
[root@10-10-144-2 client]# id test
uid=20032(test) gid=10001(hadoop) groups=10001(hadoop),9998(ficommon),10002(kafkaadmin)，
10003(kafka)
```

----结束

MRS 3.x及之后版本：

步骤1 登录FusionInsight Manager。

步骤2 选择“系统 > 权限 > 用户”。

步骤3 在使用的用户所在行单击“修改”。

步骤4 为用户添加kafkaadmin组。单击“确定”完成修改操作。

步骤5 通过命令id查询用户组信息。
[root@10-10-144-2 client]# id test
uid=20032(test) gid=10001(hadoop) groups=10001(hadoop),9998(ficommon),10002(kafkaadmin)，
10003(kafka)

----结束

## 17.10 设置 Kafka Topic ACL 权限时报错“NoAuthException”

### 问题描述

在使用Kafka客户端命令设置Topic ACL权限时，发现Topic无法被设置。

kafka-acls.sh --authorizer-properties zookeeper.connect=10.5.144.2:2181/kafka --topic topic_acl --producer --add --allow-principal User:test_acl

提示错误NoAuthException: KeeperErrorCode = NoAuth for /kafka-acl-changes/acl_changes_0000000002。

具体如下：

Error while executing ACL command: org.apache.zookeeper.KeeperException$NoAuthException:
KeeperErrorCode = NoAuth for /kafka-acl-changes/acl_changes_0000000002
org.I0Itec.zkclient.exception.ZkException: org.apache.zookeeper.KeeperException$NoAuthException:
KeeperErrorCode = NoAuth for /kafka-acl-changes/acl_changes_0000000002
at org.I0Itec.zkclient.exception.ZkException.create(ZkException.java:68)
at org.I0Itec.zkclient.ZkClient.retryUntilConnected(ZkClient.java:995)
at org.I0Itec.zkclient.ZkClient.delete(ZkClient.java:1038)
at kafka.utils.ZkUtils.deletePath(ZkUtils.scala:499)
at kafka.common.ZkNodeChangeNotificationListener$$anonfun$purgeObsoleteNotifications
$1.apply(ZkNodeChangeNotificationListener.scala:118)
at kafka.common.ZkNodeChangeNotificationListener$$anonfun$purgeObsoleteNotifications
$1.apply(ZkNodeChangeNotificationListener.scala:112)
at scala.collection.mutable.ResizableArray$class.foreach(ResizableArray.scala:59)
at scala.collection.mutable.ArrayBufer.foreach(ArrayBufer.scala:47)
at
kafka.common.ZkNodeChangeNotificationListener.purgeObsoleteNotifications(ZkNodeChangeNotificationLis
tener.scala:112)
at kafka.common.ZkNodeChangeNotificationListener.kafka$common$ZkNodeChangeNotificationListener$
$processNotifications(ZkNodeChangeNotificationListener.scala:97)
at
kafka.common.ZkNodeChangeNotificationListener.processAllNotifications(ZkNodeChangeNotificationListener
.scala:77)
at kafka.common.ZkNodeChangeNotificationListener.init(ZkNodeChangeNotificationListener.scala:65)
at kafka.security.auth.SimpleAclAuthorizer.configure(SimpleAclAuthorizer.scala:136)
at kafka.admin.AclCommand$.withAuthorizer(AclCommand.scala:73)
at kafka.admin.AclCommand$.addAcl(AclCommand.scala:80)
at kafka.admin.AclCommand$.main(AclCommand.scala:48)
at kafka.admin.AclCommand.main(AclCommand.scala)
Caused by: org.apache.zookeeper.KeeperException$NoAuthException: KeeperErrorCode = NoAuth for /kafka
acl-changes/acl_changes_0000000002
at org.apache.zookeeper.KeeperException.create(KeeperException.java:117)
at org.apache.zookeeper.KeeperException.create(KeeperException.java:51)
at org.apache.zookeeper.ZooKeeper.delete(ZooKeeper.java:1416)
at org.I0Itec.zkclient.ZkConnection.delete(ZkConnection.java:104)
at org.I0Itec.zkclient.ZkClient$11.call(ZkClient.java:1042)
at org.I0Itec.zkclient.ZkClient.retryUntilConnected(ZkClient.java:985)

### 可能原因

用户不属于kafkaadmin组，Kafka提供安全访问接口，kafkaadmin组用户才可以进行设置操作。

### 原因分析

1. 使用客户端命令，打印NoAuthException异常。

通过客户端命令klist查询当前认证用户：
[root@10-10-144-2 client]# klist
Ticket cache: FILE:/tmp/krb5cc_0
Default principal: test@HADOOP.COM
Valid starting Expires Service principal
01/25/17 11:06:48 01/26/17 11:06:45 krbtgt/HADOOP.COM@HADOOP.COM如上例中当前认证用户为test。

3. 通过命令id查询用户组信息。[root@10-10-144-2 client]# id testuid=20032(test) gid=10001(hadoop) groups=10001(hadoop),9998(ficommon),10003(kafka)

### 处理步骤

MRS 2.x及之前版本：

步骤1 登录MRS Manager。

步骤2 选择“系统设置 > 用户管理”。

步骤3 在操作用户对应的“操作”列，单击“修改”。

步骤4 为用户加入kafkaadmin组。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/d6c7d40b-b4f0-4687-9da4-937721e1f554/f7518f00576892df4509561f8c09a6ae60c330453dad56db637e8a943cb88994.jpg)

图17-3 修改用户组

步骤5 通过命令id查询用户组信息。

[root@host1 client]# id test
uid=20032(test) gid=10001(hadoop) groups=10001(hadoop),9998(ficommon),10002(kafkaadmin)，
10003(kafka)

----结束

MRS 3.x及之后版本：

步骤1 登录FusionInsight Manager。

步骤2 选择“系统 > 权限 > 用户”。

步骤3 在使用的用户所在行单击“修改”。

步骤4 为用户添加kafkaadmin组。单击“确定”完成修改操作。

步骤5 通过命令id查询用户组信息。

```ini
[root@10-10-144-2 client]# id test
uid=20032(test) gid=10001(hadoop) groups=10001(hadoop),9998(ficommon),10002(kafkaadmin)，
10003(kafka)
```

----结束

## 17.11 Producer 发送数据失败，报错“NullPointerException”

### 问题现象

使用MRS安装集群，主要安装ZooKeeper、Kafka。

在使用Producer向Kafka发送数据功能时，发现客户端报错NullPointerException。

### 可能原因

1. Kafka服务异常。

2. 客户端Producer侧jaas文件和keytab文件错误。

### 原因分析

Producer发送数据到Kafka失败，可能原因为客户端Producer侧问题或者Kafka侧问题。

1. 通过Manager页面查看Kafka服务状态及监控指标。

MRS Manager界面操作：登录MRS Manager，依次选择“服务管理 >Kafka”，查看当前Kafka状态，发现状态为良好，且监控指标内容显示正确。

FusionInsight Manager界面操作：登录FusionInsight Manager，选择“集群 > 服务 > Kafka”，查看当前Kafka状态，发现状态为良好，且监控指标内容显示正确。

2. 查看Producer客户端日志，发现打印NullPointerException异常信息，如图17-4所示。

图 17-4 Producer 客户端日志

[2016-12-06 02:04:05,906]-[schedule-C50D0717-4643-4D4E-9D6E-B940E4BD7159]-[kafka-producer-network-thread |
szx1000161910-10.21.219.222-bigdata-producer-5]-[1005]-[org-apache.kafka.clients.producer.internals.Sender.run
thread:
java.lang.NullPointerException
at org.apache.kafka.common.network.Selector.pollSelectionKeys(Selector.java:302)
at org.apache.kafka.common.network.Selector.poll(Selector.iava:283)
at org-apache.kafka.clients.NetworkClient.poll(NetworkClient.java:260)
at org.apache.kafka.clients.producer.internals.Sender.run(Sender.java:229)
at org.apache.kafka.clients.producer.internals.Sender.run(Sender.java:134)
at java.lang.Thread.run(Thread.java:745)
[2016-12-06 02:04:05,921]-[schedule-C50D0717-4643-4D4E-9D6E-B940E4BD7159]-[kafka-producer-network-thread |
szx1000161910-10.21.219.222-bigdata-producer-3]-[1005]-[org-apache.kafka.clients.producer.internals.Sender.run
thread:
java.lang.NullPointerException
at org.apache.kafka.common.network.Selector.pollSelectionKeys(Selector.java:302)
at org.apache.kafka.common.network.Selector.poll(Selector.java:283)
at org.apache.kafka.clients.NetworkClient.poll(NetworkClient.java:260)
at org.apache.kafka.clients.producer.internals.Sender.run(Sender.java:229)
at org.apache.kafka.clients.producer.internals.Sender.run(Sender.java:134)
at java.lang.Thread.run(Thread.java:745)

或者日志中只有异常信息没有堆栈信息（只有NullPointerException无堆栈信息，出现这个问题是jdk的自我保护，相同堆栈打印太多，就会触发这个保护开关，后续不再打印堆栈），如图17-5所示。

图 17-5 异常信息
[[2016-11-23 04:06:53,973] [kafka-producer-network-thread | producer-1] [ERROR] [org.apache.kafka.clients.producer.internals.Sender] (run:130)- Uncaught error in kafka producer I/0 thread:
java.lang.NullPointerException
[2016-11-23 04:06:53,973] [kafka-producer-network-thread | producer-1] [ERROR] [org.apache.kafka.clients.producer.internals.Sender] (run:130)-Uncaught error in kafka producer I/0 thread:
java.lang.NullPointerException
[2016-11-23 04:06:53,973] [kafka-producer-network-thread | producer-1] [ERROR] [org.apache.kafka.clients.producer.internals.Sender] (run:130)- Uncaught error in kafka producer I/0 thread:
java.lang.NullPointerException
[2016-11-23 04:06:53,973] [kafka-producer-network-thread | producer-1] [ERROR] [org.apache.kafka.clients.producer.internals.Sender] (run:130)- Uncaught error in kafka producer I/0 thread:
java.lang.NullPointerException

3. 查看Producer客户端日志，发现打印Failed to configure SaslClientAuthenticator异常信息，如图17-6所示。

图 17-6 异常日志信息
Caused by: org.apache.kafka.common.KafkaException: Failed to configure SaslClientAuthenticator
at org.apache.kafka.common.security.authenticator.SaslClientAuthenticator.configure(SaslClientAuthenticator.java:96
at org.apache.kafka.common.network.SaslChannelBuilder.buildChannel(SaslChannelBuilder.java:89)
... 9 more
Caused by: org.apache.kafka.common.KafkaException: Failed to create SaslClient
at org.apache.kafka.common.security.authenticator.SaslClientAuthenticator.createSaslClient(SaslClientAuthenticator.java:112)
at org.apache.kafka.common.security.authenticator.SaslClientAuthenticator.configure(SaslClientAuthenticator.java:94)
... 10 more
Caused by: javax.security.sasl.SaslException: PLAIN: authorization ID and password must be specified
at com.sun.security.sasl.PlainClient.<init>(PlainClient.java:58)
at com.sun.security.sasl.ClientFactoryImpl.createSaslClient(ClientFactoryImpl.java:97)
at javax.security.sasl.Sasl.createSaslClient(Sasl.java:384)
at com.ibm.messagehub.login.MessageHubSaslClientFactory.createSaslClient(MessageHubSaslClientFactory.java:77)
at javax.security.sasl.Sasl.createSaslClient(Sasl.java:384)
at org.apache.kafka.common.security.authenticator.SaslClientAuthenticator$1.run(SaslClientAuthenticator.iava:107)
at org.apache.kafka.common.security.authenticator.SaslClientAuthenticator$1.run(SaslClientAuthenticator.java:102)
at java.security.AccessController.doPrivileged(Native Method)
at javax.security.auth.Subject.doAs(Subject.jaya:422)
at org.apache.kafka.common.security.authenticator.SaslClientAuthenticator.createSaslClient(SaslClientAuthenticator.java:102)
... 11 more

4. 认证失败导致创建KafkaChannel失败，导致通过channel(key)方法获取的KafkaChannel为空，以至于疯狂打印NullPointerException，上述日志可以发现，认证失败的原因是用户密码不正确，密码不正确的原因可能是用户名不匹配导致。

5. 检查Jaas文件和Keytab文件，发现Jaas文件中配置使用的principal为stream。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/d6c7d40b-b4f0-4687-9da4-937721e1f554/1013c5aa7c1728f483095474a064442be7f892a01e49c64af1432437966f05b0.jpg)

图 17-7 检查 Jaas 文件

查看user.keytab文件，发现principal为zmk_kafka。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/d6c7d40b-b4f0-4687-9da4-937721e1f554/666736afbdbe408d5ecdf1a46383a8211b07defd37b37ac6f8da2f3d3c4f9a0b.jpg)

图 17-8 查看 user.keytab 文件

发现jaas文件和user.keytab文件中principal不对应。

该情况是由于应用程序自动定时更新Jaas文件，但是有两个不同的进程在进行更新，一个进程写入正确的Principal而另一个却写入了错误的Principal，以至于程序时而正常，时而异常。

### 解决办法

步骤1 修改Jaas文件，确保使用的Principal在Keytab文件中存在。

----结束

## 17.12 Producer 发送数据失败，报错“TOPIC\_AUTHORIZATION\_FAILED

### 问题现象

使用MRS安装集群，主要安装ZooKeeper、Kafka。

在使用Producer向Kafka发送数据功能时，发现客户端报错：TOPIC_AUTHORIZATION_FAILED。

### 可能原因

1. Kafka服务异常。

2. 客户端Producer侧采用非安全访问，服务端配置禁止访问。

3. 客户端Producer侧采用非安全访问，Kafka Topic设置ACL。

### 原因分析

Producer发送数据到Kafka失败，可能原因为客户端Producer侧问题或者Kafka侧问题。

1. 查看Kafka服务状态：

MRS Manager界面操作：登录MRS Manager，依次选择“服务管理 >Kafka”，查看当前Kafka状态，发现状态为良好，且监控指标内容显示正确。

FusionInsight Manager界面操作：登录FusionInsight Manager，选择“集群 > 服务 > Kafka”，查看当前Kafka状态，发现状态为良好，且监控指标内容显示正确。

2. 查看Producer客户端日志，发现打印TOPIC_AUTHORIZATION_FAILED异常信息。

[root@10-10-144-2 client]# kafka-console-producer.sh --broker-list 10.5.144.2:9092 --topic test [2017-01-24 16:58:36,671] WARN Error while fetching metadata with correlation id 0 : {test=TOPIC_AUTHORIZATION_FAILED} (org.apache.kafka.clients.NetworkClient)

[2017-01-24 16:58:36,672] ERROR Error when sending message to topic test with key: null, value: 1
bytes with error: Not authorized to access topics: [test]
(org.apache.kafka.clients.producer.internals.ErrorLoggingCallback)

Producer采用9092端口来访问Kafka，9092为非安全端口。

3. 通过Manager页面，查看当前Kafka集群配置，发现未设置自定义配置“allow.everyone.if.no.acl.found”=“false”。

MRS Manager界面操作入口：登录MRS Manager，依次选择“服务管理 >Kafka> 配置”。

FusionInsight Manager界面操作入口：登录FusionInsight Manager，选择“集群 > 服务 > Kafka > 配置”。

4. 当ACL设置为false不允许采用9092来进行访问。

5. 查看Producer客户端日志，发现打印TOPIC_AUTHORIZATION_FAILED异常信息。[root@10-10-144-2 client]# kafka-console-producer.sh --broker-list 10.5.144.2:21005 --topic test_acl1[2017-01-25 11:09:40,012] WARN Error while fetching metadata with correlation id 0 :{test_acl=TOPIC_AUTHORIZATION_FAILED} (org.apache.kafka.clients.NetworkClient)[2017-01-25 11:09:40,013] ERROR Error when sending message to topic test_acl with key: null, value:1 bytes with error: Not authorized to access topics: [test_acl](org.apache.kafka.clients.producer.internals.ErrorLoggingCallback)[2017-01-25 11:14:40,010] WARN Error while fetching metadata with correlation id 1 :{test_acl=TOPIC_AUTHORIZATION_FAILED} (org.apache.kafka.clients.NetworkClient)Producer采用21005端口来访问Kafka，21005为非安全端口。

6. 通过客户端命令查看topic的ACL权限设置信息。[root@10-10-144-2 client]# kafka-acls.sh --authorizer-properties zookeeper.connect=10.5.144.2:24002/kafka --list --topic topic_aclCurrent ACLs for resource \`Topic:topic_acl\`:User:test_user has Allow permission for operations: Describe from hosts: *User:test_user has Allow permission for operations: Write from hosts: *

Topic设置ACL，则不允许采用9092来访问。

7. 查看Producer客户端日志，发现打印TOPIC_AUTHORIZATION_FAILED异常信息。 总。

[root@10-10-144-2 client]# kafka-console-producer.sh --broker-list 10.5.144.2:21007 --topic topic_acl
--producer.config /opt/client/Kafka/kafka/config/producer.properties
[2017-01-25 12:43:58,506] WARN Error while fetching metadata with correlation id 0 :
{topic_acl=TOPIC_AUTHORIZATION_FAILED} (org.apache.kafka.clients.NetworkClient)
[2017-01-25 12:43:58,507] ERROR Error when sending message to topic topic_acl with key: null,
value: 1 bytes with error: Not authorized to access topics: [topic_acl]
(org.apache.kafka.clients.producer.internals.ErrorLoggingCallback)

Producer采用21007端口来访问Kafka。

8. 通过客户端命令klist查询当前认证用户。

当前认证用户为test。

9. 通过客户端命令查看Topic的ACL权限设置信息。[root@10-10-144-2 client]# kafka-acls.sh --authorizer-properties zookeeper.connect=10.5.144.2:2181/kafka --list --topic topic_aclCurrent ACLs for resource \`Topic:topic_acl\`:User:test_user has Allow permission for operations: Describe from hosts: *User:test_user has Allow permission for operations: Write from hosts: *Topic设置ACL，用户test_user具有producer权限。test无权限进行producer操作。

解决方法参考步骤2。

10. 通过SSH登录Kafka Broker：

通过cd /var/log/Bigdata/kafka/broker命令进入日志目录。

查看kafka-authorizer.log发现如下日志提示用户不属于kafka或者kafkaadmin组。
2017-01-25 13:26:33,648 | INFO | [kafka-request-handler-0] | The principal is test, belongs to Group :[hadoop, ficommon] | kafka.authorizer.logger (SimpleAclAuthorizer.scala:169)
2017-01-25 13:26:33,648 | WARN | [kafka-request-handler-0] | The user is not belongs to kafka orkafkaadmin group, authorize failed! | kafka.authorizer.logger (SimpleAclAuthorizer.scala:170)解决方法参考步骤3。

### 解决办法

步骤1 配置自定义配置“allow.everyone.if.no.acl.found”参数为“true”，重启Kafka服务。

步骤2 采用具有权限用户登录。

例如：

kinit test_user

或者赋予用户相关权限。

说明

需要使用Kafka管理员用户（属于kafkaadmin组）操作。

例如：

kafka-acls.sh --authorizer-properties zookeeper.connect=10.5.144.2:2181/kafka --topic topic_acl --producer --add --allow-principal User:test

[root@10-10-144-2 client]# kafka-acls.sh --authorizer-properties zookeeper.connect=8.5.144.2:2181/kafka --
list --topic topic_acl
Current ACLs for resource \`Topic:topic_acl\`:
User:test_user has Allow permission for operations: Describe from hosts: *
User:test_user has Allow permission for operations: Write from hosts: *
User:test has Allow permission for operations: Describe from hosts: *
User:test has Allow permission for operations: Write from hosts: *

步骤3 用户加入Kafka组或者Kafkaadmin组。

----结束

## 17.13 Producer 发送数据失败，报错“Too many openfiles in system”

问题背景与现象

在使用Producer向Kafka发送数据功能时，发现客户端发送失败。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/d6c7d40b-b4f0-4687-9da4-937721e1f554/70584e336ffadf48314916830515f9bb3fbe24e1dc37a756a41a8210141a5676.jpg)

图 17-9 Producer 发送数据失败

### 可能原因

1. Kafka服务异常。

2. 网络异常。

3. Kafka Topic异常。

### 原因分析

1. 查看Kafka服务状态：

MRS Manager界面操作：登录MRS Manager，依次选择“服务管理 >Kafka”，查看当前Kafka状态，发现状态为良好，且监控指标内容显示正确。

FusionInsight Manager界面操作：登录FusionInsight Manager，选择“集群 > 服务 > Kafka”，查看当前Kafka状态，发现状态为良好，且监控指标内容显示正确。

2. 查看SparkStreaming日志中提示错误的Topic信息。

执行Kafka相关命令，获取Topic分布信息和副本同步信息，观察返回结果。

kafka-topics.sh --describe --zookeeper <zk_host:port/chroot>

如图17-10所示，发现对应Topic状态正常。所有Partition均存在正常Leader信息。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/d6c7d40b-b4f0-4687-9da4-937721e1f554/5a4293e52c40f0b28e9241b9f61a9d1883de01529a1fbd42b12ba98439faca26.jpg)

图 17-10 Topic 状态

3. 通过telnet命令，查看是否可以连接Kafka。

telnet Kafka业务IP Kafka业务port

如果无法telnet成功，请检查网络安全组与ACL。

4. 通过SSH登录Kafka Broker。

通过cd /var/log/Bigdata/kafka/broker命令进入日志目录。查看server.log发现如下日志抛出java.io.IOException: Too many open files insystem。

图 17-11 日志异常
2018-05-08 23:05:00,061 | ERROR | [kafka-socket-acceptor-PLAINTEXT-21005] | Error while accepting connection | kafka.network.Accept
java.io.IOException: Too many open files in system
at sun.nio.ch.ServerSocketChannelImpl.accept0(Native Method)
at sun.nio.ch.ServerSocketChannelImpl.accept(ServerSocketChannelImpl.java:422)

5. 通过lsof命令查看当前节点Kafka进程句柄使用情况，发现占用的句柄数达到了47万。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/d6c7d40b-b4f0-4687-9da4-937721e1f554/dea3328b60273da3248896636b142185cab9a33b232a7f11b3c1de066c8bee85.jpg)

图 17-12 句柄数

6. 排查业务代码，不停地创建新的Producer对象，未正常关闭。

### 解决办法

步骤1 停止当前应用，保证服务端句柄不再疯狂增加影响服务正常运行。

步骤2 优化应用代码，解决句柄泄露问题。

建议：全局尽量使用一个Producer对象，在使用完成之后主动调用close接口进行句柄关闭。

----结束

## 17.14 Flume 正常连接 Kafka 后发送消息失败

### 问题现象

使用MRS版本安装集群，主要安装ZooKeeper、Flume、Kafka。

在使用Flume向Kafka发送数据功能时，发现Flume发送数据到Kafka失败。

### 可能原因

1. Kafka服务异常。

2. Flume连接Kafka地址错误，导致发送失败。

3. Flume发送超过Kafka大小限制的消息，导致发送失败。

### 原因分析

Flume发送数据到Kafka失败，可能原因是Flume侧问题或者Kafka侧问题。

1. Manager界面查看当前Kafka状态及监控指标。

MRS Manager界面操作：登录MRS Manager，选择 “服务管理 >Kafka”，查看当前Kafka状态，发现状态为良好，且监控指标内容显示正确。

FusionInsight Manager界面操作：登录FusionInsight Manager，选择“集群 > 服务 > Kafka”，查看当前Kafka状态，发现状态为良好，且监控指标内容显示正确。

2. 查看Flume日志，发现打印MessageSizeTooLargeException异常信息，如下所示：

2016-02-26 14:55:19,126 | WARN | [SinkRunner-PollingRunner-DefaultSinkProcessor] | Produce request with correlation id 349829 failed due to [LOG,7]: kafka.common.MessageSizeTooLargeException | kafka.utils.Logging$class.warn(Logging.scala:83)

通过异常信息，发现当前Flume向Kafka写入的数据超过了Kafka服务端定义的消息的最大值。

3. 通过Manager查看Kafka服务端定义的消息的最大值。

MRS Manager界面操作入口：登录MRS Manager，依次选择 “服务管理 >Kafka> 配置”。

FusionInsight Manager界面操作入口：登录FusionInsight Manager，选择“集群 > 服务 > Kafka > 配置”。

进入Kafka配置页面，参数类别选择全部配置，显示所有Kafka相关配置，在“搜索”中输入message.max.bytes进行检索。

MRS中Kafka服务端默认可以接收的消息最大为1000012 bytes =977 KB。

### 解决办法

与用户确认，当前Flume发送数据确实存在超过1M的消息。因此，为了确保当前这些消息能够写入Kafka，需要调整Kafka服务端相关参数。

步骤1 修改message.max.bytes，使得message.max.bytes的值大于当前业务中消息最大值，使得Kafka服务端可以接收全部消息。

步骤2 修改replica.fetch.max.bytes，使得replica.fetch.max.bytes >=

message.max.bytes，使得不同Broker上的Partition的Replica可以同步到全部消息。

MRS Manager界面操作入口：登录MRS Manager，依次选择 “服务管理 >Kafka> 配置”。

FusionInsight Manager界面操作入口：登录FusionInsight Manager，选择“集群 > 服务 > Kafka > 配置”。

进入Kafka配置页面，参数类别选择全部配置， 显示所有Kafka相关配置，在“搜索”中输入replica.fetch.max.bytes进行检索。

步骤3 单击“保存”，并重启Kafka服务，使得Kafka相关配置生效。

步骤4 修改消费者业务应用中fetch.message.max.bytes，使得fetch.message.max.bytes >=message.max.bytes，确保消费者可以消费到全部消息。

----结束

## 17.15 Kafka 生产者写入单条记录过长

### 问题背景与现象

用户在开发一个Kafka应用，作为一个生产者调用新接口（org.apache.kafka.clients.producer.*）往Kafka写数据，单条记录大小为1100055，超过了kafka配置文件server.properties中message.max.bytes=1000012。用户修改了Kafka服务配置中message.max.bytes大小为5242880，同时也将replica.fetch.max.bytes大小修改为5242880后，仍然无法成功。

报异常如下：

14749 [Thread-0] INFO com.xxx.bigdata.kafka.example.NewProducer - The ExecutionException occurred :

{}.
java.util.concurrent.ExecutionException: org.apache.kafka.common.errors.RecordTooLargeException: The
message is 1100093 bytes when serialized which is larger than the maximum request size you have
configured with the max.request.size configuration.
at org.apache.kafka.clients.producer.KafkaProducer$FutureFailure.<init>(KafkaProducer.java:739)
at org.apache.kafka.clients.producer.KafkaProducer.doSend(KafkaProducer.java:483)
at org.apache.kafka.clients.producer.KafkaProducer.send(KafkaProducer.java:430)
at org.apache.kafka.clients.producer.KafkaProducer.send(KafkaProducer.java:353)
at com.xxx.bigdata.kafka.example.NewProducer.run(NewProducer.java:150)
Caused by: org.apache.kafka.common.errors.RecordTooLargeException: The message is **** bytes when
serialized which is larger than the maximum request size you have configured with the max.request.size
configuration.
……

### 原因分析

经分析因为在写数据到Kafka时，Kafka客户端会先比较配置项“max.request.size值和本次写入数据大小，若写入数据大小超过此配置项“max.request.size ”的缺省值，则抛出上述异常。

### 解决办法

```javascript
步骤1 在初始化Kafka生产者实例时，设置此配置项“max.request.size ”的值。
例如，参考本例，可以将此配置项设置为“5252880”：
// 协议类型:当前支持配置为SASL_PLAINTEXT或者PLAINTEXT
props.put(securityProtocol, kafkaProc.getValues(securityProtocol, "SASL_PLAINTEXT"));
// 服务名
props.put(saslKerberosServiceName, "kafka");
props.put("max.request.size", "5252880");
----结束
```
----结束

## 17.16 Kafka 消费者读取单条记录过长

### 问题背景与现象

和“Kafka生产者写入单条记录过长问题”相对应的，在写入数据后，用户开发一个应用，以消费者调用新接口（org.apache.kafka.clients.consumer.*）到Kafka上读取数据，但读取失败，报异常大致如下：

1687 [KafkaConsumerExample] INFO org.apache.kafka.clients.consumer.internals.AbstractCoordinator -
Successfully joined group DemoConsumer with generation 1
1688 [KafkaConsumerExample] INFO org.apache.kafka.clients.consumer.internals.ConsumerCoordinator -
Setting newly assigned partitions [default-0, default-1, default-2] for group DemoConsumer
2053 [KafkaConsumerExample] ERROR com.xxx.bigdata.kafka.example.NewConsumer -
[KafkaConsumerExample], Error due to
org.apache.kafka.common.errors.RecordTooLargeException: There are some messages at [Partition=Ofset]:
{default-0=177} whose size is larger than the fetch size 1048576 and hence cannot be ever returned.
Increase the fetch size on the client (using max.partition.fetch.bytes), or decrease the maximum message
size the broker will allow (using message.max.bytes).
2059 [KafkaConsumerExample] INFO com.xxx.bigdata.kafka.example.NewConsumer -
[KafkaConsumerExample], Stopped

### 原因分析

经分析因为在读取数据时Kafka客户端会比较待读取数据大小和配置项

“max.partition.fetch.bytes”值，若超过此配置项值，则抛出上述异常。

### 解决办法

步骤1 在初始化建立Kafka消费者实例时，设置此配置项“max.partition.fetch.bytes”的值。

例如，参考本例，可以将此配置项设置为“5252880”：

// 安全协议类型
props.put(securityProtocol, kafkaProc.getValues(securityProtocol, "SASL_PLAINTEXT"));
// 服务名
props.put(saslKerberosServiceName, "kafka");
props.put("max.partition.fetch.bytes","5252880");
......
----结束

## 17.17 Kafka Consumer 消费数据丢失如何处理

### 问题背景与现象

用户将消费完的数据存入数据库，发现数据与生产数据不一致，怀疑Kafka消费丢数据。

### 可能原因

● 业务代码原因

● Kafka生产数据写入异常

● Kafka消费数据异常

### 解决办法

Kafka排查：

步骤1 通过consumer-groups.sh来观察写入和消费的ofset的变化情况（生产一定数量的消息，客户端进行消费，观察ofset的变化）。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/d6c7d40b-b4f0-4687-9da4-937721e1f554/a0f37f38109d61d70bbd1b51f9a1b5a468d655828d760559046378c87976e580.jpg)

步骤2 新建一个消费组，用客户端进行消费，然后查看消费的消息。

```batch
kafka-console-consumer.sh --topic <topic name> --bootstrap-server <IP1:PORT,
IP2:PORT,...> --new-consumer --consumer.config <config file>
```

----结束

业务代码排查：

步骤1 查看客户端里有没有提交ofset的报错。

步骤2 如果没有报错把消费的API里加上打印消息，打印少量数据（只打印key即可），查看丢失的数据。

----结束

## 17.18 Consumer 消费数据时，存在重复消费现象

### 问题背景与现象

当数据量较大时会频繁地发生rebalance导致出现重复消费的情况，关键日志如下：

2018-05-12 10:58:42,561 | INFO | [kafka-request-handler-3] | [GroupCoordinator 2]: Preparing to restabilize group DemoConsumer with old generation 118 | kafka.coordinator.GroupCoordinator (Logging.scala:68) 2018-05-12 10:58:43,245 | INFO | [kafka-request-handler-5] | [GroupCoordinator 2]: Stabilized group DemoConsumer generation 119 | kafka.coordinator.GroupCoordinator (Logging.scala:68)
2018-05-12 10:58:43,560 | INFO | [kafka-request-handler-7] | [GroupCoordinator 2]: Assignment received from leader for group DemoConsumer for generation 119 | kafka.coordinator.GroupCoordinator
(Logging.scala:68)
2018-05-12 10:59:13,562 | INFO | [executor-Heartbeat] | [GroupCoordinator 2]: Preparing to restabilize group DemoConsumer with old generation 119 | kafka.coordinator.GroupCoordinator (Logging.scala:68) 2018-05-12 10:59:13,790 | INFO | [kafka-request-handler-3] | [GroupCoordinator 2]: Stabilized group DemoConsumer generation 120 | kafka.coordinator.GroupCoordinator (Logging.scala:68)
2018-05-12 10:59:13,791 | INFO | [kafka-request-handler-0] | [GroupCoordinator 2]: Assignment received from leader for group DemoConsumer for generation 120 | kafka.coordinator.GroupCoordinator
(Logging.scala:68)
2018-05-12 10:59:43,802 | INFO | [kafka-request-handler-2] | Rolled new log segment for
'__consumer_ofsets-17' in 2 ms. | kafka.log.Log (Logging.scala:68)
2018-05-12 10:59:52,456 | INFO | [group-metadata-manager-0] | [Group Metadata Manager on Broker 2]: Removed 0 expired ofsets in 0 milliseconds. | kafka.coordinator.GroupMetadataManager (Logging.scala:68) 2018-05-12 11:00:49,772 | INFO | [kafka-scheduler-6] | Deleting segment 0 from log __consumer_ofsets-17. | kafka.log.Log (Logging.scala:68)
2018-05-12 11:00:49,773 | INFO | [kafka-scheduler-6] | Deleting index /srv/BigData/kafka/data4/kafka-logs/ _consumer_ofsets-17/00000000000000000000.index.deleted | kafka.log.OfsetIndex (Logging.scala:68) 2018-05-12 11:00:49,773 | INFO | [kafka-scheduler-2] | Deleting segment 2147948547 from log
_consumer_ofsets-17. | kafka.log.Log (Logging.scala:68)
2018-05-12 11:00:49,773 | INFO | [kafka-scheduler-4] | Deleting segment 4282404355 from log
_consumer_ofsets-17. | kafka.log.Log (Logging.scala:68)
2018-05-12 11:00:49,775 | INFO | [kafka-scheduler-2] | Deleting index /srv/BigData/kafka/data4/kafka-logs/ _consumer_ofsets-17/00000000002147948547.index.deleted | kafka.log.OfsetIndex (Logging.scala:68) 2018-05-12 11:00:49,775 | INFO | [kafka-scheduler-4] | Deleting index /srv/BigData/kafka/data4/kafka-logs/ _consumer_ofsets-17/00000000004282404355.index.deleted | kafka.log.OfsetIndex (Logging.scala:68) 2018-05-12 11:00:50,533 | INFO | [kafka-scheduler-6] | Deleting segment 4283544095 from log
_consumer_ofsets-17. | kafka.log.Log (Logging.scala:68)
2018-05-12 11:00:50,569 | INFO | [kafka-scheduler-6] | Deleting index /srv/BigData/kafka/data4/kafka-logs/ _consumer_ofsets-17/00000000004283544095.index.deleted | kafka.log.OfsetIndex (Logging.scala:68) 2018-05-12 11:02:21,178 | INFO | [kafka-request-handler-2] | [GroupCoordinator 2]: Preparing to restabilize group DemoConsumer with old generation 120 | kafka.coordinator.GroupCoordinator (Logging.scala:68) 2018-05-12 11:02:22,839 | INFO | [kafka-request-handler-4] | [GroupCoordinator 2]: Stabilized group DemoConsumer generation 121 | kafka.coordinator.GroupCoordinator (Logging.scala:68)
2018-05-12 11:02:23,169 | INFO | [kafka-request-handler-1] | [GroupCoordinator 2]: Assignment received from leader for group DemoConsumer for generation 121 | kafka.coordinator.GroupCoordinator
(Logging.scala:68)
2018-05-12 11:02:49,913 | INFO | [kafka-request-handler-6] | Rolled new log segment for
'__consumer_ofsets-17' in 2 ms. | kafka.log.Log (Logging.scala:68)

其中Preparing to restabilize group DemoConsumer with old generation表示正在发生rebalance。

### 可能原因

参数设置不合理。

### 原因分析

原因：由于参数设置不当，数据量大时数据处理时间过长，导致频繁发生balance，此时ofset无法正常提交，导致重复消费数据。

原理：每次poll的数据处理完后才提交ofset，如果poll数据后的处理时长超出了session.timeout.ms的设置时长，此时发生rebalance导致本次消费失败，已经消费数据的ofset无法正常提交，所以下次重新消费时还是在旧的ofset消费数据，从而导致消费数据重复。

### 解决办法

建议用户在Manager页面调整以下服务参数：

● request.timeout.ms=100000

● session.timeout.ms=90000

● max.poll.records=50

● heartbeat.interval.ms=3000

其中：

● request.timeout.ms要比session.timeout.ms大10s。

session.timeout.ms的大小设置要在服务端参数group.min.session.timeout.ms和group.max.session.timeout.ms之间。

以上参数可以根据实际情况进行适当的调整，特别是max.poll.records，这个参数是为了控制每次poll数据的records量，保证每次的处理时长尽量保持稳定。目的是为了保证poll数据以后的处理时间不要超过session.timeout.ms的时间。

### 参考信息

● poll之后的数据处理效率要高，不要阻塞下一次poll。

● poll方法和数据处理建议异步处理。
----结束

## 17.19 Consumer 初始化成功，但无法从 Kafka 中获取指定Topic 消息

### 问题背景与现象

使用MRS安装集群，主要安装ZooKeeper、Flume、Kafka、Storm、Spark。

使用Storm、Spark、Flume或者自己编写consumer代码来消费Kafka中指定Topic的消息时，发现消费不到任何数据。

### 可能原因

1. Kafka服务异常。

2. Consumer中ZooKeeper相关连接地址配置错误，导致无法消费。

3. Consumer发生ConsumerRebalanceFailedException异常，导致无法消费。

4. Consumer发生网络导致的ClosedChannelException异常，导致无法消费。

### 原因分析

Storm、Spark、Flume或者自定义Consumer代码可以都称为Consumer。

1. 查看Kafka服务状态：

MRS Manager界面操作：登录MRS Manager，依次选择“服务管理 >Kafka”，查看当前Kafka状态，发现状态为良好，且监控指标内容显示正确。

FusionInsight Manager界面操作：登录FusionInsight Manager，选择“集群 > 服务 > Kafka”，查看当前Kafka状态，发现状态为良好，且监控指标内容显示正确。

2. 通过Kafka Client，判断是否可以正常消费数据。

假设客户端已经安装在/opt/client目录，test为需要消费的Topic名称，192.168.234.231为ZooKeeper的IP地址。

cd /opt/client
source bigdata_env
kinit admin
kafka-topics.sh --zookeeper 192.168.234.231:2181/kafka --describe --topic testkafka-console-
consumer.sh --topic test --zookeeper 192.168.234.231:2181/kafka --from-beginning
当可以消费到数据时，表示集群服务正常。

3. 查看Consumer相关配置，发现ZooKeeper连接地址错误。

```ini
Flume
server.sources.Source02.type=org.apache.flume.source.kafka.KafkaSource
server.sources.Source02.zookeeperConnect=192.168.234.231:2181
server.sources.Source02.topic = test
server.sources.Source02.groupId = test_01
```

– Spark

Storm

– Consumer API

MRS中Kafka在ZooKeeper存储的ZNode是以/kafka为根路径，有别于开源。
Kafka对应的ZooKeeper连接配置为192.168.234.231:2181/kafka。

Consumer中配置为ZooKeeper连接配置为192.168.234.231:2181，导致无法正确获取Kafka中Topic相关信息。

解决方法参考步骤1。

4. 查看Consumer相关日志，发现打印ConsumerRebalanceFailedException异常。
2016-02-03 15:55:32,557 | ERROR | [ZkClient-EventThread-75- 192.168.234.231:2181/kafka] | Error
handling event ZkEvent[New session event sent to kafka.consumer.ZookeeperConsumerConnector
$ZKSessionExpireListener@34b41dfe] | org.I0Itec.zkclient.ZkEventThread.run(ZkEventThread.java:77)
kafka.common.ConsumerRebalanceFailedException: pc-zjqbetl86-1454482884879-2ec95ed3 can't
rebalance after 4 retries
at kafka.consumer.ZookeeperConsumerConnector
$ZKRebalancerListener.syncedRebalance(ZookeeperConsumerConnector.scala:633)
at kafka.consumer.ZookeeperConsumerConnector
$ZKSessionExpireListener.handleNewSession(ZookeeperConsumerConnector.scala:487)
at org.I0Itec.zkclient.ZkClient$4.run(ZkClient.java:472)
at org.I0Itec.zkclient.ZkEventThread.run(ZkEventThread.java:71)

通过异常信息，发现当前Consumer没有在指定的重试次数内完成Rebalance，使得Consumer没有被分配Kafka Topic-Partition，则无法消费消息。

解决方法参考步骤3。

5. 查看Consumer相关日志，发现打印Fetching topic metadata with correlation id0 for topics [Set(test)] from broker [id:26,host:192-168-234-231,port:9092]failed错误信息和ClosedChannelException异常。

```csv
[2016-03-04 03:33:53,047] INFO Fetching metadata from broker id:26,host:
192-168-234-231,port:9092 with correlation id 0 for 1 topic(s) Set(test) (kafka.client.ClientUtils$)
[2016-03-04 03:33:55,614] INFO Connected to 192-168-234-231:21005 for producing
(kafka.producer.SyncProducer)
[2016-03-04 03:33:55,614] INFO Disconnecting from 192-168-234-231:21005
(kafka.producer.SyncProducer)
[2016-03-04 03:33:55,615] WARN Fetching topic metadata with correlation id 0 for topics [Set(test)]
from broker [id:26,host: 192-168-234-231,port:21005] failed (kafka.client.ClientUtils$)
java.nio.channels.ClosedChannelException
at kafka.network.BlockingChannel.send(BlockingChannel.scala:100)
at kafka.producer.SyncProducer.liftedTree1$1(SyncProducer.scala:73)
at kafka.producer.SyncProducer.kafka$producer$SyncProducer$$doSend(SyncProducer.scala:72)
at kafka.producer.SyncProducer.send(SyncProducer.scala:113)
at kafka.client.ClientUtils$.fetchTopicMetadata(ClientUtils.scala:58)
at kafka.client.ClientUtils$.fetchTopicMetadata(ClientUtils.scala:93)
at kafka.consumer.ConsumerFetcherManager
$LeaderFinderThread.doWork(ConsumerFetcherManager.scala:66)
at kafka.utils.ShutdownableThread.run(ShutdownableThread.scala:60)
[2016-03-04 03:33:55,615] INFO Disconnecting from 192-168-234-231:21005
(kafka.producer.SyncProducer)
```

通过异常信息，发现当前Consumer无法从Kafka Broker 192-168-234-231节点获取元数据，导致无法连接正确的Broker获取消息。

6. 检查网络是否存在问题，如果网络没有问题，检查是否配置主机和IP的对应关系

Linux

执行cat /etc/hosts命令。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/d6c7d40b-b4f0-4687-9da4-937721e1f554/26ae619ca671c0e94571f0d0d8919863412b09515299a21955570923fa9fb3e9.jpg)

Windows

打开“C:\Windows\System32\drivers\etc\hosts”。

For example:
192.168.94.97 rhino.acme.com # source server
192.168.63.10 x.acme.com # x client host
localhost name resolution is handled within DNS itself.
127.0.0.1 localhost
::1 localhost
10.82.129.120 rms. .com # modified by IrmTool at 2015-01-18 17:55:13

解决方法参考步骤4。

### 解决办法

步骤1 ZooKeeper连接地址配置错误。

步骤2 修改Consumer配置中的ZooKeeper连接地址信息，保证和MRS相一致。

● Flume

server.sources.Source02.type=org.apache.flume.source.kafka.KafkaSource server.sources.Source02.zookeeperConnect=192.168.234.231:2181/kafka server.sources.Source02.topic = test
server.sources.Source02.groupId = test_01

Spark val zkQuorum = "192.168.234.231:2181/kafka"

Storm

● Consumer API

步骤3 Rebalance异常。

同一个消费者组(consumer group)有多个consumer先后启动，就是一个消费者组内有多个consumer同时消费多个partition数据，consumer端也会有负载均衡（consumer个数小于partitions数量时）。

consumer实际上是靠存储在zk中的临时节点来表明针对哪个topic的哪个partition拥有读权限的。所在路径为：/consumers/consumer-group-xxx/owners/topic-xxx/x。

当触发负载均衡后，原来的consumer会重新计算并释放已占用的partitions，此过程需要一定的处理时间，新来的consumer抢占该partitions时很有可能会失败。

表 17-1 参数说明

<table><tr><td rowspan=1 colspan=1>名称</td><td rowspan=1 colspan=1>作用</td><td rowspan=1 colspan=1>默认值</td></tr><tr><td rowspan=1 colspan=1>rebalance.max.retries</td><td rowspan=1 colspan=1>Rebalance最大重试次数</td><td rowspan=1 colspan=1>4</td></tr><tr><td rowspan=1 colspan=1>rebalance.backoff.ms</td><td rowspan=1 colspan=1>Rebalance每次重试间隔</td><td rowspan=1 colspan=1>2000</td></tr><tr><td rowspan=1 colspan=1>zookeeper.session.timeout.ms</td><td rowspan=1 colspan=1>Zookeeper连接会话超时时间</td><td rowspan=1 colspan=1>15000</td></tr></table>

可以适当调大上述三个参数，可以参考如下数值：

zookeeper.session.timeout.ms = 45000
rebalance.max.retries = 10
rebalance.backof.ms = 5000

参数设置应遵循：

rebalance.max.retries * rebalance.backof.ms > zookeeper.session.timeout.ms步骤4 网络异常。

在hosts文件中没有配置主机名和IP的对应关系，导致使用主机名进行访问时，无法获取信息。

步骤5 在hosts文件中添加对应的主机名和IP的对应关系。

● Linux

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/d6c7d40b-b4f0-4687-9da4-937721e1f554/236c9d8449716d7a662e03f6c313e966a7f7281d92858e718f595f7a37e060b4.jpg)

● Windows

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/d6c7d40b-b4f0-4687-9da4-937721e1f554/f4f6f3e4e13d5f27e9523438b3b820c29ff764d3454434af13206af9898a502f.jpg)

----结束

## 17.20 Consumer 消费数据失败，报错“SchemaException:Error reading field”

问题背景与现象

Consumer来消费Kafka中指定Topic的消息时，发现无法从Kafka中获取到数据。

提示如下错误：

org.apache.kafka.common.protocol.types.SchemaException: Error reading field 'brokers': Error reading field 'host': Error reading string of length 28271, only 593 bytes available

Exception in thread "Thread-0" org.apache.kafka.common.protocol.types.SchemaException: Error reading
field 'brokers': Error reading field 'host': Error reading string of length 28271, only 593 bytes available
at org.apache.kafka.common.protocol.types.Schema.read(Schema.java:73)
at org.apache.kafka.clients.NetworkClient.parseResponse(NetworkClient.java:380)
at org.apache.kafka.clients.NetworkClient.handleCompletedReceives(NetworkClient.java:449)
at org.apache.kafka.clients.NetworkClient.poll(NetworkClient.java:269)
at
org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.clientPoll(ConsumerNetworkClient.java:
360)
at
org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:224)
at
org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:192)
at
org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:163)
atorg.apache.kafka.clients.consumer.internals.AbstractCoordinator.ensureCoordinatorReady(AbstractCoordina
tor.java:179)
at org.apache.kafka.clients.consumer.KafkaConsumer.pollOnce(KafkaConsumer.java:973)

at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:937) at KafkaNew.Consumer$ConsumerThread.run(Consumer.java:40)

### 可能原因

客户端和服务端Jar版本不一致。

### 解决办法

修改Consumer应用程序中Kafka jar，确保和服务端保持一致。
----结束

## 17.21 Consumer 消费数据失败，Consumer 一直处于等待状态

### 问题现象

使用MRS服务安装集群，主要安装ZooKeeper、Kafka。

在使用Consumer从Kafka消费数据时，发现客户端一直处于等待状态。

### 可能原因

1. Kafka服务异常。

2. 客户端Consumer侧采用非安全访问，服务端配置禁止访问。

3. 客户端Consumer侧采用非安全访问，Kafka Topic设置ACL。

### 原因分析

Consumer向Kafka消费数据失败，可能原因客户端Consumer侧问题或者Kafka侧问题。

1. 查看Kafka服务状态：

MRS Manager界面操作：登录MRS Manager，依次选择“服务管理 >Kafka”，查看当前Kafka状态，发现状态为良好，且监控指标内容显示正确。

FusionInsight Manager界面操作：登录FusionInsight Manager，选择“集群 > 服务 > Kafka”，查看当前Kafka状态，发现状态为良好，且监控指标内容显示正确。

2. 查看Consumer客户端日志发现频繁连接Broker节点和断链打印信息，如下所示。[root@10-10-144-2 client]# kafka-console-consumer.sh --topic test --zookeeper 10.5.144.2:2181/kafka--from-beginning[2017-03-07 09:22:00,658] INFO Fetching metadata from broker BrokerEndPoint(1,10.5.144.2,9092)with correlation id 26 for 1 topic(s) Set(test) (kafka.client.ClientUtils$)[2017-03-07 09:22:00,659] INFO Connected to 10.5.144.2:9092 for producing(kafka.producer.SyncProducer)[2017-03-07 09:22:00,659] INFO Disconnecting from 10.5.144.2:9092 (kafka.producer.SyncProducer)Consumer采用9092端口来访问Kafka，9092为非安全端口。

3. 通过Manager页面查看当前Kafka集群配置，发现未配置自定义参数“allow.everyone.if.no.acl.found”=“false”。

MRS Manager界面操作入口：登录MRS Manager，依次选择“服务管理 >Kafka> 配置”。

FusionInsight Manager界面操作入口：登录FusionInsight Manager，选择“集群 > 服务 > Kafka > 配置”。

4. 当ACL设置为false不允许采用9092来进行访问。

5. 查看Consumer客户端日志发现频繁连接Broker节点和断链打印信息，如下所示。[root@10-10-144-2 client]# kafka-console-consumer.sh --topic test_acl --zookeeper 10.5.144.2:2181/kafka --from-beginning[2017-03-07 09:49:16,992] INFO Fetching metadata from broker BrokerEndPoint(2,10.5.144.3,9092)with correlation id 16 for 1 topic(s) Set(topic_acl) (kafka.client.ClientUtils$)[2017-03-07 09:49:16,993] INFO Connected to 10.5.144.3:9092 for producing(kafka.producer.SyncProducer)[2017-03-07 09:49:16,994] INFO Disconnecting from 10.5.144.3:9092 (kafka.producer.SyncProducer)Consumer采用21005端口来访问Kafka，21005为非安全端口。

6. 通过客户端命令查看topic的ACL权限设置信息。[root@10-10-144-2 client]# kafka-acls.sh --authorizer-properties zookeeper.connect=10.5.144.2:2181/kafka --list --topic topic_aclCurrent ACLs for resource \`Topic:topic_acl\`:User:test_user has Allow permission for operations: Describe from hosts: *User:test_user has Allow permission for operations: Write from hosts: *

Topic设置ACL，则不允许采用9092来访问。

7. 查看Consumer客户端日志发现打印信息，如下所示。

[root@10-10-144-2 client]# kafka-console-consumer.sh --topic topic_acl --bootstrap-server
10.5.144.2:21007 --consumer.config /opt/client/Kafka/kafka/config/consumer.properties --from
beginning --new-consumer
[2017-03-07 10:19:18,478] INFO Kafka version : 0.9.0.0 (org.apache.kafka.common.utils.AppInfoParser)
[2017-03-07 10:19:18,478] INFO Kafka commitId : unknown
(org.apache.kafka.common.utils.AppInfoParser)

Consumer采用21007端口来访问Kafka。

8. 通过客户端命令klist查询当前认证用户：

Valid starting Expires Service principal 01/25/17 11:06:48 01/26/17 11:06:45 krbtgt/HADOOP.COM@HADOOP.COM

当前认证用户为test。

9. 通过客户端命令查看topic的acl权限设置信息。[root@10-10-144-2 client]# kafka-acls.sh --authorizer-properties zookeeper.connect=10.5.144.2:24002/kafka --list --topic topic_aclCurrent ACLs for resource \`Topic:topic_acl\`:User:test_user has Allow permission for operations: Describe from hosts: *User:test_user has Allow permission for operations: Write from hosts: *User:test_user has Allow permission for operations: Read from hosts: *

Topic设置acl，test无权限进行consumer操作。

解决方法参考步骤2。

10. 通过SSH登录Kafka Broker：

通过cd /var/log/Bigdata/kafka/broker命令进入日志目录。

查看kafka-authorizer.log发现如下日志提示用户不属于kafka或者kafkaadmin组。
2017-01-25 13:26:33,648 | INFO | [kafka-request-handler-0] | The principal is test, belongs to Group :[hadoop, ficommon] | kafka.authorizer.logger (SimpleAclAuthorizer.scala:169)
2017-01-25 13:26:33,648 | WARN | [kafka-request-handler-0] | The user is not belongs to kafka orkafkaadmin group, authorize failed! | kafka.authorizer.logger (SimpleAclAuthorizer.scala:170)解决方法参考步骤3。

### 解决办法

步骤1 配置自定义参数“allow.everyone.if.no.acl.found”参数为“true”，重启Kafka服务。

步骤2 采用具有权限用户登录。

例如：

kinit test_user

或者赋予用户相关权限。

须知

需要使用Kafka管理员用户（属于kafkaadmin组）操作。

例如：

kafka-acls.sh --authorizer-properties zookeeper.connect=10.5.144.2:2181/kafka --topic topic_acl --consumer --add --allow-principal User:test --group test

[root@10-10-144-2 client]# kafka-acls.sh --authorizer-properties zookeeper.connect=8.5.144.2:2181/kafka --
list --topic topic_acl
Current ACLs for resource \`Topic:topic_acl\`:
User:test_user has Allow permission for operations: Describe from hosts: *
User:test_user has Allow permission for operations: Write from hosts: * User:test has Allow permission for operations: Describe from hosts: * User:test has Allow permission for operations: Write from hosts: * User:test has Allow permission for operations: Read from hosts: *

步骤3 用户加入Kafka组或者Kafkaadmin组。

----结束

## 17.22 Consumer 消费数据失败，报错“GROUP\_COORDINATOR\_NOT\_AVAILABLE”

### 问题背景与现象

新建Kafka集群，部署Broker节点数为2，使用Kafka客户端可以正常生产，但是无法正常消费。Consumer消费数据失败，提示GROUP_COORDINATOR_NOT_AVAILABLE，关键日志如下：

2018-05-12 10:58:42,561 | INFO | [kafka-request-handler-3] | [GroupCoordinator 2]: Preparing to restabilize group DemoConsumer with old generation 118 | kafka.coordinator.GroupCoordinator (Logging.scala:68) 2018-05-12 10:59:13,562 | INFO | [executor-Heartbeat] | [GroupCoordinator 2]: Preparing to restabilize group DemoConsumer with old generation 119 | kafka.coordinator.GroupCoordinator (Logging.scala:68)

### 可能原因

__consumer_ofsets无法创建。

### 原因分析

1. 查看日志，发现大量__consumer_ofset创建异常。

2. 查看集群发现当前Broker数量为2。

3. 查看__consumer_ofset topic要求副本为3，因此创建失败。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/d6c7d40b-b4f0-4687-9da4-937721e1f554/77ed9b5d2b7cc08b084e7533fef7c9e9739fb0c4ea8f1fe63c255e84b90a524f.jpg)

### 解决办法

可以将扩容至少3个流式core节点，或参考如下步骤修改服务配置参数。

步骤1 进入服务参数配置界面。

MRS Manager界面操作：登录MRS Manager，选择“服务管理 > Kafka > 服务配置”，“参数类别”设置为“全部配置”。

FusionInsight Manager界面操作：登录FusionInsight Manager。选择“集群 >服务 > Kafka”，单击“配置”，选择“全部配置”。

步骤2 搜索并修改ofsets.topic.replication.factor和transaction.state.log.replication.factor的值为2。

步骤3 保存配置，并重启配置过期的服务或者实例。

----结束

## 17.23 SparkStreaming 消费 Kafka 消息失败，报错“Errorgetting partition metadata”

### 问题现象

使用SparkStreaming来消费Kafka中指定Topic的消息时，发现无法从Kafka中获取到数据。提示如下错误： Error getting partition metadata。

Exception in thread "main" org.apache.spark.SparkException: Error getting partition metadata for
'testtopic'. Does the topic exist?
org.apache.spark.streaming.kafka.KafkaCluster$$anonfun$checkErrors$1.apply(KafkaCluster.scala:366)
org.apache.spark.streaming.kafka.KafkaCluster$$anonfun$checkErrors$1.apply(KafkaCluster.scala:366)
scala.util.Either.fold(Either.scala:97)
org.apache.spark.streaming.kafka.KafkaCluster$.checkErrors(KafkaCluster.scala:365)
org.apache.spark.streaming.kafka.KafkaUtils$.createDirectStream(KafkaUtils.scala:422)
com.xxx.bigdata.spark.examples.FemaleInfoCollectionPrint$.main(FemaleInfoCollectionPrint.scala:45)
com.xxx.bigdata.spark.examples.FemaleInfoCollectionPrint.main(FemaleInfoCollectionPrint.scala)
sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
java.lang.reflect.Method.invoke(Method.java:498)
org.apache.spark.deploy.SparkSubmit$.org$apache$spark$deploy$SparkSubmit$
$runMain(SparkSubmit.scala:762)
org.apache.spark.deploy.SparkSubmit$.doRunMain$1(SparkSubmit.scala:183)
org.apache.spark.deploy.SparkSubmit$.submit(SparkSubmit.scala:208)
org.apache.spark.deploy.SparkSubmit$.main(SparkSubmit.scala:123)
org.apache.spark.deploy.SparkSubmit.main(SparkSubmit.scala)

### 可能原因

1. Kafka服务异常。

2. 客户端Consumer侧采用非安全访问，服务端配置禁止访问。

3. 客户端Consumer侧采用非安全访问，Kafka Topic设置ACL。

### 原因分析

1. 查看Kafka服务状态：

MRS Manager界面操作：登录MRS Manager，依次选择“服务管理 >Kafka”，查看当前Kafka状态，发现状态为良好，且监控指标内容显示正确。

FusionInsight Manager界面操作：登录FusionInsight Manager，选择“集群 > 服务 > Kafka”，查看当前Kafka状态，发现状态为良好，且监控指标内容显示正确。

2. 通过Manager页面，查看当前Kafka集群配置，发现未配置“allow.everyone.if.no.acl.found”或配置为“false”。

3. 当ACL设置为false不允许采用Kafka非安全端口21005来进行访问。

4. 通过客户端命令查看topic的ACL权限设置信息：[root@10-10-144-2 client]# kafka-acls.sh --authorizer-properties zookeeper.connect=10.5.144.2:2181/kafka --list --topic topic_aclCurrent ACLs for resource \`Topic:topic_acl\`:User:test_user has Allow permission for operations: Describe from hosts: *User:test_user has Allow permission for operations: Write from hosts: *

Topic设置ACL，则不允许采用Kafka非安全端口21005来访问。

### 解决办法

步骤1 修改或者添加自定义配置“allow.everyone.if.no.acl.found”参数为“true”，重启Kafka服务。

步骤2 删除Topic设置的ACL。

例如：

kinit test_user

须知

需要使用Kafka管理员用户（属于kafkaadmin组）操作。

例如：

kafka-acls.sh --authorizer-properties zookeeper.connect=10.5.144.2:2181/kafka --remove --allow-principal User:test_user --producer --topic topic_acl

kafka-acls.sh --authorizer-properties zookeeper.connect=10.5.144.2:2181/kafka --remove --allow-principal User:test_user --consumer --topic topic_acl --group test

----结束

## 17.24 SparkStreaming 消费 Kafka 消息失败，报错“Couldn't find leader ofsets”

### 问题背景与现象

使用SparkStreaming来消费Kafka中指定Topic的消息时，发现无法从Kafka中获取到数据。

提示如下错误： Couldn't find leader ofsets。

2018-05-30 12:01:17,816 | INF0 | [Driver] | Reconnect due to socket error: java. net.SocketTimeoutException |kafka.utils.Logging$class. info (Logging. scala:68)
2018-05-30 12:01:47,859 | ERR0R | [Driver] | User class threw exception: org. apache. spark. SparkException: java. net.SocketTimeoutException
org. apache. spark. SparkException: Couldn't find leader offsets for Set ([STK6, 57], [STK6, 21]) | org. apache. spark. Logging$class. logError (Logging. scala:96)
org. apache. spark. SparkException: java. net.SocketTimeoutException
org. apache. spark.SparkException: Couldn't find leader offsets for Set ([STKB, 57]. [STK6, 21]) at org. apache. spark. streaming. kafka. KafkaCluster$$anonfun$checkErrors$1. apply (KafkaCluster. scala:366) at org. apache. spark. streaming. kafka. KafkaCluster$$anonfun$checkErrors$1. apply (KafkaCluster. scala:366) at scala. util.Either. fold(Either. scala:97) at org. apache. spark. streaming. kafka. KafkaCluster$. checkErrors (KafkaCluster. scala: 365) at org. apache. spark. streaming. kafka. KafkaUtils$. createDirectStream (KafkaUtils. scala:422) at org. apache. spark. streaming. kafka. Kafkaltils$. createDirectStream (Kafkaltils. scala:532) at org. apache. spark. streaming. kafka. KafkaUtils. createDirectStream (Kafkaltils. scala) at com. stk. bigdata. sparkstreaming. notify. SparkAlarmControlwz, main(SparkAlarmControlwz. java: 194) at com. stk. bigdata. sparkstreaming. submit.SparkNotifyA. main(SparkNotifyA. java:14) at sun. reflect. NativeMethodAccessorImpl. invokeO (Native Method) at sun. reflect. NativeMethodAccessorImpl. invoke (NativeMethodAccessorImpl.java:62) at sun. reflect. DelegatingMethodAccessorImpl. invoke (DelegatingMethodAccessorImpl. java:43) at java. lang. reflect. Method. invoke (Method. java:498) at org. apache. spark. deploy. yarn. ApplicationMaster$$anon$2. run (Applicationlaster. scala:540)
2018-05-30 12:01:47, 863 | INF0 | [Driver] | Final app status: FAILED, exitCode: 15, (reason: User class threw exception: org. apache. spark. SparkException: java.,
org. apache. spark. SparkException: Couldn't find leader offsets for Set ([STK6, 57], [STK6, 21])) | org. apache. spark. Logging$class. logInfo (Logging. scala:59)
2018-05-30 12:01:47, 866 | INF0 | [pool-1-thread-1] | Invoking stop () from shutdown hook | org. apache. spark. Logging$class.logInfo (Logging. scala:59)

### 可能原因

● Kafka服务异常。

● 网络异常。

● Kafka Topic异常。

### 原因分析

步骤1 通过Manager页面，查看Kafka集群当前状态，发现状态为“良好”，且监控指标内容显示正确。

步骤2 查看SparkStreaming日志中提示错误的Topic信息。

执行Kafka相关命令，获取Topic分布信息和副本同步信息，观察返回结果。

kafka-topics.sh --describe --zookeeper <zk host:port/chroot> --topic <topic name>

如下所示，发现对应Topic状态正常。所有Partition均存在正常Leader信息。

图 17-13 Topic 分布信息和副本同步信息

<table><tr><td rowspan=1 colspan=4>Topic: STK6     Partition: 36  Leader: 3</td><td></td><td rowspan=3 colspan=1>Replicas: 3,5  Isr: 3,5Replicas: 4,6  Isr: 4,6Replicas: 5,7  Isr: 5,7</td></tr><tr><td rowspan=1 colspan=3>Topic: STK6     Partition:</td><td rowspan=1 colspan=1>37  Leader: 4</td><td></td></tr><tr><td rowspan=1 colspan=3>Topic: STK6     Partition:</td><td rowspan=1 colspan=1>38  Leader: 5</td><td></td></tr><tr><td rowspan=1 colspan=3>Topic: STK6     Partition:</td><td rowspan=1 colspan=1>39  Leader: 6</td><td></td><td rowspan=1 colspan=1>Replicas: 6,8  Isr: 6,8</td></tr><tr><td rowspan=17 colspan=4>Topic: STK6    Partition: 40Topic: STK6     Partition: 41  Leader: 8Topic: STK6    Partition: 42  Leader: 9Topic: STK6     Partition: 43Topic: STK6     Partition: 44  Leader: 2Topic: STK6     Partition: 45Topic: STK6     Partition: 46  Leader: 4Topic: STK6     Partition: 47Topic:STK6     Partition: 48  Leader: 6Topic: STK6    Partition: 49  Leader: 7Topic: STK6     Partition: 50Topic: STK6     Partition: 51Topic: STK6     Partition: 52Topic: STK6    Partition: 53  Leader: 2Topic: STK6     Partition: 54  Leader: 3Topic: STK6     Partition: 55Topic: STK6     Partition: 56Topic: STK6Topic: STK6</td><td rowspan=1 colspan=1>40 Leader: 7</td><td></td></tr><tr><td rowspan=1 colspan=1>41Leader: 8</td><td></td><td></td></tr><tr><td rowspan=1 colspan=1>43 Leader: 1</td><td></td><td></td></tr><tr><td rowspan=1 colspan=1>44Leader: 2</td><td></td><td rowspan=1 colspan=1></td></tr><tr><td rowspan=1 colspan=1>Partition:</td><td rowspan=1 colspan=1>45 Leader: 3</td><td></td><td rowspan=1 colspan=1></td></tr><tr><td rowspan=1 colspan=1>Partition:</td><td rowspan=1 colspan=1>46 Leader: 4</td><td></td><td rowspan=1 colspan=1></td></tr><tr><td rowspan=1 colspan=1>Partition:</td><td rowspan=1 colspan=1>47 Leader: 5</td><td></td><td rowspan=1 colspan=1></td></tr><tr><td rowspan=1 colspan=1>Partition:</td><td rowspan=1 colspan=1>48 Leader: 6</td><td></td><td rowspan=1 colspan=1></td></tr><tr><td rowspan=1 colspan=1>Partition:</td><td rowspan=1 colspan=1>49 Leader: 7</td><td></td><td rowspan=1 colspan=1></td></tr><tr><td rowspan=2 colspan=1>Partttion:</td><td rowspan=1 colspan=1>51 Leader: 8</td><td></td><td rowspan=1 colspan=1></td></tr><tr><td rowspan=1 colspan=1>52 Leader: 1</td><td></td><td rowspan=1 colspan=1></td></tr><tr><td rowspan=2 colspan=1>Partition:</td><td rowspan=1 colspan=1>53 Leader: 2</td><td rowspan=4 colspan=2>Replicas: 2,5  Isr: 5,2Replicas: 3,7  Isr: 3,7Replicas: 4,8  Isr:4,8Replicas: 5,9  Isr: 5,9</td><td rowspan=1 colspan=1></td></tr><tr><td rowspan=1 colspan=1>54Leader: 3</td><td rowspan=1 colspan=1></td></tr><tr><td rowspan=1 colspan=1>Partition:</td><td rowspan=2 colspan=1>5 Leader: </td></tr><tr><td rowspan=1 colspan=1>Partition:</td></tr><tr><td rowspan=1 colspan=1></td><td rowspan=1 colspan=2></td><td rowspan=1 colspan=2>Replicas: 6,1  Isn: 6.1</td></tr><tr><td rowspan=1 colspan=4>Replicas: 7,2  Isr: 2,7</td></tr></table>

步骤3 检查客户端与Kafka集群网络是否连通，若网络不通协调网络组进行处理。

步骤4 通过SSH登录Kafka Broker。

通过cd /var/log/Bigdata/kafka/broker命令进入日志目录。

查看server.log发现如下日志抛出java.lang.OutOfMemoryError: Direct bufermemory。

2018-05-30 12:02:00,246 | ERROR | [kafka-network-thread-6-PLAINTEXT-3] | Processor got uncaught
exception. | kafka.network.Processor (Logging.scala:103)
java.lang.OutOfMemoryError: Direct bufer memory
at java.nio.Bits.reserveMemory(Bits.java:694)
at java.nio.DirectByteBufer.<init>(DirectByteBufer.java:123)
at java.nio.ByteBufer.allocateDirect(ByteBufer.java:311)
at sun.nio.ch.Util.getTemporaryDirectBufer(Util.java:241)
at sun.nio.ch.IOUtil.read(IOUtil.java:195)
at sun.nio.ch.SocketChannelImpl.read(SocketChannelImpl.java:380)

at

org.apache.kafka.common.network.PlaintextTransportLayer.read(PlaintextTransport Layer.java:110)

步骤5 通过Manager页面，查看当前Kafka集群配置。

MRS Manager界面操作：登录MRS Manager，选择“服务管理 > Kafka > 服务配置”，“参数类别”设置为“全部配置”，发现

“KAFKA_JVM_PERFORMANCE_OPTS”的中“-XX:MaxDirectMemorySize”值为“1G”。

FusionInsight Manager界面操作：登录FusionInsight Manager。选择“集群 >
服务 > Kafka”，单击“配置”，选择“全部配置”，发现
“KAFKA_JVM_PERFORMANCE_OPTS”的中“-XX:MaxDirectMemorySize”值
为“1G”。

步骤6 直接内存配置过小导致报错，而且一旦直接内存溢出，该节点将无法处理新请求，会导致其他节点或者客户端访问超时失败。

----结束

### 解决办法

步骤1 登录到Manager，进入Kafka配置页面。

步骤2 选择“全部配置”，搜索并修改KAFKA_JVM_PERFORMANCE_OPTS的值。

步骤3 保存配置，并重启配置过期的服务或者实例。

----结束

## 17.25 账号锁定导致启动 Kafka组件失败

### 问题背景与现象

新创建的MRS集群，启动Kafka服务失败。

查看服务启动日志，显示认证失败。

/home/omm/kerberos/bin/kinit -k -t ${BIGDATA_HOME}/etc/2_15_ Broker /kafka.keytab kafka/
hadoop.hadoop.com -c ${BIGDATA_HOME}/etc/2_15_ Broker /11846 failed.
export key tab file for kafka/hadoop.hadoop.com failed.export and check keytab file failed, errMsg=]}] for Broker #192.168.1.92@192-168-1-92.
[2015-07-11 02:34:33] RoleInstance started failure for ROLE[name: Broker].
[2015-07-11 02:34:34] Failed to complete the instances start operation. Current operation entities: [Broker #192.168.1.92@192-168-1-92], Failure entities : [Broker #192.168.1.92@192-168-1-92].Operation Failed. Failed to complete the instances start operation. Current operation entities:
[Broker#192.168.1.92@192-168-1-92], Failure entities: [Broker #192.168.1.92@192-168-1-92].

### 原因分析

查看Kerberos日志“/var/log/Bigdata/kerberos/krb5kdc.log”，发现有集群外的IP使用Kafka用户连接，导致多次认证失败，最终导致Kafka账号被锁定。
Jul 11 02:49:16 192-168-1-91 krb5kdc[1863](info): AS_REQ (2 etypes {18 17}) 192.168.1.93:
NEEDED_PREAUTH: kafka/hadoop.hadoop.com@HADOOP.COM for krbtgt/HADOOP.COM@HADOOP.COM,Additional pre-authentication required
Jul 11 02:49:16 192-168-1-91 krb5kdc[1863](info): preauth (encrypted_timestamp) verify failure: Decryptintegrity check failed
Jul 11 02:49:16 192-168-1-91 krb5kdc[1863](info): AS_REQ (2 etypes {18 17}) 192.168.1.93:
PREAUTH_FAILED: kafka/hadoop.hadoop.com@HADOOP.COM for krbtgt/HADOOP.COM@HADOOP.COM,Decrypt integrity check failed

### 解决办法

步骤1 确认集群外连接Kafka的节点IP地址信息（如原因分析示例中的192.168.1.93）。

步骤2 登录集群外的节点，断开其对Kafka的认证。

步骤3 等待5分钟，此账号就会被解锁。

步骤4 重新尝试启动Kafka服务。

----结束

## 17.26 Kafka Broker 上报进程异常，报错“IllegalArgumentException” 7

### 问题背景与现象

使用Manager提示进程故障告警，查看告警进程为Kafka Broker。

### 可能原因

Broker配置异常。

### 原因分析

1. 在Manager页面，在告警页面得到主机信息。

2. 通过SSH登录Kafka Broker，执行cd /var/log/Bigdata/kafka/broker命令进入日志目录。

查看server.log发现如下日志抛出IllegalArgumentException异常，提示java.lang.IllegalArgumentException: requirement failed: replica.fetch.max.bytesshould be equal or greater than message.max.bytes。

2017-01-25 09:09:14,930 | FATAL | [main] | | kafka.Kafka$ (Logging.scala:113)
java.lang.IllegalArgumentException: requirement failed: replica.fetch.max.bytes should be equal or
greater than message.max.bytes at scala.Predef$.require(Predef.scala:233) at kafka.server.KafkaConfig.validateValues(KafkaConfig.scala:959) at kafka.server.KafkaConfig.<init>(KafkaConfig.scala:944) at kafka.server.KafkaConfig$.fromProps(KafkaConfig.scala:701) at kafka.server.KafkaConfig$.fromProps(KafkaConfig.scala:698) at kafka.server.KafkaServerStartable$.fromProps(KafkaServerStartable.scala:28) at kafka.Kafka$.main(Kafka.scala:60) at kafka.Kafka.main(Kafka.scala)

Kafka要求replica.fetch.max.bytes需要大于等于message.max.bytes。

3. 进入Kafka配置页面，选择“全部配置”， 显示所有Kafka相关配置，分别搜索message.max.bytes、replica.fetch.max.bytes进行检索，发现replica.fetch.max.bytes小于message.max.bytes。

### 解决办法

步骤1 登录Manager界面，进入Kafka配置页面。

MRS 3.x之前的版本：登录MRS Manager，选择“服务管理 > Kafka > 配置 > 全部配置”。

MRS 3.x及后续版本，登录FusionInsight Manager，选择“集群 > 服务 > Kafka> 配置 > 全部配置”。

步骤2 搜索并修改replica.fetch.max.bytes参数，使得replica.fetch.max.bytes的值大于等于message.max.bytes，使得不同Broker上的Partition的Replica可以同步到全部消息。

步骤3 保存配置，查看集群是否存在配置过期的服务，如果存在，需重启对应服务或角色实例使配置生效。

步骤4 修改消费者业务应用中fetch.message.max.bytes，使得fetch.message.max.bytes的值大于等于message.max.bytes，确保消费者可以消费到全部消息。

----结束

## 17.27 Kafka 集群节点内，多磁盘数据量占用高如何处理

### 用户问题

Kafka流式集群节点内有多块磁盘的使用量很高。当达到100%时就会造成kafka不可用如何处理？

### 问题现象

客户购买的MRS Kafka流式集群节点内有多块磁盘，由于分区不合理及业务原因导致某几个磁盘的使用量很高。当达到100%时就会造成kafka不可用。

### 原因分析

需要提前干预处理磁盘数据，全局的log.retention.hours修改需要重启服务。为了不断服，可以将数据量大的单个topic老化时间根据需要改短。

### 处理步骤

步骤1 登录Kafka集群的流式Core节点。

步骤2 执行df -h命令查看磁盘使用率。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/d6c7d40b-b4f0-4687-9da4-937721e1f554/185d44a726125b061a2f97374305f2d9f4fe969f9608c7345c15ca63e9271698.jpg)

步骤3 通过kafka配置文件/opt/Bigdata/MRS 2.1.0/1 11 Broker/etc/server.properties中的配置项log.dirs获得数据存储目录。

其中配置文件路径请根据时间环境的集群版本修改，当磁盘有多块时，该配置项有多个，逗号间隔。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/d6c7d40b-b4f0-4687-9da4-937721e1f554/18be5754dc1f7650569404a6dcbab97c22d07bc0320c5ee63827b4b3a888f406.jpg)

步骤4 使用cd命令进入使用率较高的磁盘对应的步骤3中获取的数据存储目录下。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/d6c7d40b-b4f0-4687-9da4-937721e1f554/3fdeaefd413ae199950ae15183824c34879592065cfa7dc3fabdfcd723632ee1.jpg)

步骤5 使用du -sh *命令打印出当前topic的名称及大小。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/d6c7d40b-b4f0-4687-9da4-937721e1f554/4c7b027cb7cfa8ab82afb8095703dded9fe9395c295508acff0ccd380142c25f.jpg)

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/d6c7d40b-b4f0-4687-9da4-937721e1f554/366ad6b2dca4dd18855ecffd9a5d0618a5a994d1a2f11cee4d1df936061a2b23.jpg)

步骤6 由于Kafka的全局的数据保留时间默认是7天。部分topic由于业务写入量大，而这些topic的分区正好在上面使用量高的磁盘上，因此导致磁盘使用率较高。

可以通过修改全局数据的保留期为较短时间来释放磁盘空间，该方式需要重启Kafka服务才能生效，可能会影响业务运行。具体请参见步骤7。

可以单独将topic的数据保留期改为较短时间来释放磁盘空间，该方式无需重启Kafka服务即可生效。具体请参见步骤8。

步骤7 登录Manager页面，在Kafka的服务配置页面，切换为“全部配置”并搜索“log.retention.hours”配置项，该值默认为7天，请根据需要进行修改。

步骤8 可以单独将这些磁盘上的topic的数据老化时间修改为较短时间来解决该问题。

1. 查看topic数据过期时间。

bin/kafka-topics.sh --describe --zookeeper <ZooKeeper集群业务IP>:2181/kafka --topic kktest

(roots Mu kafka1s bin/kafka-topics.sh -describe -zookeeper 192.168.201.175:2181/kafka -topic kktest Topic:kktest PartitionCount:1 ReplicationFactor:1 Configs:retention.ms1000000 Topic: kktest Partition: 0 cas:1

2. 设置topic数据过期时间，其中--topic表示具体topic名称，retention.ms=具体的数据过期时间，单位是毫秒。

kafka-topics.sh --zookeeper <ZooKeeper集群业务IP>:2181/kafka --alter --topic kktest --config retention.ms=1000000

[root@node-master1nTNu kafka]# kafka-topics.sh --zookeeper 192.168.201.175:2181/kafka --alter --topic kktest --config retenti
ms=1000000
WARNING: Altering topic configuration from this script has been deprecated and may be removed in future releases. Going forward, please use kafka-configs.sh for this functionality
Updated config for topic "kktest"

设置数据过期时间之后系统可能不会立刻执行，删除操作在参数log.retention.check.interval.ms所规定时间之后开始执行，可以通过查看kafka的server.log检索是否有delete字段来判断删除操作是否生效，有delete字段则表示已经生效，也可以通过执行df -h命令查看磁盘的数据量占用情况判断设置是否生效。

log.retention.check.interval.ms = 300000

----结束
