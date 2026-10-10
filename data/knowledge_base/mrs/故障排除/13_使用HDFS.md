---

## 13.1 HDFS 容量达到 100%导致上层服务 HBase、Spark 等不可用

### 问题描述

集群的HDFS容量使用达到100%，HDFS服务状态为只读，导致上层服务HBase、Spark等上报服务不可用告警。

### 问题现象

HDFS使用容量100%，磁盘容量只使用85%左右，HDFS服务状态为只读，导致上层服务HBase、Spark等上报服务不可用。

### 原因分析

当前NodeManager和DataNode共数据盘使用，MRS默认预留15%的数据磁盘空间给非HDFS使用，可通过HDFS参数“dfs.datanode.du.reserved.percentage”修改百分比来控制具体的磁盘占比。

当HDFS磁盘使用100%之后，可通过降低“dfs.datanode.du.reserved.percentage”百分比来恢复业务，再进行磁盘扩容。

### 处理步骤

步骤1 登录集群任意Master节点。

步骤2 执行 `source /opt/client/bigdata_env` 命令，初始化环境变量。

> **说明**：如果是安全集群，则需要执行 `kinit -kt <keytab file> <principal name>` 进行认证。

步骤3 执行 `hdfs dfs -put ./startDetail.log /tmp` 命令，测试HDFS写文件失败。

```
19/05/12 10:07:32 WARN hdfs.DataStreamer: DataStreamer Exception org.apache.hadoop.ipc.RemoteException(java.io.IOException): File /tmp/startDetail.log._COPYING_ could only be replicated to 0 nodes instead of minReplication (=1). There are 3 datanode(s) running and no node(s) are excluded in this operation.
```

步骤4 执行 `hdfs dfsadmin -report` 命令，检查HDFS使用容量，发现已经达到100%。

```
Configured Capacity: 5389790579100 (4.90 TB)
Present Capacity: 5067618628404 (4.61 TB)
DFS Remaining: 133350196 (127.17 MB)
DFS Used: 5067485278208 (4.61 TB)
DFS Used%: 100.00%
Under replicated blocks: 10
Blocks with corrupt replicas: 0
Missing blocks: 0
Missing blocks (with replication factor 1): 0
Pending deletion blocks: 0
```

步骤5 当HDFS使用容量达到100%时，通过HDFS参数“dfs.datanode.du.reserved.percentage”修改百分比来控制具体的磁盘占比。

1. 登录Manager进入服务配置页面。
   - MRS Manager界面操作入口：登录MRS Manager，依次选择“服务管理>HDFS>配置”。
   - FusionInsight Manager界面操作入口：登录FusionInsight Manager，选择“集群>服务>HDFS>配置”。
2. 选择“全部配置”，在搜索框中搜索“dfs.datanode.du.reserved.percentage”。
3. 修改此参数的取值为“10”。

步骤6 修改完成后，扩容Core节点的磁盘个数。

----结束

## 13.2 启动 HDFS 和 Yarn 服务报错“Permission denied”

### 问题描述

启动HDFS和Yarn时报错。

### 问题现象

无法启动HDFS、Yarn服务组件，报错内容：/dev/null Permission denied。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-04/61754321-9258-4018-a91e-47382976d70a/6c3fe9a2097272b43dafd2890cdb10b8b64db48386386502c6e57e54d4fc39e4.jpg)

### 原因分析

用户修改了虚机系统的“/dev/null”的权限值为775。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-04/61754321-9258-4018-a91e-47382976d70a/6d4dd91fde5c0866628d7366babba27cd38deea01f20bb017a8716015910ff0e.jpg)

### 处理步骤

步骤1 以root用户登录集群的任意一个Master节点。

步骤2 登录成功后，执行 `chmod 666 /dev/null` 命令，修改“/dev/null”的权限值为“666”。

步骤3 执行 `ls -al /dev/null` 命令，查看修改的“/dev/null”权限值是否为“666”，如果不是，需要修改为“666”。

步骤4 修改成功后，重新启动HDFS和Yarn组件。

----结束

## 13.3 集群外节点访问 MRS HDFS 报错

### 问题描述

集群外节点访问MRS HDFS的时候报错：Class org.apache.hadoop.hdfs.server.namenode.ha.AdaptiveFailoverProxyProvider not found。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-04/61754321-9258-4018-a91e-47382976d70a/8ef5a33c52254796721503dc31227c3dcd8d51457826b1ecc0937847e8a41732.jpg)

### 原因分析

出现这个报错可能的场景有：

- 开源HDFS客户端访问MRS集群的HDFS时报错。
- 使用jar包连接MRS集群的HDFS（包括提交任务时连接HDFS）时报错。

### 处理步骤

**方法一**

步骤1 找到命令或者jar包使用的HDFS配置文件hdfs-site.xml。

步骤2 修改“dfs.client.failover.proxy.provider.hacluster”参数配置项如下。

```xml
<property>
  <name>dfs.client.failover.proxy.provider.hacluster</name>
  <value>org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider</value>
</property>
```

> **说明**：也可以将上述配置项删除。

步骤3 保存文件后，重新访问MRS HDFS。

**方法二**

步骤1 从Maven库下载MRS集群版本对应的hadoop-plugins版本。下载路径：https://repo.huaweicloud.com/repository/maven/huaweicloudsdk/com/huawei/mrs/hadoop-plugins/

步骤2 将下载的jar包添加到命令或者jar包的依赖中。

----结束

## 13.4 修改 RPC 端口后 HDFS NameNode 实例都变为备状态

### 问题描述

通过页面更改NameNode的RPC端口，随后重启HDFS服务，出现所有NameNode一直是备状态，导致集群异常。

### 问题现象

所有NameNode都是备状态，导致集群异常。

### 原因分析

集群安装启动后，如果修改NameNode的RPC端口，则需要重新格式化Zkfc服务来更新zookeeper上的节点信息。

### 处理步骤

步骤1 登录Manager，停止HDFS服务。

> **说明**：在停止HDFS时，建议不要停止相关服务。

步骤2 停止成功后，登录到被修改了RPC端口的Master节点。

> **说明**：如果两个Master节点都被修改了RPC端口，则只需登录其中一个修改即可。

步骤3 执行 `su - omm` 命令切换到omm用户。

> **说明**：如果是安全集群，需要执行 `kinit hdfs` 命令进行认证。

步骤4 执行如下命令，将环境变量脚本加载到环境中。

```shell
cd ${BIGDATA_HOME}/MRS_X.X.X/1_8_Zkfc/etc
source ${BIGDATA_HOME}/MRS_X.X.X/install/FusionInsight-Hadoop-3.1.1/hadoop/sbin/exportENV_VARS.sh
```

> **说明**：命令中的“MRS_X.X.X”和“1_8”根据实际版本而定。

步骤5 加载完成后，执行如下命令，格式化Zkfc。

```shell
cd ${HADOOP_HOME}/bin
./hdfs zkfc -formatZK
```

步骤6 格式化成功后，在Manager页面“重启”HDFS服务。

> **说明**：如果更改了NameNode的RPC端口，则之前安装的所有客户端都需要刷新配置文件。

----结束

## 13.5 内存不足导致 HDFS NameNode 启动失败

### 问题描述

场景一：重启HDFS服务后，HDFS的状态为Bad，且NameNode实例状态异常，并且很久没有退出安全模式。

场景二：NameNode启动时，启动超时后启动失败，原生页面无法打开。

### 原因分析

1. 在NameNode运行日志（/var/log/Bigdata/hdfs/nn/hadoop-omm-namenode-XXX.log）中搜索“WARN”，可以看到有大量时间在垃圾回收，如下例中耗时较长63s。

```
2017-01-22 14:52:32,641 |WARN|org.apache.hadoop.util.JvmPauseMonitor$Monitor@1b39fd82 |Detected pause in JVM or host machine (eg GC): pause of approximately 63750ms GC pool 'ParNew' had collection(s): count=1 time=0ms GC pool 'ConcurrentMarkSweep' had collection(s): count=1 time=63924ms | JvmPauseMonitor.java:189
```

2. 分析NameNode日志“/var/log/Bigdata/hdfs/nn/hadoop-omm-namenode-XXX.log”，可以看到NameNode在等待块上报，且总的Block个数过多，如下例中是3629万。

```
2017-01-22 14:52:32,641 | INFO | IPC Server handler 8 on 25000 | STATE* Safe mode ON. The reported blocks 29715437 needs additional 6542184 blocks to reach the threshold 0.9990 of total blocks 36293915.
```

3. 打开Manager页面，选择“集群>服务>HDFS>配置>全部配置”，搜索查看NameNode的GC_OPTS参数配置如下：

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-04/61754321-9258-4018-a91e-47382976d70a/94582099805d6242817547752b438168203677b19590adf25647b8b961b5bf1b.jpg)

图 13-1 查看 NameNode 的 GC_OPTS 参数配置

4. NameNode内存配置和数据量对应关系参考表13-1。

表13-1 NameNode 内存配置和数据量对应关系

| 文件对象数量 | 参考值 |
| --- | --- |
| 10,000,000 | “-Xms6G -Xmx6G -XX:NewSize=512M -XX:MaxNewSize=512M” |
| 20,000,000 | “-Xms12G -Xmx12G -XX:NewSize=1G -XX:MaxNewSize=1G” |
| 50,000,000 | “-Xms32G -Xmx32G -XX:NewSize=2G -XX:MaxNewSize=3G” |
| 100,000,000 | “-Xms64G -Xmx64G -XX:NewSize=4G -XX:MaxNewSize=6G” |
| 200,000,000 | “-Xms96G -Xmx96G -XX:NewSize=8G -XX:MaxNewSize=9G” |
| 300,000,000 | “-Xms164G -Xmx164G -XX:NewSize=12G -XX:MaxNewSize=12G” |

### 处理步骤

步骤1 按照表13-1规格修改NameNode的内存参数，例如有3600万Block（Block个数≈文件对象数量），将内存参数调整为“-Xms32G -Xmx32G -XX:NewSize=2G -XX:MaxNewSize=3G”。

步骤2 重启一个NameNode，确认该NameNode可以正常启动。

步骤3 重启另一个NameNode，确认页面状态恢复。

----结束

## 13.6 单 NameNode 长期故障时如何使用客户端手动 checkpoint

### 问题描述

在备NameNode长期异常的情况下，会积攒大量的editlog，此时如果重启HDFS或者主NameNode，主NameNode会读取大量的未合并的editlog，导致耗时启动较长，甚至启动失败。

### 原因分析

备NameNode会周期性做合并editlog，生成fsimage文件的过程叫做checkpoint。备NameNode在新生成fsimage后，会将fsimage传递到主NameNode。

> **说明**：由于“备NameNode会周期性做合并editlog”，因此当备NameNode异常时，无法合并editlog，因此主NameNode在下次启动的时候，需要加载较多editlog，需要大量内存，并且耗时较长。

合并元数据的周期由以下参数确定，即如果NameNode运行30分钟或者HDFS操作100万次，均会执行checkpoint。

- dfs.namenode.checkpoint.period：checkpoint周期，默认1800s。
- dfs.namenode.checkpoint.txns：执行指定操作次数后执行checkpoint，默认1000000。

### 处理步骤

在重启前，主动执行异常checkpoint合并主NameNode的元数据。

步骤1 停止业务。

步骤2 获取主NameNode的主机名。

步骤3 在客户端执行如下命令：

```shell
source /opt/client/bigdata_env
kinit 组件用户
```

> **说明**：“/opt/client”需要改为实际客户端的安装路径。

步骤4 执行如下命令，使主NameNode进入安全模式，其中linux22替换为主NameNode的主机名。

```shell
hdfs dfsadmin -fs 主NameNode的主机名:25000 -safemode enter
```

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-04/61754321-9258-4018-a91e-47382976d70a/f42509597538a6ae9cd0bd35040109b690bebd98a98f34909f056dc2b43e157d.jpg)

步骤5 执行如下命令，在主NameNode节点上合并editlog。

```shell
hdfs dfsadmin -fs 主NameNode的主机名:25000 -saveNamespace
```

```
linux16:/opt/fi_client # hdfs dfsadmin -fs linux22:25000 -saveNamespace
17/04/26 18:38:54 WARN fs.FileSystem: "linux22:25000" is a deprecated filesystem name. Use "hdfs://linux22:25000/" instead.
17/04/26 18:38:56 INFO hdfs.PeerCache: SocketCache disabled.
Save namespace successful
```

步骤6 执行如下命令，使主NameNode离开安全模式。

```shell
hdfs dfsadmin -fs 主NameNode的主机名:25000 -safemode leave
```

```
linux16:/opt/fi_client # hdfs dfsadmin -fs linux22:25000 -safemode leave
17/04/26 18:39:07 WARN fs.FileSystem: "linux22:25000" is a deprecated filesystem name. Use "hdfs://linux22:25000/" instead.
17/04/26 18:39:09 INFO hdfs.PeerCache: SocketCache disabled.
Safe mode is OFF
```

步骤7 检查是否合并完成。

```shell
cd /srv/BigData/namenode/current
```

检查先产生的fsimage是否是当前时间的，若是则表示已经合并完成。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-04/61754321-9258-4018-a91e-47382976d70a/31bd0930e6c845f091733b4f77b0b69a2a9c1d9bff9fd475add6e769c914c42d.jpg)

----结束

## 13.7 删除大量文件后重启 NameNode 耗时长

### 问题描述

删除大量文件之后立刻重启NameNode（例如删除100万个文件），NameNode启动慢。

### 处理步骤

由于在删除了大量文件之后，DataNode需要时间去删除对应的Block。当立刻重启NameNode时，NameNode会去检查所有DataNode上报的Block信息，发现已删除的Block时，会输出对应的INFO日志信息，如下所示：

```
2015-06-10 19:25:50,215 | INFO | IPC Server handler 36 on 25000 | BLOCK* processReport: blk_1075861877_2121067 on node 10.91.8.218:9866 size 10249 does not belong to any file | org.apache.hadoop.hdfs.server.blockmanagement.BlockManager.processReport(BlockManager.java:1854)
```

每一个被删除的Block会产生一条日志信息，一个文件可能会存在一个或多个Block。当删除的文件数过多时，NameNode会花大量的时间打印日志，然后导致NameNode启动慢。

当出现这种现象时，您可以通过如下方式提升NameNode的启动速度。

1. 删除大量文件时，不要立刻重启NameNode，待DataNode删除了对应的Block后重启NameNode，即不会存在这种情况。
   您可以通过 `hdfs dfsadmin -report` 命令来查看磁盘空间，检查文件是否删除完毕。
2. 如已大量出现以上日志，您可以将NameNode的日志级别修改为ERROR，NameNode不会再打印此日志信息。
   等待NameNode启动完毕后，再将此日志级别修改为INFO。修改日志级别后无需重启服务。

----结束

## 13.8 EditLog 不连续导致 NameNode 启动失败

### 问题描述

在JournalNode节点有断电，数据目录磁盘占满，网络异常时，会导致JournalNode上的EditLog不连续。此时如果重启NameNode，很可能会失败。

### 问题现象

重启NameNode会失败。在NameNode运行日志中会报如下的错误：

```
2019-11-08 16:30:28,399  ERROR  main  Failed to start namenode. | NameNode.java:1732
java.io.IOException: There appears to be a gap in the edit log. We expected txid 13698019, but got txid 13698088.
at org.apache.hadoop.hdfs.server.namenode.MetaRecoveryContext.editLogLoaderPrompt(MetaRecoveryContext.java:94)
at org.apache.hadoop.hdfs.server.namenode.FSEditLogLoader.loadEditRecords(FSEditLogLoader.java:278)
at org.apache.hadoop.hdfs.server.namenode.FSEditLogLoader.loadFSEdits(FSEditLogLoader.java:188)
at org.apache.hadoop.hdfs.server.namenode.FSImage.loadEdits(FSImage.java:924)
at org.apache.hadoop.hdfs.server.namenode.FSImage.loadFSImage(FSImage.java:771)
at org.apache.hadoop.hdfs.server.namenode.FSImage.recoverTransitionRead(FSImage.java:331)
at org.apache.hadoop.hdfs.server.namenode.FSNamesystem.loadFSImage(FSNamesystem.java:1108)
at org.apache.hadoop.hdfs.server.namenode.FSNamesystem.loadFromDisk(FSNamesystem.java:727)
at org.apache.hadoop.hdfs.server.namenode.NameNode.loadNamesystem(NameNode.java:638)
at org.apache.hadoop.hdfs.server.namenode.NameNode.initialize(NameNode.java:700)
at org.apache.hadoop.hdfs.server.namenode.NameNode.<init>(NameNode.java:943)
at org.apache.hadoop.hdfs.server.namenode.NameNode.<init>(NameNode.java:916)
at org.apache.hadoop.hdfs.server.namenode.NameNode.createNameNode(NameNode.java:1655)
at org.apache.hadoop.hdfs.server.namenode.NameNode.main(NameNode.java:1725)
```

### 处理步骤

1. 找到重启前的主NameNode，进入其数据目录（查看配置项“dfs.namenode.name.dir”可获取，例如/srv/BigData/namenode/current），得到最新的FSImage文件的序号。一般如下：

```
-rw- 1 omm wheel 574 0ct 2 01:12 edits_0000000000013259401-00000000000
-rw- ---. 1 omm wheel 575 0ct 2 01:13 edits_0000000000013259409-00000000000:
-rw- 1 omm wheel 42 0ct 2 01:13 edits_0000000000013259417-00000000000:
-rw- ---. 1 omm wheel 1048576 Nov 8 16:01 edits_inprogress_0000000000013698088
-rw- 1 omm wheel 314803 Nov 8 15:53 fsimage_0000000000013698018
-rw- ---. 1 omm wheel 62 Nov 8 15:53 fsimage_0000000000013698018.md5
-rw- -. 1 omm wheel 314803 Nov 8 15:56 fsimage_0000000000013698050
-rw- ---. 1 omm wheel 62 Nov 8 15:56 fsimage_0000000000013698050.md5
-rw- ---. 1 omm wheel 314803 Nov 8 15:59 fsimage_0000000000013698066
-rw- --. 1 omm wheel 62 Nov 8 15:59 fsimage_0000000000013698066.md5
-rw- ---. 1 omm wheel 9 0ct 2 01:13 seen_txid
-rw- ---. 1 omm wheel 187 Nov 8 15:59 VERSION
```

2. 查看各JournalNode的数据目录（查看配置项“dfs.journalnode.edits.dir”可获取，例如/srv/BigData/journalnode/hacluster/current），查看序号从第一步获取到的序号开始的edits文件，看是否有不连续的情况（即前一个edits文件的最后一个序号和后一个edits文件的第一个序号不是连续的，如下图中的edits_0000000000013259231-0000000000013259237和后一个edits_0000000000013259239-0000000000013259246就是不连续的）。

```
-rw 1 omm wheel 575 0ct 2 00:41 edits_0000000000013259151-0000000000013259158
-rw 1 omm wheel 575 0ct 2 00:43 edits_0000000000013259159-0000000000013259166
-rw 1 omm wheel 576 0ct 2 00:43 edits_0000000000013259167-0000000000013259174
-rw 1 omm wheel 575 0ct 2 00:45 edits_0000000000013259175-0000000000013259182
-rw 1 omm wheel 575 0ct 2 00:45 edits_0000000000013259183-0000000000013259190
-rw 1 omm wheel 576 0ct 2 00:47 edits_0000000000013259191-0000000000013259198
-rw 1 omm wheel 575 0ct 2 00:48 edits_0000000000013259199-0000000000013259206
-rw 1 omm wheel 575 0ct 2 00:49 edits_0000000000013259207-0000000000013259214
-rw 1 omm wheel 575 0ct 2 00:50 edits_0000000000013259215-0000000000013259222
-rw 1 omm wheel 573 0ct 2 00:51 edits_0000000000013259223-0000000000013259230
-rw 1 omm wheel 571 0ct 2 00:52 edits_0000000000013259231-0000000000013259237
-rw 1 omm wheel 576 0ct 2 00:53 edits_0000000000013259239-0000000000013259246
-rw 1 omm wheel 575 0ct 2 00:54 edits_0000000000013259247-0000000000013259254
-rw 1 omm wheel 576 0ct 2 00:55 edits_0000000000013259255-0000000000013259262
-rw 1 omm wheel 42 0ct 2 00:56 edits_0000000000013259263-0000000000013259264
-rw 1 omm wheel 1107 0ct 2 00:57 edits_0000000000013259265-0000000000013259278
-rw 1 omm wheel 42 0ct 2 00:58 edits_0000000000013259279-0000000000013259280
-rw 1 omm wheel 1109 0ct 2 00:59 edits_0000000000013259281-0000000000013259294
-rw 1 omm wheel 42 0ct 2 01:00 edits_0000000000013259295-0000000000013259296
-rw 1 omm wheel 1299 0ct 2 01:01 edits_0000000000013259297-0000000000013259312
-rw 1 omm wheel 260 0ct 2 01:02 edits_0000000000013259313-0000000000013259316
-rw 1 omm wheel 984 0ct 2 01:03 edits_0000000000013259317-0000000000013259328
-rw 1 omm wheel 572 0ct 2 01:04 edits_0000000000013259329-0000000000013259336
-rw 1 omm wheel 575 0ct 2 01:05 edits_0000000000013259337-0000000000013259344
-rw 1 omm wheel 983 0ct 2 01:06 edits_0000000000013259345-0000000000013259356
```

3. 如果有这种不连续的edits文件，则需要查看其它的JournalNode的数据目录或NameNode数据目录中，有没有连续的该序号相关的连续的edits文件。如果可以找到，复制一个连续的片段到该JournalNode。

4. 如此把所有的不连续的edits文件全部都修复。

5. 重启NameNode，观察是否成功。如还是失败，请联系技术支持。

----结束

## 13.9 当备 NameNode 存储元数据时，断电后备 NameNode 启动失败

### 问题描述

当Standby NameNode存储元数据（命名空间）时，出现断电的情况，Standby NameNode启动失败并发生如下错误信息。

```
2015-12-04 11:49:12,121 | ERROR | main | Failed to load image from FSImageFile(file=/srv/BigData/namenode/current/fsimage_0000000000000096080, cpktTxId=0000000000000096080) | FSImage.java:685

java.io.IOException: Invalid MD5 file /srv/BigData/namenode/current/fsimage_0000000000000096080.md5: the content "银斤拷银斤拷银斤拷银斤拷锟[1m^A!锟 does not match the expected pattern.

at org.apache.hadoop.hdfs.util.MD5FileUtils.readStoredMd5(MD5FileUtils.java:92)
at org.apache.hadoop.hdfs.util.MD5FileUtils.readStoredMd5ForFile(MD5FileUtils.java:109)
at org.apache.hadoop.hdfs.server.namenode.FSImage.loadFSImage(FSImage.java:975)
at org.apache.hadoop.hdfs.server.namenode.FSImage.loadFSImageFile(FSImage.java:744)
at org.apache.hadoop.hdfs.server.namenode.FSImage.loadFSImage(FSImage.java:682)
at org.apache.hadoop.hdfs.server.namenode.FSImage.recoverTransitionRead(FSImage.java:300)
at org.apache.hadoop.hdfs.server.namenode.FSNamesystem.loadFSImage(FSNamesystem.java:968)
at org.apache.hadoop.hdfs.server.namenode.FSNamesystem.loadFromDisk(FSNamesystem.java:675)
at org.apache.hadoop.hdfs.server.namenode.NameNode.loadNamesystem(NameNode.java:625)
at org.apache.hadoop.hdfs.server.namenode.NameNode.initialize(NameNode.java:685)
at org.apache.hadoop.hdfs.server.namenode.NameNode.<init>(NameNode.java:889)
at org.apache.hadoop.hdfs.server.namenode.NameNode.<init>(NameNode.java:872)
at org.apache.hadoop.hdfs.server.namenode.NameNode.createNameNode(NameNode.java:1580)
at org.apache.hadoop.hdfs.server.namenode.NameNode.main(NameNode.java:1654)
```

### 处理步骤

当Standby NameNode存储元数据（命名空间）时，出现断电的情况，Standby NameNode启动失败，MD5文件会损坏。通过移除损坏的fsimage，然后启动Standby NameNode，可以修复此问题。Standby NameNode会加载先前的fsimage并重现所有的edits。

1. 移除损坏的fsimage。

```shell
rm -rf ${BIGDATA_DATA_HOME}/namenode/current/fsimage_0000000000000096080
```

2. 启动Standby NameNode。

----结束

## 13.10 备 NameNode 节点长时间未启动，导致启动失败

### 问题描述

长时间没有启动备NameNode，edits文件由于老化策略被自动清理后，重新启动NameNode时找不到所需的edits文件，从而报错。

```
There appears to be a gap in the edit log. We expected txid XXX, but got txid XXX.
```

### 处理步骤

步骤1 登录FusionInsight Manager。

步骤2 选择“集群>服务>HDFS>配置>全部配置”。

步骤3 搜索并查看“dfs.namenode.name.dir”参数值获取NameNode数据目录，例如获取到数据目录为“/srv/BigData/namenode/current”。

> **说明**：dfs.namenode.name.dir表示DFS NameNode在本地文件系统存储fsimage的目录。如果设置为一个以逗号分隔的目录列表，那fsimage会复制到该列表中的所有目录以进行冗余备份。默认值为“${BIGDATA_DATADIR}/namenode”。

步骤4 在HDFS服务页面选择“实例”页签，查看并记录主备NameNode节点的业务IP地址。

步骤5 以root用户登录发生故障的备NameNode节点，将步骤3获取的数据目录中的fsimage文件进行备份。例如备份到“/srv/BigData/namenode/current.bak”路径下。

```shell
mv /srv/BigData/namenode/current /srv/BigData/namenode/current.bak
```

步骤6 以root用户登录主NameNode节点，执行如下命令复制fsimage文件到备NameNode节点。

```shell
scp -rp /srv/BigData/namenode/current/{备NameNode节点IP}:/srv/BigData/namenode/
chown omm:wheel /srv/BigData/namenode/current -R
```

步骤7 重启备NameNode，观察是否重启成功。如果失败请联系技术支持进行处理。

----结束

## 13.11 HDFS 的 DataNode 一直显示退服中

### 问题描述

HDFS的DataNode一直显示退服中。

### 问题现象

HDFS的某个DataNode退服（或者对Core节点进行缩容）任务失败，但是DataNode在任务失败后一直处于退服中的状态。

### 原因分析

在对HDFS的某个DataNode进行退服（或者对Core节点进行缩容）过程中，因为Master节点重启或者nodeagent进程意外退出等情况出现，使得退服（或缩容）任务失败，并且没有进行黑名单清理。此时DataNode节点会一直处于退服中的状态，需要人工介入进行黑名单清理。

### 处理步骤

步骤1 进入服务实例界面。

- MRS Manager界面操作：登录MRS Manager，在MRS Manager页面，选择“服务管理>HDFS>实例”。
- FusionInsight Manager界面操作：对于MRS 3.x及后续版本集群，可登录FusionInsight Manager，选择“集群>服务>HDFS>实例”。也可登录MRS控制台，选择“组件管理>HDFS>实例”。

步骤2 查看HDFS服务实例状态，找到一直处于退服中的DataNode，复制这个DataNode的IP地址。

步骤4 执行 `sed -i "/^IP$/d" excludeHosts` 命令清理黑名单中的故障DataNode信息，该命令中IP替换为步骤2中查询到的故障DataNode的IP地址，其中不能有空格。

步骤5 如果有两个Master节点，请在Master2节点上同样执行步骤3和步骤4。

步骤6 在Master1节点执行如下命令初始化环境变量。

```shell
source 客户端安装目录/bigdata_env
```

步骤7 如果当前集群已启用Kerberos认证，执行以下命令认证当前用户。如果当前集群未启用Kerberos认证，则无需执行此命令。

```shell
kinit 具有HDFS操作权限的业务用户
```

步骤8 在Master1节点执行如下命令刷新HDFS的黑名单。

```shell
hdfs dfsadmin -refreshNodes
```

步骤9 执行 `hdfs dfsadmin -report` 命令来查看各个DataNode的状态，确认步骤2中查到的IP对应的DataNode已经恢复为“Normal”状态。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-04/61754321-9258-4018-a91e-47382976d70a/e5138c0b497326e083883e7a7b14425bbf6917b960f654abe129092ba3a3f245.jpg)

图 13-2 DataNode 的状态

步骤10 进入服务实例界面。

- MRS Manager界面操作：登录MRS Manager，在MRS Manager页面，选择“服务管理>HDFS>实例”。
- FusionInsight Manager界面操作：对于MRS 3.x及后续版本集群，可登录FusionInsight Manager，选择“集群>服务>HDFS>实例”。也可登录MRS控制台，选择“组件管理>HDFS>实例”。

步骤11 勾选一直处于退服中的DataNode实例，单击“更多>重启实例”。

步骤12 等待重启完成，确认DataNode是否恢复正常。

----结束

### 建议与总结

尽量不要在退服（或缩容）过程中重启节点等高危操作。

## 13.12 DataNode 偶现 CPU 占用接近 100%导致节点无法连接

### 问题描述

DataNode概率性出现CPU占用接近100%，导致节点丢失（ssh连得很慢或者连不上）。

图 13-3 DataNode 出现 CPU 占用接近 100%

```
PID USER PR NI VIRT RES SHR S %CPU %MEM TIME+ COMMAND
60636 20 9445m 16m 299 1.3 1952:06 -Dpro /var/log/Bigdata/hdfs/dn/jsvc. /var/log/Bigdata/hdfs/dn/javc.err -pidfil
.02428 ossadm 20 18116 3784 1828 155 0.0 1:17.63 /opt/tsp/manager/rtsp/python/bin/python /opt/tsp/manager/agent-1.3.10.200/tools/pyscript/sysappctrl.pyc cmd status
.02410 casadm 20 55016 8048 2836 155 0.0 1:59.80 /opt/tap/manager/rtap/python/bin/python /opt/tap/manager/agent-1.3.10.200/tools/pyscript/watchdog.pyc cmd status
.02412 ossadm 20 36752 5912 2340 155 0.0 1:50.32 /opt/tsp/manager/rtsp/python/bin/python /opt/tsp/manager/agent-1.3.10.200/tools/pyscript/sysappctrl.pyc cmd procinfo
.02484 cem 12800 1476 1124 155 0.0 0:10.73 /bin/bash /jdk1.7.0_80//bin/java -server -Xmx1024m -Djava.io.tmpdir=/export/datal/yarn/nm/localds
.02341 ossadm 20 57760 8688 3000 R 139 0.0 3:29.41 /opt/tsp/manager/rtsp/python/bin/python /opt/tsp/manager/agent/tools/pyscript/syscollector.pyc sys /opt/tsp/manager/var
02531 20 11176 640 468 106 0:04.19
```

### 原因分析

1. DataNode有许多写失败的日志。

图 13-4 DataNode 写失败的日志

```
2015-08-31 11:29:34,184 |ERROR | DataXceiver for client DFSClient_NONMAPREDUCE_1675952887_23 at /192.168.8.40:44514 [Receiving block BP-125271511-192.168.8.29-1440656260530:blk_1074766997_1034914] | TSP21:25009:DataXceiver error processing WRITE_BLOCK operation src: /192.168.8.40:44514 dst: /192.168.8.64:25009|DataXceiver.java:258
java.io.IOException: Premature EOF from inputStream
at org.apache.hadoop.io.IOUtils.readFully(IOUtils.java:194)
at org.apache.hadoop.hdfs.protocol.datatransfer.PacketReceiver.doReadFully(PacketReceiver.java:213)
at org.apache.hadoop.hdfs.protocol.datatransfer.PacketReceiver.doRead(PacketReceiver.java:134)
at org.apache.hadoop.hdfs.protocol.datatransfer.PacketReceiver.receiveNextPacket(PacketReceiver.java:109)
at org.apache.hadoop.hdfs.server.datanode.BlockReceiver.receiveBlock(BlockReceiver.java:707)
at org.apache.hadoop.hdfs.server.datanode.DataXceiver.writeBlock(DataXceiver.java:748)
at org.apache.hadoop.hdfs.protocol.datatransfer.Receiver.opWriteBlock(Receiver.java:124)
at org.apache.hadoop.hdfs.protocol.datatransfer.Receiver.processOp(Receiver.java:71)
at org.apache.hadoop.hdfs.server.datanode.DataXceiver.run(DataXceiver.java:240)
at java.lang.Thread.run(Thread.java:745)

2015-08-31 11:29:35,147 |INFO| DataXceiver for client DFSClient_NONMAPREDUCE_-402997805_1 at /192.168.8.30:59449 [Sending block BP-125271511-192.168.8.29-1440656260530:blk_1074181856_446655] src: /192.168.8.64:25009, dest: /192.168.8.30:59449, bytes: 16826, op: HDFS_READ, cliID: DFSClient_NONMAPREDUCE_-402997805_1, offset: 0, srvID: 9d1d30a5-046d-438b-83c9-2c6c54c6bd12, blockid: BP-125271511-192.168.8.29-1440656260530:blk_1074181856_446655, duration: 78832|BlockSender.java:738

2015-08-31 11:29:35,269 | INFO| org.apache.hadoop.util.JvmPauseMonitor$Monitor@551bd2a0 | Detected pause in JVM or host machine (eg GC): pause of approximately 7480ms

2015-08-31 11:29:36,985 | INFO| org.apache.hadoop.util.JvmPauseMonitor$Monitor@551bd2a0 | Detected pause in JVM or host machine (eg GC): pause of approximately 1215ms

2015-08-31 11:29:43,067 | INFO | DataXceiver for client DFSClient_NONMAPREDUCE_1675952887_23 at /192.168.8.33:35530 [Receiving block BP-125271511-192.168.8.29-1440656260530:blk_1074767006_1034923]|Exception for BP-125271511-192.168.8.29-1440656260530:blk_1074767006_1034923| BlockReceiver.java:742
```

2. 短时间内写入大量文件导致这种情况，因此DataNode内存不足。

图 13-5 写入大量文件导致 DataNode 内存不足

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-04/61754321-9258-4018-a91e-47382976d70a/5f56e84ff1b7f2d6fe60869e9c2ad703c5795979e3643e09e1aacb5ad7332bf2.jpg)

### 处理步骤

步骤1 检查DataNode内存配置，以及机器剩余内存是否充足。

步骤2 增加DataNode内存，并重启DataNode。

----结束

## 13.13 由于 HDFS 块丢失导致 DataNode 退服失败

### 问题描述

在退服DataNode过程中，一直提示退服失败。

### 原因分析

1. 查看退服失败报错日志，日志中显示总计1564个块，有一个块一直没法被备份。

```
[2021-02-25 09:52:46]NameNode#192.168.1.51, current underReplicatedBlocks: 1, total blocks: 1564.
[2021-02-25 09:52:50]NameNode#192.168.1.51, current underReplicatedBlocks: 1, total blocks: 1564.
[2021-02-25 09:52:55]NameNode#192.168.1.51, current underReplicatedBlocks: 1, total blocks: 1564.
[2021-02-25 09:52:59]NameNode#192.168.1.51, current underReplicatedBlocks: 1, total blocks: 1564.
[2021-02-25 09:53:03]NameNode#192.168.1.51, current underReplicatedBlocks: 1, total blocks: 1564.
[2021-02-25 09:53:07]NameNode#192.168.1.51, current underReplicatedBlocks: 1, total blocks: 1564.
[2021-02-25 09:53:11]NameNode#192.168.1.51, current underReplicatedBlocks: 1, total blocks: 1564.
[2021-02-25 09:53:16]NameNode#192.168.1.51, current underReplicatedBlocks: 1, total blocks: 1564.
[2021-02-25 09:53:20]NameNode#192.168.1.51, current underReplicatedBlocks: 1, total blocks: 1564.
[2021-02-25 09:53:20]Node 192.168.1.44 decommission failed, no data was decommissioned in 30 minutes.
[2021-02-25 09:53:20]192.168.1.44#DataNode cannot be decommissioned.
```

2. 登录集群Master节点，进入HDFS客户端，执行 `hdfs fsck /` 命令查看损坏的块，并记录文件路径。

例如：/tmp/hive-scratch/omm/_tez_session_dir/xxx-resources/xxx.jar。

并且HDFS状态为“CORRUPT”。

```
Erasure Coded Block Groups:
Total size: 0 B
Total files: 0
Total block groups (validated): 0
Minimally erasure-coded block groups: 0
Over-erasure-coded block groups: 0
Under-erasure-coded block groups: 0
Unsatisfactory placement block groups: 0
Average block group size: 0.0
Missing block groups: 0
Corrupt block groups: 0
Missing internal blocks: 0
FSCK ended at Thu Feb 25 17:36:56 CST 2021 in 2584 milliseconds
The filesystem under path '/' is CORRUPT
```

### 处理步骤

步骤1 请确认该损坏的块是否可以删除。

- 是，执行步骤2。
- 否，请联系技术支持。

步骤2 执行以下命令进入HDFS客户端。

```shell
cd HDFS客户端安装目录
source bigdata_env
kinit 业务用户
```

步骤3 执行以下命令删除之前记录的损坏的块。

```shell
hdfs dfs -rm -skipTrash /tmp/hive-scratch/omm/_tez_session_dir/xxx-resources/xxx.jar
```

步骤4 执行命令查看HDFS状态是否恢复为“HEALTHY”。

```shell
hdfs fsck /
```

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-04/61754321-9258-4018-a91e-47382976d70a/db9a2da2ba7f90aba3646a12ed7b39bff626e8d61ea8edac440acc1be4bb0faa.jpg)

步骤5 再次执行DataNode退服操作。

----结束

## 13.14 dfs.datanode.data.dir 中定义的磁盘数量等于 dfs.datanode.failed.volumes.tolerated 的值时，DataNode 启动失败

### 问题描述

当“dfs.datanode.data.dir”（DataNode在本地文件系统中存储块的位置）中定义的磁盘数量等于“dfs.datanode.failed.volumes.tolerated”（DataNode停止提供服务前允许失败的卷数）的值时，DataNode启动失败。

### 处理步骤

默认情况下，单个磁盘的故障将会引起HDFS DataNode进程关闭，导致NameNode为每一个存在DataNode上的block调度额外的副本，在没有故障的磁盘中引起不必要的块复制。

为了防止此情况，用户可以通过配置DataNodes来承受dfs.data.dir目录的故障。

1. 登录Manager，选择“集群>服务>HDFS>配置>全部配置”。

2. 搜索参数“dfs.datanode.failed.volumes.tolerated”。

“dfs.datanode.failed.volumes.tolerated”：表示DataNode停止提供服务前允许失败的卷数。默认情况下，必须至少有一个有效卷。值-1表示有效卷的最小值是1。大于等于0的值表示允许失败的卷数。默认值“-1”，取值范围：-1~DataNode上配置的磁盘卷数。

例如：如果当前该参数值为3，DataNode只有在4个或者更多个目录故障之后才会出现故障。该值会影响到DataNode的启动。

如果想要DataNode不出现故障，配置的“dfs.datanode.failed.volumes.tolerated”一定要小于所配置的卷数，也可以将“dfs.datanode.failed.volumes.tolerated”设置成-1，相当于设置该值为n-1（n为卷数），那样DataNode就不会出现启动失败。

3. 修改完成后保存，并重启配置过期的服务或实例。

----结束

## 13.15 HDFS 写文件失败，报错“item limit of xxx is exceeded”

### 问题描述

客户端或者上层组件日志报往HDFS的某目录写文件失败，报错为：

```
The directory item limit of /tmp is exceeded: limit=5 items=5。
```

### 原因分析

1. 查看客户端或者NameNode运行日志“/var/log/Bigdata/hdfs/nn/hadoop-omm-namenode-XXX.log”存在异常提示The directory item limit of /tmp is exceeded:。该错误的含义为/tmp目录的文件数超过1048576的限制。

```
2018-03-14 11:18:21,625 | WARN |IPC Server handler 62 on 25000 | DIR* NameSystem.startFile: /tmp/test.txt The directory item limit of /tmp is exceeded: limit=1048576 items=1048577 |FSNamesystem.java:2334
```

2. 该限制是dfs.namenode.fs-limits.max-directory-items参数，定义单个目录下不含递归的最大目录数或者文件数，默认值1048576，取值范围1～6400000。

### 处理步骤

步骤1 确认该目录不含递归拥有100万以上文件目录是否正常，如果正常，可以将HDFS的参数dfs.namenode.fs-limits.max-directory-items调大并且重启HDFS NameNode生效。

步骤2 如果该目录下拥有100万文件不正常，需要清理不需要的文件。

----结束

## 13.16 HDFS 读写文件失败，报错“Failed to place enough replicas”

### 问题描述

当用户在HDFS上执行写操作时，出现“Failed to place enough replicas: expected…”信息。

### 原因分析

- DataNode的数据接收器不可用。

```
2016-03-17 18:51:44,721 | WARN |
org.apache.hadoop.hdfs.server.datanode.DataXceiverServer@5386659f |
hadoopc1h2:25009:DataXceiverServer: | DataXceiverServer.java:158
java.io.IOException: Xceiver count 4097 exceeds the limit of concurrent xcievers: 4096
at org.apache.hadoop.hdfs.server.datanode.DataXceiverServer.run(DataXceiverServer.java:140)
at java.lang.Thread.run(Thread.java:745)
```

- DataNode的磁盘空间不足。
- DataNode的心跳有延迟。

### 处理步骤

如果DataNode的数据接收器不可用，通过在Manager页面，增加HDFS参数“dfs.datanode.max.transfer.threads”的值解决。

如果没有足够的硬盘空间或者CPU，试着增加新的数据节点或确保资源是可用的（磁盘空间或CPU）。

如果网络问题，确保网络是可用的。

----结束

## 13.17 HDFS 读取文件失败，报错“FileNotFoundException”

### 问题描述

有MapReduce任务所有map任务均成功，但reduce任务失败，查看日志发现报异常“FileNotFoundException..No lease on..File does not exist”。

```
Error: org.apache.hadoop.ipc.RemoteException(java.io.FileNotFoundException): No lease on /user/sparkhive/warehouse/daas/dsp/output/_temporary/1/_temporary/attempt_1479799053892_17075_r_000007_0/partr-00007 (inode 6501287): File does not exist. Holder DFSClient_attempt_1479799053892_17075_r_000007_0_-1463597952_1 does not have any open files. at org.apache.hadoop.hdfs.server.namenode.FSNamesystem.checkLease(FSNamesystem.java:3350) at org.apache.hadoop.hdfs.server.namenode.FSNamesystem.completeFileInternal(FSNamesystem.java:3442) at org.apache.hadoop.hdfs.server.namenode.FSNamesystem.completeFile(FSNamesystem.java:3409) at org.apache.hadoop.hdfs.server.namenode.NameNodeRpcServer.complete(NameNodeRpcServer.java:789)
```

### 原因分析

FileNotFoundException...No lease on...File does not exist，该日志说明文件在操作的过程中被删除了。

1. 搜索HDFS的NameNode的审计日志（Active NameNode的/var/log/Bigdata/audit/hdfs/nn/hdfs-audit-namenode.log）搜索文件名，确认文件的创建时间。

2. 搜索文件创建到出现异常时间范围的NameNode的审计日志，搜索该文件是否被删除或者移动到其他目录。

3. 如果该文件没有被删除或者移动，可能是该文件的父目录，或者更上层目录被删除或者移动，需要继续搜索上层目录。如本样例中，是文件的父目录被删除。

```
2017-05-31 02:04:08,286 | INFO | IPC Server handler 30 on 25000 | allowed=true ugi=appUser@HADOOP.COM (auth:TOKEN) ip=/192.168.1.22 cmd=delete src=/user/sparkhive/warehouse/daas/dsp/output/_temporary dst=null perm=null proto=rpc | FSNamesystem.java:8189
```

> **说明**：
> - 如上日志说明：192.168.1.22节点的appUser用户删除了/user/sparkhive/warehouse/daas/dsp/output/_temporary。
> - 可以使用 `zgrep "文件名" *.zip` 命令搜索zip包的内容。

### 处理步骤

步骤1 需要排查业务，确认为何该文件或者文件的父目录被删除。

----结束

## 13.18 HDFS 读文件失败，报错“No common protection layer”

### 问题描述

shell客户端或者其他客户端操作HDFS失败，报“No common protection layer between client and server”。

在集群外的机器，执行任意hadoop命令，如 `hadoop fs -ls /` 均失败，最底层的报错为“No common protection layer between client and server”。

```
2017-05-13 19:14:19,060 | ERROR | [pool-1-thread-1] | Server startup failure|
org.apache.sqoop.core.SqoopServer.initializeServer(SqoopServer.java:69)
org.apache.sqoop.common.SqoopException: MAPRED_EXEC_0028:Failed to operate HDFS - Failed to get the
file /user/loader/etl_dirty_data_dir status at org.apache.sqoop.job.mr.HDFSClient.fileExist(HDFSClient.java:85) at java.lang.Thread.run(Thread.java:745)
Caused by: java.io.IOException: Failed on local exception: java.io.IOException: Couldn't setup connection for
loader/hadoop@HADOOP.COM to loader37/10.162.0.37:25000; Host Details : local host is:
"loader37/10.162.0.37"; destination host is: "loader37":25000; at org.apache.hadoop.net.NetUtils.wrapException(NetUtils.java:776)
... 10 more Caused by: java.io.IOException: Couldn't setup connection for loader/hadoop@HADOOP.COM to loader37/10.162.0.37:25000
at org.apache.hadoop.ipc.Client$Connection$1.run(Client.java:674 ... 28 more
Caused by: javax.security.sasl.SaslException: No common protection layer between client and server at com.sun.security.sasl.gsskerb.GssKrb5Client.doFinalHandshake(GssKrb5Client.java:251)
at org.apache.hadoop.ipc.Client$Connection.setupIOstreams(Client.java:720)
```

### 原因分析

1. HDFS的客户端和服务端数据传输走的rpc协议，该协议有多种加密方式，由hadoop.rpc.protection参数控制。

2. 如果客户端和服务端的hadoop.rpc.protection参数的配置值不一样，即会报No common protection layer between client and server错误。

> **说明**：hadoop.rpc.protection参数表示数据可通过以下任一方式在节点间进行传输。
> - privacy：指数据在鉴权及加密后再传输。这种方式会降低性能。
> - authentication：指数据在鉴权后直接传输，不加密。这种方式能保证性能但存在安全风险。
> - integrity：指数据直接传输，即不加密也不鉴权。为保证数据安全，请谨慎使用这种方式。

### 处理步骤

步骤1 重新下载客户端，如果是应用程序，更新应用程序中的配置文件。

----结束

## 13.19 HDFS 写数据时报错“java.net.SocketException”

### 问题描述

为什么在往HDFS写数据时报“java.net.SocketException: No buffer space available”异常？

这个问题发生在往HDFS写文件时。查看客户端和DataNode的错误日志。

客户端日志如下：

图 13-6 客户端日志

```
2017-07-05 21:58:06,459 INFO [htable-pool3-t1] ipc.AbstractRpcClient: RPC Server Kerberos principal name for service=ClientService is hbase/hadoop.hadoop123.com@HADOOP12
2017-07-05 21:58:06,893 WARN [main] mapreduce.LoadIncrementalHFiles: Skipping non-directory hdfs://hacluster/HBaseTest/bulkload_output/_SUCCESS
2017-07-05 21:59:13,211 WARN [main] hdfs.BlockReaderFactory: I/O error constructing remote block reader.
java.net.SocketException: No buffer space available
at sun.nio.ch.Net.connect0(Native Method)
at sun.nio.ch.Net.connect(Net.java:454)
at sun.nio.ch.Net.connect(Net.java:446)
at sun.nio.ch.SocketChannelImpl.connect(SocketChannelImpl.java:648)
at org.apache.hadoop.net.SocketIOwithTimeout.connect(SocketIOwithTimeout.java:192)
at org.apache.hadoop.net.NetUtils.connect(NetUtils.java:531)
at org.apache.hadoop.hdfs.DFSClient.newConnectedPeer(DFSClient.java:3345)
at org.apache.hadoop.hdfs.BlockReaderFactory.nextTcpPeer(BlockReaderFactory.java:789)
at org.apache.hadoop.hdfs.BlockReaderFactory.getRemoteBlockReaderFromTcp(BlockReaderFactory.java:706)
at org.apache.hadoop.hdfs.BlockReaderFactory.build(BlockReaderFactory.java:369)
at org.apache.hadoop.hdfs.DFSInputStream.getBlockReader(DFSInputStream.java:713)
at org.apache.hadoop.hdfs.DFSInputStream.blockSeekTo(DFSInputStream.java:663)
at org.apache.hadoop.hdfs.DFSInputStream.readWithStrategy(DFSInputStream.java:919)
at org.apache.hadoop.hdfs.DFSInputStream.read(DFSInputStream.java:973)
at java.io.DataInputStream.readFully(DataInputStream.java:195)
at org.apache.hadoop.hbase.io.hfile.FixedFileTrailer.readFromStream(FixedFileTrailer.java:391)
at org.apache.hadoop.hbase.io.hfile.HFile.isHFileFormat(HFile.java:578)
at org.apache.hadoop.hbase.io.hfile.HFile.isHFileFormat(HFile.java:560)
at org.apache.hadoop.hbase.mapreduce.LoadIncrementalHFiles.visitBulkHFiles(LoadIncrementalHFiles.java:229)
at org.apache.hadoop.hbase.mapreduce.LoadIncrementalHFiles.discoverLoadQueue(LoadIncrementalHFiles.java:281)
at org.apache.hadoop.hbase.mapreduce.LoadIncrementalHFiles.prepareHFileQueue(LoadIncrementalHFiles.java:452)
at org.apache.hadoop.hbase.mapreduce.LoadIncrementalHFiles.doBulkLoad(LoadIncrementalHFiles.java:365)
at org.apache.hadoop.hbase.mapreduce.LoadIncrementalHFiles.doBulkLoad(LoadIncrementalHFiles.java:331)
at org.apache.hadoop.hbase.mapreduce.LoadIncrementalHFiles.run(LoadIncrementalHFiles.java:1107)
at org.apache.hadoop.util.ToolRunner.run(ToolRunner.java:70)
at org.apache.hadoop.hbase.mapreduce.LoadIncrementalHFiles.main(LoadIncrementalHFiles.java:1114)
2017-07-05 21:59:13,215 WARN [main] hdfs.DFSClient: Failed to connect to /192.168.152.128:25009 for block BP-1989348819-192.168.199.5-1497961637591:blk_1107301222_335745
java.net.SocketException: No buffer space available
at sun.nio.ch.Net.connect0(Native Method)
at sun.nio.ch.Net.connect(Net.java:454)
at sun.nio.ch.Net.connect(Net.java:446)
at sun.nio.ch.SocketChannelImpl.connect(SocketChannelImpl.java:648)
at org.apache.hadoop.net.SocketIOwithTimeout.connect(SocketIOwithTimeout.java:192)
at org.apache.hadoop.net.NetUtils.connect(NetUtils.java:531)
at org.apache.hadoop.hdfs.DFSClient.newConnectedPeer(DFSClient.java:3345)
```

DataNode日志如下：

```
2017-07-24 20:43:39,269 | ERROR | DataXceiver for client DFSClient_NONMAPREDUCE_996005058_86
at /192.168.164.155:40214 [Receiving block
BP-1287143557-192.168.199.6-1500707719940:blk_1074269754_528941 with io weight 10]|
DataNode{data=FSDataset{dirpath='[/srv/BigData/hadoop/data1/dn/current, /srv/BigData/hadoop/
data2/dn/current, /srv/BigData/hadoop/data3/dn/current, /srv/BigData/hadoop/data4/dn/current, /srv/
BigData/hadoop/data5/dn/current,/srv/BigData/hadoop/data6/dn/current, /srv/BigData/hadoop/data7/dn/
current]'}, localName='192-168-164-155:9866', datanodeUuid='a013e29c-4e72-400c-bc7b-bbbf0799604c',
xmitslnProgress=0}:Exception transfering block
BP-1287143557-192.168.199.6-1500707719940:blk_1074269754_528941 to mirror 192.168.202.99:9866:
java.net.SocketException: No buffer space available | DataXceiver.java:870
2017-07-24 20:43:39,269 | INFO | DataXceiver for client DFSClient_NONMAPREDUCE_996005058_86
at /192.168.164.155:40214 [Receiving block
BP-1287143557-192.168.199.6-1500707719940:blk_1074269754_528941 with io weight 10] | opWriteBlock
BP-1287143557-192.168.199.6-1500707719940:blk_1074269754_528941 received exception
java.net.SocketException: No buffer space available | DataXceiver.java:933
2017-07-24 20:43:39,270 | ERROR | DataXceiver for client DFSClient_NONMAPREDUCE_996005058_86
at /192.168.164.155:40214 [Receiving block
BP-1287143557-192.168.199.6-1500707719940:blk_1074269754_528941 with io weight 10]|
192-168-164-155:9866:DataXceiver error processing WRITE_BLOCK operation src: /192.168.164.155:40214
dst: /192.168.164.155:9866 | DataXceiver.java:304 java.net.SocketException: No buffer space available
at sun.nio.ch.Net.connect0(Native Method)
at sun.nio.ch.Net.connect(Net.java:454)
at sun.nio.ch.Net.connect(Net.java:446)
at sun.nio.ch.SocketChannelImpl.connect(SocketChannelImpl.java:648)
at org.apache.hadoop.net.SocketIOWithTimeout.connect(SocketIOWithTimeout.java:192)
at org.apache.hadoop.net.NetUtils.connect(NetUtils.java:531)
at org.apache.hadoop.net.NetUtils.connect(NetUtils.java:495)
at org.apache.hadoop.hdfs.server.datanode.DataXceiver.writeBlock(DataXceiver.java:800)
at org.apache.hadoop.hdfs.protocol.datatransfer.Receiver.opWriteBlock(Receiver.java:138)
at org.apache.hadoop.hdfs.protocol.datatransfer.Receiver.processOp(Receiver.java:74)
at org.apache.hadoop.hdfs.server.datanode.DataXceiver.run(DataXceiver.java:265)
at java.lang.Thread.run(Thread.java:748)
```

### 处理步骤

上述问题可能是因为网络内存枯竭而导致的。

问题的解决方案是根据实际场景适当增大网络设备的阈值级别。

例如：

```shell
[root@xxxxx ~]# cat /proc/sys/net/ipv4/neigh/default/gc_thresh*
128
512
1024
[root@xxxxx ~]# echo 512 > /proc/sys/net/ipv4/neigh/default/gc_thresh1
[root@xxxxx ~]# echo 2048 > /proc/sys/net/ipv4/neigh/default/gc_thresh2
[root@xxxxx ~]# echo 4096 > /proc/sys/net/ipv4/neigh/default/gc_thresh3
[root@xxxxx ~]# cat /proc/sys/net/ipv4/neigh/default/gc_thresh*
512
2048
4096
```

还可以将以下参数添加到“/etc/sysctl.conf”中，即使主机重启，配置依然能生效。

```
net.ipv4.neigh.default.gc_thresh1 = 512
net.ipv4.neigh.default.gc_thresh2 = 2048
net.ipv4.neigh.default.gc_thresh3 = 4096
```

----结束

## 13.20 HDFS 写文件并发较大时报副本不足

### 问题描述

用户运行作业时写文件到HDFS，偶现写文件失败的情况。

操作日志如下：

```
105 | INFO | IPC Server handler 23 on 25000 | IPC Server handler 23 on 25000, call
org.apache.hadoop.hdfs.protocol.ClientProtocol.addBlock from 192.168.1.96:47728 Call#1461167 Retry#0 Server.java:2278
java.io.IOException: File /hive/warehouse/000000_0.835bf64f-4103 could only be replicated to 0 nodes instead of minReplication (=1). There are 3 datanode(s) running and 3 node(s) are excluded in this operation.
```

### 原因分析

HDFS写文件的预约机制：无论文件是10 MB还是1 GB，开始写的每个块都会被预约128 MB。如果需要写入一个10 MB的文件，HDFS会预约一个块来写，当文件写完后，这个块只占实际大小10MB，释放多余预约的118MB空间。如果需要写入一个1 GB的文件，HDFS还是会预约一个块来写，这个块写完后再开启下一个块，文件写完后，实际占用1GB磁盘，释放多余预约的空间。

该异常通常是因为业务写文件的并发量太高，预约写Block的磁盘空间不足，导致写文件失败。

### 处理步骤

步骤1 登录HDFS的WebUI页面，进入DataNode的JMX页面。

1. 在HDFS原生界面，选择Datanodes页面。
2. 找到对应的DataNode节点，单击Http Address地址进入DataNode详情。
3. 将url的“datanode.html”改为“jmx”就能获取到DataNode的JMX信息。

步骤2 搜索“XceiverCount”指标，当该指标的值*Block块的大小超过DataNode磁盘的容量，就说明预约写Block的磁盘空间不足。

步骤3 发生该问题，通常有以下两种方法来解决：

**方法一**：降低业务的并发度。

**方法二**：减少业务写文件的数目，将多个文件合并成一个文件来写。

----结束

## 13.21 HDFS 客户端写文件 close 失败

### 问题描述

HDFS客户端写文件close失败，客户端提示数据块没有足够副本数。

客户端日志：

```
2015-05-27 19:00:52.811 [pool-2-thread-3] ERROR: /tsp/nedata/collect/UGW/ugwufdr/
20150527/10/6_20150527105000_20150527105500_SR5S14_1432723806338_128_11.pkg.tmp1432723806338 close hdfs sequence file fail (SequenceFileInfoChannel.java:444)
java.io.IOException: Unable to close file because the last block does not have enough number of replicas. at org.apache.hadoop.hdfs.DFSOutputStream.completeFile(DFSOutputStream.java:2160)
at org.apache.hadoop.hdfs.DFSOutputStream.close(DFSOutputStream.java:2128)
at org.apache.hadoop.fs.FSDataOutputStream$PositionCache.close(FSDataOutputStream.java:70)
at org.apache.hadoop.fs.FSDataOutputStream.close(FSDataOutputStream.java:103)
at com.huawei.pai.collect2.stream.SequenceFileInfoChannel.close(SequenceFileInfoChannel.java:433) at com.huawei.pai.collect2.stream.SequenceFileWriterToolChannel$FileCloseTask.call(SequenceFileWriterToolChannel.java:804)
at com.huawei.pai.collect2.stream.SequenceFileWriterToolChannel$FileCloseTask.call(SequenceFileWriterToolChannel.java:792) at java.util.concurrent.FutureTask.run(FutureTask.java:262)
at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1145) at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:615) at java.lang.Thread.run(Thread.java:745)
```

### 原因分析

1. HDFS客户端开始写Block。

例如：HDFS客户端是在2015-05-27 18:50:24,232开始写/tsp/nedata/collect/UGW/ugwufdr/20150527/10/6_20150527105000_20150527105500_SR5S14_1432723806338_128_11.pkg.tmp1432723806338的。其中分配的块是blk_1099105501_25370893。

```
2015-05-27 18:50:24,232 | INFO | IPC Server handler 30 on 25000 | BLOCK* allocateBlock: /tsp/nedata/collect/UGW/ugwufdr/20150527/10/6_20150527105000_20150527105500_SR5S14_1432723806338_128_11.pkg.tmp1432723806338. BP-1803470917-192.168.57.33-1428597734132 blk_1099105501_25370893{blockUCState=UNDER_CONSTRUCTION, primaryNodeIndex=-1, replicas=[ReplicaUnderConstruction[[DISK]DS-b2d7b7d0-f410-4958-8eba-6deecbca2f87:NORMAL|RBW], ReplicaUnderConstruction[[DISK]DS-76bd80e7-ad58-49c6-bf2c-03f91caf750f:NORMAL|RBW]]}
```

2. 写完之后HDFS客户端调用了fsync。

```
2015-05-27 19:00:22,717 | INFO | IPC Server handler 22 on 25000 | BLOCK* fsync:20150527/10/6_20150527105000_20150527105500_SR5S14_1432723806338_128_11.pkg.tmp1432723806338 for DFSClient_NONMAPREDUCE_-120525246_15 |org.apache.hadoop.hdfs.server.namenode.FSNamesystem.fsync(FSNamesystem.java:3805)
```

3. HDFS客户端调用close关闭文件，NameNode收到客户端的close请求之后就会检查最后一个块的完成状态，只有当有足够的DataNode上报了块完成才可关闭文件，检查块完成的状态是通过checkFileProgress函数检查的，打印如下：

```
2015-05-27 19:00:27,603 | INFO | IPC Server handler 44 on 25000 | BLOCK* checkFileProgress:blk_1099105501_25370893{blockUCState=COMMITTED, primaryNodeIndex=-1,replicas=[ReplicaUnderConstruction[[DISK]DS-ef5fd3c9-5088-4813-ae9a-34a0714ec3a3:NORMAL|RBW], ReplicaUnderConstruction[[DISK]DS-f863e30f-ce5b-48cc-9cca-72f64c558adc:NORMAL|RBW]]}has not reached minimal replication 1 |org.apache.hadoop.hdfs.server.namenode.FSNamesystem.checkFileProgress(FSNamesystem.java:3197)
2015-05-27 19:00:28,005 | INFO | IPC Server handler 45 on 25000 | BLOCK* checkFileProgress:blk_1099105501_25370893{blockUCState=COMMITTED, primaryNodeIndex=-1,replicas=[ReplicaUnderConstruction[[DISK]DS-ef5fd3c9-5088-4813-ae9a-34a0714ec3a3:NORMAL|RBW], ReplicaUnderConstruction[[DISK]DS-f863e30f-ce5b-48cc-9cca-72f64c558adc:NORMAL|RBW]]}has not reached minimal replication 1 |org.apache.hadoop.hdfs.server.namenode.FSNamesystem.checkFileProgress(FSNamesystem.java:3197)
2015-05-27 19:00:28,806 | INFO | IPC Server handler 63 on 25000 | BLOCK* checkFileProgress:blk_1099105501_25370893{blockUCState=COMMITTED, primaryNodeIndex=-1,replicas=[ReplicaUnderConstruction[[DISK]DS-ef5fd3c9-5088-4813-ae9a-34a0714ec3a3:NORMAL|RBW], ReplicaUnderConstruction[[DISK]DS-f863e30f-ce5b-48cc-9cca-72f64c558adc:NORMAL|RBW]]}has not reached minimal replication 1 |org.apache.hadoop.hdfs.server.namenode.FSNamesystem.checkFileProgress(FSNamesystem.java:3197)
2015-05-27 19:00:30,408 | INFO | IPC Server handler 43 on 25000 | BLOCK* checkFileProgress:blk_1099105501_25370893{blockUCState=COMMITTED, primaryNodeIndex=-1,replicas=[ReplicaUnderConstruction[[DISK]DS-ef5fd3c9-5088-4813-ae9a-34a0714ec3a3:NORMAL|RBW], ReplicaUnderConstruction[[DISK]DS-f863e30f-ce5b-48cc-9cca-72f64c558adc:NORMAL|RBW]]}has not reached minimal replication 1 |org.apache.hadoop.hdfs.server.namenode.FSNamesystem.checkFileProgress(FSNamesystem.java:3197)
2015-05-27 19:00:33,610 | INFO | IPC Server handler 37 on 25000 | BLOCK* checkFileProgress:blk_1099105501_25370893{blockUCState=COMMITTED, primaryNodeIndex=-1,replicas=[ReplicaUnderConstruction[[DISK]DS-ef5fd3c9-5088-4813-ae9a-34a0714ec3a3:NORMAL|RBW], ReplicaUnderConstruction[[DISK]DS-f863e30f-ce5b-48cc-9cca-72f64c558adc:NORMAL|RBW]]}has not reached minimal replication 1 |org.apache.hadoop.hdfs.server.namenode.FSNamesystem.checkFileProgress(FSNamesystem.java:3197)
2015-05-27 19:00:40,011 | INFO | IPC Server handler 37 on 25000 | BLOCK* checkFileProgress:blk_1099105501_25370893{blockUCState=COMMITTED, primaryNodeIndex=-1,replicas=[ReplicaUnderConstruction[[DISK]DS-ef5fd3c9-5088-4813-ae9a-34a0714ec3a3:NORMAL|RBW], ReplicaUnderConstruction[[DISK]DS-f863e30f-ce5b-48cc-9cca-72f64c558adc:NORMAL|RBW]]}has not reached minimal replication 1 |org.apache.hadoop.hdfs.server.namenode.FSNamesystem.checkFileProgress(FSNamesystem.java:3197)
```

4. NameNode打印了多次checkFileProgress是由于HDFS客户端多次尝试close文件，但是由于当前状态不满足要求，导致close失败，HDFS客户端retry的次数是由参数dfs.client.block.write.locateFollowingBlock.retries决定的，该参数默认是5，所以在NameNode的日志中看到了6次checkFileProgress打印。

5. 但是再过0.5s之后，DataNode就上报块已经成功写入。

```
2015-05-27 19:00:40,608 | INFO | IPC Server handler 60 on 25000 | BLOCK* addStoredBlock:
blockMap updated: 192.168.10.21:25009 is added to
blk_1099105501_25370893{blockUCState=COMMITTED, primaryNodeIndex=-1,
replicas=[ReplicaUnderConstruction[[DISK]DS-ef5fd3c9-5088-4813-ae9a-34a0714ec3a3:NORMAL|RBW], ReplicaUnderConstruction[[DISK]DS-f863e30f-ce5b-48cc-9cca-72f64c558adc:NORMAL|RBW]]}
size 11837530 |
org.apache.hadoop.hdfs.server.blockmanagement.BlockManager.logAddStoredBlock(BlockManager.java:2393)
2015-05-27 19:00:48,297 | INFO | IPC Server handler 37 on 25000 | BLOCK* addStoredBlock:
blockMap updated: 192.168.10.10:25009 is added to blk_1099105501_25370893 size 11837530 |
org.apache.hadoop.hdfs.server.blockmanagement.BlockManager.logAddStoredBlock(BlockManager.java:2393)
```

6. DataNode上报块写成功通知延迟的原因可能有：网络瓶颈导致、CPU瓶颈导致。

7. 如果此时再次调用close或者close的retry的次数增多，那么close都将返回成功。建议适当增大参数dfs.client.block.write.locateFollowingBlock.retries的值，默认值为5次，尝试的时间间隔为400ms、800ms、1600ms、3200ms、6400ms、12800ms，那么close函数最多需要25.2秒才能返回。

### 处理步骤

可以通过调整客户端参数dfs.client.block.write.locateFollowingBlock.retries的值来增加retry的次数，可以将值设置为6，那么中间睡眠等待的时间为400ms、800ms、1600ms、3200ms、6400ms、12800ms，也就是说close函数最多要50.8秒才能返回。

### 备注说明

一般出现上述现象，说明集群负载很大，通过调整参数只是临时规避这个问题，建议还是降低集群负载。

例如：避免把所有CPU都分配MapReduce跑任务。

----结束

## 13.22 HDFS 目录配额不足导致写文件失败

### 问题描述

给某目录设置quota后，往目录中写文件失败，出现如下问题“The DiskSpace quota of /tmp/tquota2 is exceeded”。

```
[omm@189-39-150-115 client]$ hdfs dfs -put switchuser.py /tmp/tquota2
put: The DiskSpace quota of /tmp/tquota2 is exceeded: quota = 157286400 B = 150 MB but diskspace consumed = 402653184 B = 384 MB
```

### 可能原因

目录配置的剩余的空间小于写文件实际需要的空间。

### 原因分析

1. HDFS支持设置某目录的配额，即限制某目录下的文件最多占用空间大小，例如如下命令是设置“/tmp/tquota”目录最多写入150MB的文件（文件大小*副本数）。

```shell
hadoop dfsadmin -setSpaceQuota 150M /tmp/tquota2
```

2. 使用如下命令可以查看目录设置的配额情况，SPACE_QUOTA是设置的空间配额，REM_SPACE_QUOTA是当前剩余的空间配额。

```shell
hdfs dfs -count -q -h -v /tmp/tquota2
```

图13-7 查看目录设置的配额

```
hdfs dfs -count -q -h -v /tmp/tquota2
QUOTA REM_QUOTA SPACE_QUOTA REM_SPACE_QUOTA DIR_COUNT FILE_COUNT CONTENT_SIZE PATHNAME
none inf 150M 150M 1 0 0 /tmp/tquota2
```

3. 日志分析，如下日志说明写入文件需要消耗384M，但是当前的空间配额是150M，因此空间不足。写文件前，需要的剩余空间是：块大小*副本数，128M*3副本=384M。

### 处理步骤

步骤1 增加配额大小，即重新设置目录的配额大小。

```shell
hadoop dfsadmin -setSpaceQuota 150G /目录名
```

步骤2 清空配额。

```shell
hdfs dfsadmin -clrSpaceQuota /目录名
```

----结束

## 13.23 文件错误导致上传文件到 HDFS 失败

### 问题描述

用 `hadoop dfs -put` 把本地文件拷贝到HDFS上，有报错。

上传部分文件后，报错失败，从NameNode原生页面看，临时文件大小不再变化。

### 原因分析

1. 查看NameNode日志“/var/log/Bigdata/hdfs/nn/hadoop-omm-namenode-主机名.log”，发现该文件一直在被尝试写，直到最终失败。

```
2015-07-13 10:05:07,847 | WARN| org.apache.hadoop.hdfs.server.namenode.LeaseManager$Monitor@36fea922 | DIR* NameSystem.internalReleaseLease: Failed to release lease for file /hive/order/OS_ORDER._8.txt._COPYING_. Committed blocks are waiting to be minimally replicated. Try again later. | FSNamesystem.java:3936
2015-07-13 10:05:07,847 | ERROR | org.apache.hadoop.hdfs.server.namenode.LeaseManager$Monitor@36fea922 | Cannot release the path /hive/order/OS_ORDER._8.txt._COPYING_ in the lease [Lease. Holder: DFSClient_NONMAPREDUCE_-1872896146_1, pendingcreates: 1] | LeaseManager.java:459
org.apache.hadoop.hdfs.protocol.AlreadyBeingCreatedException: DIR* NameSystem.internalReleaseLease: Failed to release lease for file /hive/order/OS_ORDER._8.txt._COPYING_. Committed blocks are waiting to be minimally replicated. Try again later.
at FSNamesystem.internalReleaseLease(FSNamesystem.java:3937)
```

2. 根因分析：被上传的文件损坏，因此会上传失败。

3. 验证办法：cp或者scp被拷贝的文件，也会失败，确认文件本身已损坏。

### 处理步骤

步骤1 文件本身损坏造成的此问题，采用正常文件进行上传。

----结束

## 13.24 集群外节点安装客户端上传 HDFS 文件失败

### 问题描述

集群外节点安装客户端使用hdfs命令上传文件失败。

### 问题现象

在集群节点上安装客户端，在该客户端使用hdfs命令上传一个文件，报如下错误：

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-04/61754321-9258-4018-a91e-47382976d70a/3c61b5c5acf2df6871ba7671882405562726168e7888716ca96b739a8a7b091d.jpg)

图 13-8 上传文件报错

### 原因分析

从错误截图可以看到报错是no route to host，且报错信息里面有192.168的ip，也即客户端节点到集群的DN节点的内网路由不通，导致上传文件失败。

### 处理步骤

在客户端节点的客户端目录下，找到HDFS的客户端配置目录hdfs-site.xml文件，在配置文件中增加配置项dfs.client.use.datanode.hostname，并将该配置设置为true。

----结束

## 13.25 查询或者删除 HDFS 文件失败

### 问题描述

使用HDFS的shell客户端查询或者删除文件失败，父目录可以看见此文件（不可见字符）。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-04/61754321-9258-4018-a91e-47382976d70a/51cc29a315772b1f071851cf925214f0d495ae893c84d0a5f9ab2e61824802b4.jpg)

图13-9 父目录文件列表

### 原因分析

可能是该文件写入时有异常，写入了不可见字符。可以将该文件名重定向写入本地文本中，使用vi命令打开。

```shell
hdfs dfs -ls 父目录 > /tmp/t.txt
vi /tmp/t.txt
```

然后输入命令“:set list”将文件名的不可见字符显示出来。如这里显示出文件名中包含“^M”不可见字符。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-04/61754321-9258-4018-a91e-47382976d70a/b5833fad8b8d7953013bceba37d319e483e07fd38b1b7ccd2057c26e41453b8d.jpg)

图13-10 显示不可见字符

### 处理步骤

步骤1 使用shell命令读到文本中记录的该文件名，确认如下命令输出的是该文件在HDFS中的全路径。

```shell
cat /tmp/t.txt | awk '{print $8}'
```

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-04/61754321-9258-4018-a91e-47382976d70a/a1a7ec8cf113d2aa96ed2d28fdb41358c36a381d4548fa72f6d021938e8c8fd9.jpg)

图 13-11 文件路径

步骤2 使用如下命令删除该文件。

```shell
hdfs dfs -rm $(cat /tmp/t.txt | awk '{print $8}')
```

步骤3 查看确认该文件已被删除。

```shell
hdfs dfs -ls 父目录
```

----结束

## 13.26 文件最大打开句柄数设置太小导致读写文件异常

### 问题描述

文件最大打开句柄数设置太小，导致文件句柄不足。写文件到HDFS很慢，或者写文件失败。

### 原因分析

1. DataNode日志“/var/log/Bigdata/hdfs/dn/hadoop-omm-datanode-XXX.log”，存在异常提示java.io.IOException: Too many open files。

```
2016-05-19 17:18:59,126 |WARN|
org.apache.hadoop.hdfs.server.datanode.DataXceiverServer@142ff9fa |
YSDN12:25009:DataXceiverServer:
org.apache.hadoop.hdfs.server.datanode.DataXceiverServer.run(DataXceiverServer.java:160)
java.io.IOException: Too many open files
at sun.nio.ch.ServerSocketChannelImpl.accept0(Native Method)
at sun.nio.ch.ServerSocketChannelImpl.accept(ServerSocketChannelImpl.java:241)
at sun.nio.ch.ServerSocketAdaptor.accept(ServerSocketAdaptor.java:100)
at org.apache.hadoop.hdfs.net.TcpPeerServer.accept(TcpPeerServer.java:134)
at org.apache.hadoop.hdfs.server.datanode.DataXceiverServer.run(DataXceiverServer.java:137)
at java.lang.Thread.run(Thread.java:745)
```

2. 如果某个DataNode日志中打印“Too many open files”，说明该节点文件句柄不足，导致打开文件句柄失败，然后就会重试往其他DataNode节点写数据，最终表现为写文件很慢或者写文件失败。

### 处理步骤

步骤1 执行 `ulimit -a` 命令查看有问题节点文件句柄数最多设置是多少，如果很小，建议修改成640000。

图13-12 查看文件句柄数

```
[omm@189-39-150-167 ~]$ ulimit -a
core file size (blocks, -c) 0
data seg size (kbytes, -d) unlimited
scheduling priority (-e) 0
file size (blocks, -f) unlimited
pending signals (-i) 256551
max locked memory (kbytes, -l) 64
max memory size (kbytes, -m) unlimited
open files (-n) 640000
pipe size (512 bytes, -p) 8
POSIX message queues (bytes, -q) 819200
real-time priority (-r) 0
stack size (kbytes, -s) 10240
cpu time (seconds, -t) unlimited
max user processes (-u) 60000
virtual memory (kbytes, -v) unlimited
file locks (-x) unlimited
```

步骤2 执行 `vi /etc/security/limits.d/90-nofile.conf` 命令编辑文件，修改文件句柄数设置。如果没有这个文件，可以新建一个文件，并按照下图内容修改。

图 13-13 修改文件句柄数

```ini
* hard nofile 640000
* soft nofile 640000
```

步骤3 重新打开一个终端窗口，用 `ulimit -a` 命令查看是否修改成功，如果没有，请重新按照上述步骤重新修改。

步骤4 从Manager页面重启DataNode实例。

----结束

## 13.27 调整 HDFS Shell 客户端日志级别

### 临时调整

临时调整，关闭该Shell客户端窗口后，日志会还原为默认值。

a. 执行 `export HADOOP_ROOT_LOGGER` 命令可以调整客户端日志级别。

b. 执行 `export HADOOP_ROOT_LOGGER=日志级别,console`，可以调整shell客户端的日志级别。

```shell
export HADOOP_ROOT_LOGGER=DEBUG,console   # 调整为DEBUG
export HADOOP_ROOT_LOGGER=ERROR,console   # 调整为ERROR
```

### 永久调整

a. 在HDFS客户端环境变量配置文件“/opt/client/HDFS/component_env”（其中“/opt/client”需要改为实际客户端路径）增加 `export HADOOP_ROOT_LOGGER=日志级别,console`。

b. 执行 `source /opt/client/bigdata_env`。

c. 重新执行客户端命令。

----结束

## 13.28 使用普通模式集群的 HDFS 客户端时报错“error creating DomainSocket”

### 问题描述

普通模式集群在Core节点新建用户，安装使用HDFS客户端报错“error creating DomainSocket”。

### 问题现象

普通集群在Core节点新建用户安装使用客户端报错如下：

```
2020-03-14 19:16:17,166 WARN shortcircuit.DomainSocketFactory: error creating DomainSocket
java.net.ConnectException: connect(2) error: Permission denied when trying to connect to '/var/run/MRS-HDFS/dn_socket'
at org.apache.hadoop.net.unix.DomainSocket.connect0(Native Method)
at org.apache.hadoop.net.unix.DomainSocket.connect(DomainSocket.java:256)
at org.apache.hadoop.hdfs.shortcircuit.DomainSocketFactory.createSocket(DomainSocketFactory.java:168)
at org.apache.hadoop.hdfs.client.impl.BlockReaderFactory.nextDomainPeer(BlockReaderFactory.java:799)
```

### 原因分析

用户使用 useradd 命令来创建用户，此用户默认用户组不包含“ficommon”用户组，导致在使用hdfs的get命令的时候出现上述报错。

### 处理步骤

使用命令 `usermod -a -G ficommon username` 为用户添加用户组“ficommon”。

----结束

## 13.29 执行 distcp 跨集群拷贝文件报错“Source and target differ in block-size”

### 问题描述

执行distcp跨集群拷贝文件时，出现部分文件拷贝失败“Source and target differ in block-size. Use -pb to preserve block-sizes during copy.”。

```
Caused by: java.io.IOException: Check-sum mismatch between hdfs://10.180.144.7:25000/kylin/kylin_default_instance_prod/parquet/f2e72874-f01c-45ff-b219-207f3a5b3fcb/c769cd2d-575a-4459-837b-a19dd7b20c27/339114721280/0.parquet and hdfs://10.180.180.194:25000/kylin/kylin_default_instance_prod/parquet/f2e72874-f01c-45ff-b219-207f3a5b3fcb/.distcp.tmp.attempt_1523424430246_0004_m_000019_2. Source and target differ in block-size. Use -pb to preserve block-sizes during copy. Alternatively, skip checksum-checks altogether, using -skipCrc. (NOTE: By skipping checksums, one runs the risk of masking data-corruption during file transfer.) at org.apache.hadoop.tools.mapred.RetriableFileCopyCommand.compareCheckSums(RetriableFileCopyCommand.java:214)
```

### 可能原因

distcp默认拷贝文件时不记录原block大小导致在原文件block.size不是128M时校验失败，需要在distcp命令增加-pb参数。

### 原因分析

1. HDFS在写的时候有设置块大小，默认128M，某些组件或者业务程序写入的文件可能不是128M，如8M。

```xml
<name>dfs.blocksize</name>
<value>134217728</value>
```

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-04/61754321-9258-4018-a91e-47382976d70a/961e2b8fc10cc951c197ee9299d60d658fd28adca4e2e53b8bbab732f953fa98.jpg)

图13-14 某些组件或者业务程序写入的文件大小

2. distcp 从源集群读文件后写入新集群，默认是使用的MapReduce任务中的dfs.blocksize，默认128M。

3. 在distcp写完文件后，会基于块的物理大小做校验，因为该文件在新旧集群中block.size不一致，因此拆分大小不一致，导致校验失败。如以上文件，在旧集群是17.9/8MB = 3个block，在新集群17.9/128M = 1个block，因此实际在磁盘的物理大小因分割而导致校验失败。

### 处理步骤

distcp时，增加-pb参数。该参数作用为distcp时候保留block大小，确保新集群写入文件blocksize和老集群一致。

图 13-15 distcp 时保留 block 大小

```
root@189-39-235-118 client~]# hadoop distcp -pb hdfs://haclusterX/user hdfs://hacluster/tmp/test
```

----结束

## 13.30 使用 distcp 命令拷贝空文件夹报错

### 问题描述

通过MRS客户端使用以下distcp命令，无法从HDFS复制空文件夹到OBS。

```
hadoop distcp -Dfs.obs.endpoint=xxx -Dfs.obs.access.key=xxx -Dfs.obs.secret.key=xxx -update hdfs://hacluster/blee obs://xxx/aaa
```

### 原因分析

如果源端（例如“blee”）为空目录，且目的端（例如“aaa”）目录不存在，系统会自动创建出来“aaa”目录，但是不会在“aaa”目录下面再创建“blee”目录。如果源端“blee”不是空目录，且目的端“aaa”目录不存在，系统会自动创建出来“aaa”目录，并在“aaa”目录下面再创建“blee”目录，进行文件迁移。

### 处理步骤

- 进行迁移操作时，源端目录（例如“blee”）不建议为空。
- 如果源端目录为空，在执行迁移前，需要手动创建目的端目录，即手动创建“aaa”目录。

----结束

## 13.31 HDFS 客户端无法删除超长目录

### 问题描述

执行 `hadoop fs -rm -r -f obs://<obs_path>` 命令，删除OBS超长目录出现如下报错：

```
2022-02-28 17:12:45,605 INFO internal.RestStorageService: OkHttp cost 19 ms to apply http request
2022-02-28 17:12:45,606 WARN internal.RestStorageService: Request failed, Response code: 400; Request ID: 0000017F3F9A8545401491602FC8CAD9; Request path: http://wordcount01-fcq.obs.example.com/user%2Froot%2F.Trash%2FCurrent%2Ftest1%2F12345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456
2022-02-28 17:12:45,606 WARN services.AbstractClient: Storage|1|HTTP+XML|getObjectMetadata|| 2022-02-28 17:12:45|2022-02-28 17:12:45|||400|
2022-02-28 17:12:45,607 INFO log.AccessLogger: 2022-02-28 17:12:45,605| com.obs.services.internal.RestStorageService|executeRequest|560|OkHttp cost 19 ms to apply http request
2022-02-28 17:12:45,606|com.obs.services.internal.RestStorageService|handleThrowable|221|Request failed, Response code: 400; Request ID: 0000017F3F9A8545401491602FC8CAD9; Request path: http://wordcount01-fcq.obs.example.com/user%2Froot%2F.Trash%2FCurrent%2Ftest1%2F12345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456
2022-02-28 17:12:45,606|com.obs.services.AbstractClient|doActionWithResult|404|Storage|1|HTTP+XML|getObjectMetadata||||2022-02-28 17:12:45|2022-02-28 17:12:45|||400|
```

### 原因分析

使用rm命令从HDFS中删除某些内容时，文件或目录不会立即被清除，它们将被移动到回收站Current目录（/user/${username}/.Trash/current）中。

### 处理步骤

使用skipTrash命令可以跳过HDFS回收站，直接删除。使用前先设置HDFS客户端配置项“dfs.client.skipTrash.enabled=true”。

步骤1 以root用户登录集群任一Master节点。

步骤2 执行如下命令编辑HDFS用到的“hdfs-site.xml”文件。

```shell
vim 客户端安装目录/HDFS/hadoop/etc/hadoop/hdfs-site.xml
```

步骤3 在hdfs-site.xml文件中增加如下内容。

```xml
<property>
  <name>dfs.client.skipTrash.enabled</name>
  <value>true</value>
</property>
```

步骤4 执行以下命令直接删除OBS超长目录。

```shell
hadoop fs -rm -r -f -skipTrash obs://<obs_path>
```

步骤5 登录集群其他Master节点，执行步骤2~步骤4，直到集群所有Master节点操作完成。

----结束

## 13.32 HDFS 调用 FileInputFormat 的 getSplit 的时候出现数组越界

### 问题描述

HDFS调用FileInputFormat的getSplit方法的时候，出现ArrayIndexOutOfBoundsException: 0，日志如下：

```
java.lang.ArrayIndexOutOfBoundsException: 0
at org.apache.hadoop.mapred.FileInputFormat.identifyHosts(FileInputFormat.java:708)
at org.apache.hadoop.mapred.FileInputFormat.getSplitHostsAndCachedHosts(FileInputFormat.java:675)
at org.apache.hadoop.mapred.FileInputFormat.getSplits(FileInputFormat.java:359)
at org.apache.spark.rdd.HadoopRDD.getPartitions(HadoopRDD.scala:210)
at org.apache.spark.rdd.RDD$$anonfun$partitions$2.apply(RDD.scala:239)
at org.apache.spark.rdd.RDD$$anonfun$partitions$2.apply(RDD.scala:237)
at scala.Option.getOrElse(Option.scala:120)
at org.apache.spark.rdd.RDD.partitions(RDD.scala:237)
at org.apache.spark.rdd.MapPartitionsRDD.getPartitions(MapPartitionsRDD.scala:35)
```

### 处理步骤

每个block对应的机架信息组成为：/default/rack0/:、/default/rack0/datanodeip:port。

该问题是由于某个block块损坏或者丢失，导致该block对应的机器ip和port为空引起的，出现该问题的时候使用 `hdfs fsck` 检查对应文件块的健康状态，删除损坏或者恢复丢失的块，重新进行任务计算即可。

----结束

## 13.33 ntpdate 修改时间导致 HDFS 出现大量丢块

### 问题描述

1. 用ntpdate修改了集群时间，修改时未停止集群，修改后HDFS进入安全模式，无法启动。

2. 退出安全模式后启动，fsck检查丢了大概1 TB数据。

### 原因分析

1. 查看NameNode原生页面发现有大量的块丢失。

图 13-16 块丢失

```
There are 41491 missing blocks. The following files may be corrupted:
blk_1090519588 /user/etlhadoop/struct_data/uds_data/PRS/20180130/DCH_PRS_PDWTMDTL_S_000_input/1/ccw-20180130-pdwtmdtl-023_022.bin_7
blk_1090519796 /user/etlhadoop/struct_data/uds_data/GCM/20180130/DCM_GCM_PNDLTA200211_H_output/1/part-m-00010
blk_1090520189 /user/hive/warehouse/prs_mc.db/dcm_prs_pdwtmdtl_s/pt_dt=2018-01-30/part-m-00004
blk_1082131961 /user/hive/warehouse/cas_mc.db/dcm_cas_nthpatel_h/end_dt=2017-12-31/000004_0
blk_1082132310 /user/hive/warehouse/cr1_mc.db/dcm_cr1_ees_tb2045_s/pt_dt=2017-12-31/000005_0
blk_1082132604 /user/hive/warehouse/cr1_mc.db/dcm_cr1_ecs_tb2045_s/pt_dt=2017-12-31/000040_0
blk_1090521279 /user/hive/warehouse/gcm_mc.db/dcm_gcm_pndlta200211_h/end_dt=2018-01-30/000006_0
blk_1090521284 /user/hive/warehouse/gcm_mc.db/dcm_gcm_pndlta200211_h/end_dt=2018-01-30/000012_0
blk_1090521427 /user/hive/warehouse/pis_mc.db/dcm_pis_lthpcdtl_h/end_dt=2018-01-30/000080_0
blk_1090521473 /user/hive/warehouse/pis_mc.db/dcm_pis_lthpcdtl_h/end_dt=2018-01-30/000016_0
blk_1082133176 /user/hive/warehouse/cas_mc.db/dcm_cas_kffpbat_s/pt_dt=2017-12-31/part-m-00006
blk_1090522261 /user/etlhadoop/struct_data/uds_data/ECS/20180130/DCH_ECS_TB1170_S_000_input/1/ccw-20180130-hdwb1171-022_032.bin_16
blk_1090522656 /user/etlhadoop/struct_data/uds_data/ECS/20180130/DCM_ECS_TB1170_S_output/1/part-m-00007
blk_1090522747 /user/hive/warehouse/gcm_mc.db/dcm_gcm_zassure_change_detail_s/pt_dt=2018-01-31/000002_0
blk_1082134372 /user/hive/warehouse/bcs_mc.db/dcm_bcs_bthrsism_h/pt_dt=2017-12-31/part-m-00006
blk_1090523585 /user/hive/warehouse/ecs_mc.db/dcm_ecs_tb1170_s/pt_dt=2018-01-30/000002_0
blk_1090523811 /user/hive/warehouse/nse_mc.db/dcm_nse_nfpjnl_s/pt_dt=2018-01-30/part-m-00005
blk_1082135337 /user/hive/warehouse/bcs_mc.db/dcm_bcs_bthrsism_h/pt_dt=2017-12-31/part-m-00022
blk_1090524043 /user/hive/warehouse/nse_mc.db/dcm_nse_nfpjnl_s/pt_dt=2018-01-30/part-m-00016
blk_1082138206 /user/hive/warehouse/bcs_mc.db/dcm_bcs_bthrsism_h/pt_dt=2017-12-31/part-m-00038
blk_1090525355 /user/hive/warehouse/bdsp_bcas_act.db/dcm_bcs_jzcs_detail/pt_dt=2017-11-30/000006_0
blk_1090526191 /user/hive/warehouse/bdsp_bcas_act.db/dcm_bcs_jzcs_detail/pt_dt=2017-11-30/000008_0
blk_1090526995 /user/hive/warehouse/bdsp_bcas_act.db/dcm_bcs_jzcs_detail/pt_dt=2017-11-30/000014_0
blk_1082140552 /user/hive/warehouse/ccs_mc.db/m01_ccs_corp_cust_mgr/pt_dt=2017-12-31/000001_0
blk_1090529399 /user/hive/warehouse/bdsp_bcas_act.db/dcm_bcs_jzcs_middle_t/pt_dt=2017-11-30/000017_0
blk_1090529420 /user/hive/warehouse/bdsp_bcas_act.db/dcm_bcs_jzcs_middle_t/pt_dt=2017-11-30/000014_0
blk_1082141596 /user/hive/warehouse/asa_mc.db/t80_asa_bcas_agt_stat/pt_dt=2017-12-31/000032_0
blk_1082141631 /user/hive/warehouse/asa_mc.db/t80_asa_bcas_agt_stat/pt_dt=2017-12-31/000003_0
blk_1082142345 /user/hive/warehouse/sum_mc.db/c00_prod_level_overview_h/pt_dt=2017-12-31/000000_0_copy_1514441582192
blk_1090531076 /user/etlhadoop/struct_data/uds_data/GCM/20180131/DCM_GCM_DEDUN_STOP_PARA_S_000_input/1/CMA_DEDUN_STOP_PARAD111800000-011-20180131.BIN_11_UTF
blk_1090531330 /user/hive/warehouse/gcc_mc.db/dcm_gcc_zcorp_motor_info_s/pt_dt=2018-01-31/000011_0
blk_1090531342 /user/hive/warehouse/gcc_mc.db/dcm_gcc_zcorp_motor_info_s/pt_dt=2018-01-31/000002_0
blk_1090531494 /user/etlhadoop/struct_data/uds_data/GCM/20180131/DCM_GCM_ZMORTGAGE_PROJECT_STAT_S_000_input/1/CHA_ZMORTGAGE_PROJECT_STAT_0050100000-
```

2. 查看原生页面Datanode Information发现显示的DataNode节点数和实际的相差10个节点。

图 13-17 查看 DataNode 节点数

```
Security is on.
Safemode is off.
14442 files and directories, 13907 blocks = 28349 total filesystem object(s).
Heap Memory used 495.63 MB of 1.99 GB Heap Memory. Max Heap Memory is 3.98 GB.
Non Heap Memory used 104.5 MB of 107.94 MB Committed Non Heap Memory. Max Non Heap Memory is 1.36 GB.
```

| 项目 | 值 |
| --- | --- |
| Configured Capacity | 112.09 GB |
| DFS Used | 15.33 GB (13.68%) |
| Non DFS Used | 18.56 GB |
| DFS Remaining | 78.2 GB (69.77%) |
| Block Pool Used | 15.33 GB (13.68%) |
| DataNodes usages% (Min/Median/Max/stdDev) | 13.56% / 13.73% / 13.73% / 0.08% |
| Live Nodes | 3 (Decommissioned: 0) |
| Dead Nodes | 0 (Decommissioned: 0) |
| Decommissioning Nodes | 0 |

3. 查看DataNode运行日志“/var/log/Bigdata/hdfs/dn/hadoop-omm-datanode-主机名.log”，发现如下错误信息。重要错误信息Clock skew too great。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-04/61754321-9258-4018-a91e-47382976d70a/811bd168c0bb03b0c3f43aed4adc8dd48bcac1a852f29dccfae7e2f1895fbbcc.jpg)

### 处理步骤

步骤1 修改在原生页面查看不到的10个数据节点的时间。

步骤2 在Manager页面重启对应的DataNode实例。

----结束

## 13.34 界面配置 dfs.blocksize 后上传数据，block 大小未改变

### 问题描述

界面配置“dfs.blocksize”，将其设置为268435456，上传数据，block大小还是原来的大小。

### 原因分析

HDFS客户端的“hdfs-site.xml”文件中的dfs.blocksize大小没有更改，以客户端配置为准。

### 处理步骤

步骤1 确保“dfs.blocksize”为512的倍数。

步骤2 重新下载安装客户端或者更改客户端配置。

步骤3 dfs.blocksize是客户端配置，以客户端为准。若客户端不配置，以服务端为准。

----结束

## 13.35 通过公网 IP 连接使用 HDFS 客户端报错

### 问题描述

通过公网IP连接主机，不能使用HDFS客户端，运行hdfs命令后提示“-bash: hdfs: command not found”。

### 原因分析

用户登录Master节点执行命令之前，未设置环境变量。

### 处理步骤

步骤1 以root用户登录任意一个Master节点。

步骤2 执行 `source 客户端安装目录/bigdata_env` 命令，设置环境变量。

步骤3 执行hdfs命令即可成功使用HDFS客户端。

----结束

## 13.36 使用 Python 远程连接 HDFS 的端口失败

### 问题描述

使用Python远程连接HDFS的端口失败，如何解决？

### 问题现象

用户使用Python远程连接HDFS的50070端口失败。

### 处理步骤

HDFS开源3.0.0以下版本的默认端口为50070，3.0.0及以上的默认端口为9870。用户使用的端口和HDFS版本不匹配导致连接端口失败。

步骤1 登录集群的主Master节点。

步骤2 执行 `su - omm` 命令，切换到omm用户。

步骤3 执行 `/opt/Bigdata/om-0.0.1/sbin/queryVersion.sh` 或者 `sh ${BIGDATA_HOME}/om-server/om/sbin/queryVersion.sh` 命令，查看集群中的HDFS版本号。根据版本号确认开源组件的端口号，查询开源组件的端口号可参考开源组件端口列表，获取对应版本的HDFS端口号。

步骤4 执行 `netstat -anp | grep ${port}` 命令，查看组件的默认端口号是否存在。如果不存在，说明用户修改了默认的端口号。请修改为默认端口，再重新连接HDFS。如果存在，请联系技术服务。

> **说明**：
> - ${port}：表示与组件版本相对应的组件默认端口号。
> - 如果用户修改了默认端口号，请使用修改后的端口号连接HDFS。不建议修改默认端口号。

----结束

## 13.37 执行 balance 常见问题定位方法

### 问题1：报没权限（Access denied）执行 balance

问题描述：执行start-balancer.sh，“hadoop-root-balancer-主机名.out”日志显示“Access denied for user test1. Superuser privilege is required”。

```
org.apache.hadoop.ipc.RemoteException(org.apache.hadoop.security.AccessControlException): Access denied for user test1. Superuser privilege is required
at org.apache.hadoop.hdfs.server.namenode.FSPermissionChecker.checkSuperuserPrivilege(FSPermissionChecker.java:122)
at org.apache.hadoop.hdfs.server.namenode.FSNamesystem.checkSuperuserPrivilege(FSNamesystem.java:5916)
```

执行balance需要使用管理员账户。

**解决方法**

- 安全版本：使用hdfs或者其他属于supergroup组的用户认证后，执行balance。
- 普通版本：执行HDFS的balance命令前，需要在客户端执行 `su - omm` 命令。

### 问题2：执行 balance 失败，/system/balancer.id 文件异常

问题描述：在HDFS客户端启动一个Balance进程，该进程被异常停止后，再次执行Balance操作，操作会失败。

```
org.apache.hadoop.ipc.RemoteException(org.apache.hadoop.protocol.RecoveryInProgressException): Failed to APPEND_FILE /system/balancer.id for DFSClient because lease recovery is in progress. Try again later.
```

问题根因：通常，HDFS执行Balance操作结束后，会自动释放“/system/balancer.id”文件，可再次正常执行Balance。

但在上述场景中，由于第一次的Balance操作是被异常停止的，所以第二次进行Balance操作时，“/system/balancer.id”文件仍然存在，则会触发append /system/balancer.id操作，进而导致Balance操作失败。

**解决方法**

方法1：等待硬租期超过1小时后，原有客户端释放租约，再执行第二次Balance操作。

方法2：删除HDFS中的“/system/balancer.id”文件，再执行下次Balance操作。

----结束

## 13.38 非 HDFS 数据残留导致数据分布不均衡

### 问题描述

数据出现不均衡，某磁盘过满而其他磁盘未写满。

HDFS DataNode数据存储目录配置为“/export/data1/dfs--/export/data12/dfs”，看到的现象是大量数据都是存储到了“/export/data1/dfs”，其他盘的数据比较均衡。

### 原因分析

磁盘为卸载重装，有一个目录在上次卸载时未卸载干净，即添加的磁盘，未格式化，残留历史垃圾数据。

### 处理步骤

手动清理未卸载干净的数据。

----结束

## 13.39 HDFS 客户端安装在数据节点导致数据分布不均衡

### 问题描述

HDFS的DataNode数据分布不均匀，在某节点上磁盘使用率很高，甚至达到100%，其他节点空闲很多。

### 原因分析

客户端安装在该节点，根据HDFS数据副本机制，第一个副本会存放在本地机器，最终导致节点磁盘被占满，而其他节点空闲很多。

### 处理步骤

步骤1 针对已有不平衡的数据，执行balance脚本均衡数据。

```shell
/opt/client/HDFS/hadoop/sbin/start-balancer.sh -threshold 10
```

其中“/opt/client”是实际的客户端安装目录。

步骤2 针对新写入数据，将客户端安装在没有安装DataNode的节点。

----结束

## 13.40 节点内 DataNode 磁盘使用率不均衡

### 问题描述

单个节点内DataNode的各磁盘使用率不均匀。

例如：

```
189-39-235-71:~ # df -h
Filesystem Size Used Avail Use% Mounted on
/dev/xvda 360G 92G 250G 28% /
/dev/xvdb 700G 900G 200G 78% /srv/BigData/hadoop/data1
/dev/xvdc 700G 900G 200G 78% /srv/BigData/hadoop/data2
/dev/xvdd 700G 900G 200G 78% /srv/BigData/hadoop/data3
/dev/xvde 700G 900G 200G 78% /srv/BigData/hadoop/data4
/dev/xvdf 10G 900G 890G 2% /srv/BigData/hadoop/data5
```

### 可能原因

- 部分磁盘故障，更换为新盘，因此新盘使用率低。
- 增加了磁盘个数，如原先4个数据盘，现扩容为5个数据盘。

### 原因分析

DataNode节点内写block磁盘时，有两种策略“轮询”和“优先写剩余磁盘空间多的磁盘”。

参数说明：dfs.datanode.fsdataset.volume.choosing.policy

可选值：

- org.apache.hadoop.hdfs.server.datanode.fsdataset.RoundRobinVolumeChoosingPolicy：轮询。
- org.apache.hadoop.hdfs.server.datanode.fsdataset.AvailableSpaceVolumeChoosingPolicy：优先写剩余空间多的磁盘。

### 处理步骤

步骤1 登录FusionInsight Manager。

登录集群Manager具体操作，请参考访问MRS集群Manager。

步骤2 选择“集群>服务>HDFS>配置>全部配置”。

步骤3 搜索“dfs.datanode.fsdataset.volume.choosing.policy”参数名称，并将参数值修改为“org.apache.hadoop.hdfs.server.datanode.fsdataset.AvailableSpaceVolumeChoosingPolicy”。

步骤4 保存并重启受影响的服务或实例。让DataNode根据磁盘剩余空间大小，优先选择磁盘剩余空间多的节点存储数据副本。

### 说明

- 针对新写入到本DataNode的数据会优先写磁盘剩余空间多的磁盘。
- 部分磁盘使用率较高，依赖业务逐渐删除在HDFS中的数据（老化数据）来逐渐降低。

----结束

## 13.41 MRS 集群上报 HDFS 磁盘空间不足告警但是实际磁盘空间未被占满

### 问题描述

1. MRS集群上报了“ALM-14001 HDFS磁盘空间使用率超过阈值”告警。

2. 通过客户端命令或者HDFS WebUI页面，查看磁盘空间使用率非常高，但是并未完全被占满。

### 原因分析

HDFS中用户可以自行配置DataNode预留磁盘空间百分比，配置参数为“dfs.datanode.du.reserved.percentage”，该参数用于指定DataNode所在磁盘的预留空间百分比，默认为10%。

当DataNode存储数据时，会根据此参数计算并保留一部分磁盘空间，不用于存储HDFS的数据块，以确保磁盘有足够的空闲空间供操作系统、其他应用或临时文件使用，或者预留升级时使用。

由于系统默认预留了10%的磁盘空间，因此当磁盘使用率达到90%的时候，集群会上报HDFS磁盘空间不足的告警。

### 处理步骤

步骤1 如果集群已上报告警，请参考对应告警的帮助文档进行处理，调整告警阈值为合理范围。

如果磁盘实际空间仍充足，告警触发阈值需要进行调整，参考ALM-14001 HDFS磁盘空间使用率超过阈值进行处理。

步骤2 登录HDFS客户端，参考以下命令，删除HDFS中无用的文件或目录。

1. 执行以下命令查看文件夹下的文件或子目录。

```shell
hdfs dfs -ls /文件夹名称
```

2. 执行以下命令查询HDFS文件目录大小。

```shell
hdfs dfs -du 待查看的目录路径
```

例如查询“/tmp”文件夹下的文件或子目录大小，执行后结果如下，表示“/tmp/hadoop-yarn”占用磁盘大小为622222017字节：

```
0 0 /tmp/.testHDFS
207407339 622222017 /tmp/hadoop-yarn
0 0 /tmp/hive
0 0 /tmp/hive-scratch
0 0 /tmp/logs
```

3. 执行以下命令删除已确认无用的HDFS文件。

例如可以删除过期日志、临时文件等，如MapReduce/YARN的历史日志、Spark作业临时输出等，通常可按时间清理30天前的文件。

开发测试产生的临时目录（如/user/test）、已下线业务的数据表等，与上层业务侧确认无用后也可以进行删除。

> **警告**：文件删除操作为高危操作，请务必确认删除的文件为无用的文件，避免造成数据丢失。

4. HDFS默认启用回收站，若空间紧急可手动清空。

```shell
# 查看当前用户回收站路径
hdfs dfs -ls /user/UserA/.Trash
# 清空回收站
hdfs dfs -rm -r /user/UserA/.Trash/*
```

步骤3 归档/迁移冷数据。

对不常访问但需保留的数据，建议迁移到低成本存储（如对象存储OBS），例如使用Distcp工具。

步骤4 扩容MRS集群。

在HDFS DataNode节点对应磁盘分区空间已使用到80%以上时，建议及时扩容MRS集群，新增DataNode节点组，请参考扩容MRS集群。

DataNode扩容完成后需进行数据均衡，可参考配置HDFS DataNode数据均衡进行操作。

数据均衡操作完成后，可执行 `hdfs dfsadmin -report` 命令，确认各DataNode节点的磁盘使用率均衡。

----结束

## 13.42 NameNode 节点存在 ALM-12027 主机 PID 使用率超过阈值告警

### 问题描述

3.1.2及之前的3.x版本集群，NameNode节点存在ALM-12027主机PID使用率超过阈值告警，节点Java进程可能出现“unable to create new native thread”报错。

### 原因分析

1. 使用以下命令统计节点进程的线程数并排序。

```shell
ps -efT | awk '{print $2}' | sort -n | uniq -c | sort -n
```

执行后结果如下：

```
64 15310
54533 2346
275 2983
504 32139
323 33641
113 38454
105 41630
174 43672
101 44918
66 55187
155 3153
76 7057
```

2. 查看启动线程数最多的进程，案例中进程2346为NameNode进程，启动了5.4万线程，且持续增长。

3. 多次打印对应进程的jstack日志，根据jstack日志信息发现，NameNode存在大量线程处于WAITING，且长期不释放。

```
Line 200: at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
Line 215: at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
Line 230: at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
Line 245: at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
Line 260: at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
Line 275: at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
"Thread-121224" #653415 daemon prio=5 os_prio=0 tid=0x00007fb25b753000 nid=0x50ea waiting on condition [0x00007fbl6a287000]
java.lang.Thread.State: WAITING (parking)
at sun.misc.Unsafe.park(Native Method)
- parking to wait for <0x000000073f5e8838> (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject)
at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
at java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject.await(AbstractQueuedSynchronizer.java:2045)
at java.util.concurrent.LinkedBlockingQueue.take(LinkedBlockingQueue.java:442)
at java.util.concurrent.ThreadPoolExecutor.getTask(ThreadPoolExecutor.java:1074)
at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1134)
at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
at java.lang.Thread.run(Thread.java:748)
Locked ownable synchronizers:
- None
```

结合以上问题分析如下：NameNode存在内置机制，根据WARN日志信息自动开启DEBUG日志，在环境中由于选择副本失败，导致一直启动Debug日志，不停地修改log4j，修改组件的log4j后进程会自动加载该配置文件，此时就会有新的线程自动产生，长时间后就会触发该告警。

出现这种情况时，将内置机制关闭，禁止自动修改日志级别即可恢复。

### 处理步骤

步骤1 分别登录到集群主备NameNode节点，执行以下命令备份脚本。

```shell
cd $BIGDATA_HOME/FusionInsight_Current/*_*_NameNode/install/hadoop/sbin
cp hdfs-namenode-period-check.sh /tmp
```

步骤2 在主备NameNode节点编辑hdfs-namenode-period-check.sh文件。

```shell
vi hdfs-namenode-period-check.sh
```

在main方法中将“checkBlockplacementLog”注释掉，例如：

```shell
main()
{
  Log $INFO "start period check"
  checkHaState
  checkDefaultFS
  checkAutoBalancer
  checkFsMonitorDirectory
  checkAutoMover
  checkAutoDatamove
  checkAutoNodeLabelrefresh
  checkJournalNodeSync
  checkCheckpoint
  checkCleanAcls
  checkSssdMonitor
  checkOperationCollecter
  checkMapReduceDistributedCache
  #checkBlockplacementLog
  checkAutoDiskBalancer
}
```

步骤3 保存文件后，登录Manager，选择“集群>服务>HDFS>实例”，勾选所有NameNode实例，选择“更多>重启实例”。

----结束

## 13.43 集群出现 ALM-14012 Journalnode 数据不同步告警

### 问题描述

MRS集群出现ALM-14012 Journalnode数据不同步告警。

### 原因分析

1. 登录告警节点，查找日志路径“/var/log/Bigdata/hdfs/nn”下Journalnode实例的startDetail.log日志信息，发现Journalnode实例停止过。

2. 分别查看告警节点和其他JournalNode节点的“/srv/BigData/journalnode/hacluster/current”路径下最新的edits日志文件，发现告警节点与其他节点存在不同步的情况。

### 处理步骤

步骤1 登录FusionInsight Manager，选择“集群>服务>HDFS>实例”，勾选告警发生节点对应的Journalnode实例，选择“更多>停止实例”。

步骤2 登录告警节点，将“/srv/BigData/journalnode/hacluster/current”目录下的所有文件移动到其他新建目录下（例如“/opt/test”），保持该目录下清空状态。

步骤3 登录FusionInsight Manager，选择“集群>服务>HDFS>实例”，勾选停止的Journalnode实例，单击“启动实例”。

步骤4 等待一段时间后，观察告警是否恢复。

----结束
