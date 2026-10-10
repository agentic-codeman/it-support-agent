

## 20.1 运行 Spark 应用时修改 MapReduce 分片值报错

### 问题现象

用户需要通过修改一个split最大值来实现多个mapper，从而达到提速的目的，但是执行set命令修改Hive的配置时报错。

0: jdbc:hive2://192.168.1.18:21066/> set mapred.max.split.size=1000000;
Error: Error while processing statement: Cannot modify mapred.max.split.size at runtime. It is not in list of params that are allowed to be modified at runtime( state=42000,code=1)

### 原因分析

在安全模式下配置白名单启停参数hive.security.whitelist.switch时，需要运行的参数必须在hive.security.authorization.sqlstd.confwhitelist中配置。

hive.security.temporary.function.need.admin

hive.security.transform.disallow

truefalse

hive.security.whitelist.switch

ONOFF

hive.server2.enable.doAs

truefalse

默认白名单中没有包含mapred.max.split.size参数，所以运行的时候会提示不允许。

### 处理步骤

步骤1 进入Hive服务配置页面：

MRS 3.x之前版本，单击集群名称，登录集群详情页面，选择“组件管理 > Hive> 服务配置”，单击“基础配置”下拉菜单，选择“全部配置”。

说明

如果集群详情页面没有“组件管理”页签，请先完成IAM用户同步（在集群详情页的“概览”页签，单击“IAM用户同步”右侧的“同步”进行IAM用户同步）。

MRS 3.x及后续版本，登录FusionInsight Manager，然后选择“集群 > 服务 >Hive > 配置 > 全部配置”。

步骤2 搜索hive.security.authorization.sqlstd.confwhitelist.append，把mapred.max.split.size加进hive.security.authorization.sqlstd.confwhitelist.append中，详细信息可参考从零开始使用Hive。

步骤3 修改完成后，保存配置，重启Hive组件。

步骤4 重新在Hive Beeline命令行中执行set mapred.max.split.size=1000000;。

----结束

## 20.2 提交Spark任务时提示参数格式错误

### 问题现象

用户在使用Spark组件时，提交集群任务运行失败，提示参数格式错误。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/c64d1fad0d9bd7b0661a276e9b723b5f7369cf1117d6c754dcd586f4ee4d0af9.jpg)

### 原因分析

● 执行的命令包含了非法字符。

● 上传的jar包属主属组异常。

### 处理步骤

步骤1 检查用户执行命令./bin/spark-submit --class cn.interf.Test --master yarn-client客户端安装目录/Spark/spark1-1.0-SNAPSHOT.jar;，排查是否引入了非法字符。

步骤2 如果是，修改非法字符，重新执行命令。

步骤3 重新执行命令后，发生其他错误，查看该jar包的属主属组信息，发现全为root。

步骤4 修改jar包的属主属组为omm:wheel，重新执行成功。

----结束

## 20.3 节点磁盘容量不足导致 Spark 服务不可用

### 问题现象

用户创建的集群显示磁盘容量不足，产生告警导致Spark、Hive和Yarn服务不可用。

### 原因分析

由于集群磁盘容量不足，会影响到HDFS的数据写入，HDFS磁盘空间使用率超过阈值，因此导致HDFS服务异常。

HDFS服务异常则会导致Spark、Hive和Yarn服务不可用。

根据该集群出现磁盘容量不足产生Spark、Hive和Yarn服务不可用的报警，扩容磁盘后不再告警，可以判断是磁盘容量不足引起HDFS功能故障所导致。

### 处理步骤

针对磁盘容量不足产生的告警处理步骤，请参考ALM-12017 磁盘容量不足。

### 参考信息

HDFS磁盘空间使用率超过阈值处理步骤，请参考ALM-14001 HDFS磁盘空间使用率超过阈值。
----结束

## 20.4 引入 jar 包不正确导致 Spark 任务无法运行

### 问题现象

执行Spark任务，任务无法运行。

### 原因分析

执行Spark任务时，引入的jar包不正确，导致Spark任务运行失败。

### 处理步骤

步骤1 登录任意Master节点。

步骤2 执行cd /opt/Bigdata/MRS_*/install/FusionInsight-Spark-*/spark/examples/jars命令， 查看样例程序的jar包。

说明

jar包名最多为1023字符，不能包含;|&>,<'$特殊字符，且不可为空或全空格。

步骤3 执行程序可存储于HDFS或者OBS中，不同的文件系统对应的路径存在差异。

OBS存储路径：以“obs://”开头。示例：obs://wordcount/program/hadoop-mapreduce-examples-2.7.x.jar

HDFS存储路径：以“/user”开头。Spark Script需要以“.sql”结尾，MapReduce和Spark需要以“.jar”结尾。sql、jar不区分大小写。

----结束

## 20.5 Spark 任务由于内存不足或未添加 Jar 包导致异常

### 问题现象

Spark提交作业内存不足或提交作业时未添加Jar包导致任务长时间处于pending状态或者运行中内存溢出。

使用Spark提交作业后，长期卡住不动。反复运行作业后报错，内容如下：

Exception in thread "main" org.apache.spark.SparkException: Job aborted due to stage failure: Aborting TaskSet 3.0 because task 0 (partition 0) cannot run anywhere due to node and executor blacklist. Blacklisting behavior can be configured via spark.blacklist.*.

### 原因分析

内存不足或提交作业时未添加Jar包，导致Spark提交的作业任务长时间处于pending状态。

### 处理步骤

步骤1 检查提交作业时是否添加Jar包。

● 是，执行步骤2。

● 否，添加Jar包，执行作业正常，操作结束。如果执行作业任务长时间处于pending状态，执行步骤2。

步骤2 在MRS控制台页面的现有集群中，选择集群名称，在“节点信息”页面，查看当前集群的节点规格。

步骤3 提高NodeManager进程所持有的集群资源。

MRS Manager界面操作：

1. 登录MRS Manager页面，选择“服务管理 > Yarn > 服务配置”。

2. 在“参数类别”中选择“全部配置”，然后在搜索框中搜索yarn.nodemanager.resource.memory-mb，查看该参数值。建议配置成节点物理内存总量的75%-90%。

FusionInsight Manager界面操作：

1. 选择“集群 > 服务 > Yarn”。

2. 单击“配置”，选择“全部配置”。然后在搜索框中搜索yarn.nodemanager.resource.memory-mb，查看该参数值。建议配置成节点物理内存总量的75%-90%。

步骤4 修改Spark的服务配置。

MRS Manager界面操作：

1. 登录MRS Manager页面，选择“服务管理”>“Spark” >“服务配置”。

2. 在“参数类别”中选择“全部配置”，然后在搜索框中搜索

spark.driver.memory和spark.executor.memory

根据作业的需要调大或者调小该值，具体以提交的Spark作业的复杂度和内存需要为参考（一般调大）。

FusionInsight Manager界面操作：

1. 选择“集群 > 服务 > Spark”。

2. 单击“配置”，选择“全部配置”。然后在搜索框中搜索spark.driver.memory和spark.executor.memory，根据作业的需要调大或者调小该值，具体以提交的Spark作业的复杂度和内存需要为参考（一般调大）。

说明

● 如果使用到SparkJDBC作业，搜索并修改SPARK_EXECUTOR_MEMORY和

SPARK_DRIVER_MEMORY两个参数取值，具体以提交的Spark作业的复杂度和内存需要为参考（一般调大）。

● 如果对核数有要求，可以搜索并修改spark.driver.cores和spark.executor.cores的核数取值。

步骤5 Spark依赖内存做计算，如果以上还是不能满足任务的提交需要，建议扩容集群。

----结束

## 20.6 提交 Spark 任务时报错“ClassNotFoundException”

### 问题现象

运行Spark任务报找不到指定的类“ClassNotFoundException”。

详细报错内容如下：

Exception encountered | org.apache.spark.internal.Logging$class.logError(Logging.scala:91) org.apache.hadoop.hbase.DoNotRetryIOException: java.lang.ClassNotFoundException: org.apache.phoenix.filter.SingleCQKeyValueComparisonFilter

### 原因分析

用户配置的默认路径不正确。

### 处理步骤

步骤1 登录任意Master节点。

步骤2 修改Spark客户端目录下的配置文件。

执行vim 客户端安装目录/Spark/spark/conf/spark-defaults.conf命令，打开spark-defaults.conf文件，设置“spark.executor.extraClassPath” 取值为“${PWD}/*”。

步骤3 重新尝试提交任务。

----结束

## 20.7 提交 Spark 任务时 Driver 端提示运行内存超限

### 问题现象

运行内存超限导致提交Spark任务失败。

### 原因分析

在Driver日志中直接打印申请的executor memory超过集群限制。
... INFO Client: Verifying our application has not requested more than the maximum memory capability of
the cluster (6144 MB per container)
... ERROR SparkContext: Error initializing SparkContext.
java.lang.IllegalArgumentException: Required executor memory (10240+1024 MB) is above the max
threshold (6144 MB) of this cluster!

Spark任务提交至Yarn上面，运行task的executor使用的资源受yarn的管理。从报错信息可看出，用户申请启动executor时，指定10G的内存，超出了Yarn设置的每个container的最大内存的限制，导致任务无法启动。

### 处理步骤

修改Yarn的配置，提高对container的限制。如可通过调整

“yarn.scheduler.maximum-allocation-mb”参数的大小，可控制启动的executor的资源，修改之后要重启Yarn服务。

MRS Manager界面操作：

步骤1 登录MRS Manager页面。

步骤2 选择“服务管理 > Yarn > 服务配置”将“参数类别”修改为“全部配置”。

步骤3 在“搜索”栏输入“yarn.scheduler.maximum-allocation-mb”修改参数并保存重启服务。如下图所示：

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/2b8192de733f1c3c232ca0b718c1892b44a6aebe5de452ef178e97bf97b016c0.jpg)

图 20-1 修改 Yarn 服务参数

----结束

FusionInsight Manager界面操作：

步骤1 登录FusionInsight Manager页面。

步骤2 选择“集群 > 服务 > Yarn”，单击“配置”，选择“全部配置”。

步骤3 在“搜索”栏输入“yarn.scheduler.maximum-allocation-mb”修改参数并保存重启服务。

----结束

## 20.8 Yarn-cluster 模式下提交 Spark 任务报“Can't getthe Kerberos realm”异常

### 问题现象

认证异常导致提交Spark任务失败，报“Can't get the Kerberos realm”异常。

### 原因分析

1. 在Driver端打印异常找不到连接HDFS的Token信息，报错如下：16/03/22 20:37:10 WARN Client: Exception encountered while connecting to the server :org.apache.hadoop.ipc.RemoteException(org.apache.hadoop.security.token.SecretManager$InvalidToken): token (HDFS_DELEGATION_TOKEN token 192 for admin) can't be found in cache16/03/22 20:37:10 WARN Client: Failed to cleanup staging dir .sparkStaging/application_1458558192236_0003

org.apache.hadoop.ipc.RemoteException(org.apache.hadoop.security.token.SecretManager $InvalidToken): token (HDFS_DELEGATION_TOKEN token 192 for admin) can't be found in cache

2. 在Yarn原生页面显示ApplicationMaster启动两次均失败，任务退出。

图 20-2 ApplicationMaster 启动失败

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/db40c55d60735a0034d2475fbe7d7af1445357058384b8a41a43bf2e3cc8a6a3.jpg)

3. 查看ApplicationMaster日志看到如下异常信息：

Exception in thread "main" java.lang.ExceptionInInitializerError

Caused by: org.apache.spark.SparkException: Unable to load YARN support

Caused by: java.lang.IllegalArgumentException: Can't get Kerberos realm

Caused by: java.lang.reflect.InvocationTargetException

Caused by: KrbException: Cannot locate default realm

Caused by: KrbException: Generic error (description in e-text) (60) - Unable to locate Kerberos realm org.apache.hadoop.hive.metastore.MetaStoreUtils.newInstance(MetaStoreUtils.java:1410)

Caused by: javax.jdo.JDOFatalInternalException: Unexpected exception caught.

NestedThrowables:java.lang.reflect.InvocationTargetException

... 110 more

4. 执行./spark-submit --class yourclassname --master yarn-cluster / 4. 执行./spark-submit --class yourclassname --master yarn-cluster /

任务以yarn-cluster模式提交任务，Driver端会在集群中启动，由于加载的是客户端的spark.driver.extraJavaOptions，在集群节点上对应路径下找不到对应的kdc.conf文件，无法获取kerberos认证所需信息，导致ApplicationMaster启动失败。

### 处理步骤

在客户端提交任务时，在命令行中配置自定义的spark.driver.extraJavaOptions参数这样任务运行时就不会自动加载客户端路径下“spark-defaults.conf”中的spark.driver.extraJavaOptions；或者在启动Spark任务时，通过“--conf”来指定Driver的配置，如下（此处spark.driver.extraJavaOptions“=”号后面的引号部分不能缺少）。

./spark-submit -class yourclassname --master yarn-cluster --conf spark.driver.extraJavaOptions="

-Dlog4j.configuration=file:/opt/client/Spark/spark/conf/log4j.properties - Djetty.version=x.y.z -Dzookeeper.server.principal=zookeeper/ hadoop.794bbab6_9505_44cc_8515_b4eddc84e6c1.com - Djava.security.krb5.conf=/opt/client/KrbClient/kerberos/var/krb5kdc/ krb5.conf -Djava.security.auth.login.config=/opt/client/Spark/spark/conf/ jaas.conf -Dorg.xerial.snappy.tempdir=/opt/client/Spark/tmp - Dcarbon.properties.filepath=/opt/client/Spark/spark/conf/ carbon.properties" ../yourdependencyjars
----结束

## 20.9 JDK 版本不匹配导致启动 spark-sql 和 spark-shell 失败

### 问题现象

JDK版本不匹配导致客户端启动spark-sql、spark-shell失败。

### 原因分析

1. 在Driver端打印异常如下：Exception Occurs: BadPadding 16/02/22 14:25:38 ERROR Schema: Failed initialising database. Unableto open a test connection to the given database. JDBC url = jdbc:postgresql://ip:port/sparkhivemeta,username = spark. Terminating connection pool (set lazyInit to true if you expect to start yourdatabase after your app).

2. SparkSQL任务使用时，需要访问DBService以获取元数据信息，在客户端需要解密密文来访问，在使用过程中，用户没有按照流程操作，没有执行配置环境变量操作，且在其客户端环境变量中存在默认的JDK版本，导致在执行解密过程中调用的解密程序执行解密异常，导致用户被锁。

### 解决办法

步骤1 使用which java命令查看默认的JAVA命令是否是客户端的JAVA。

步骤2 如果不是，请按正常的客户端执行流程。

source ${client path}/bigdata_env

kinit 用户名，然后输入用户名对应的密码，启动任务即可。

----结束

## 20.10 Yarn-client 模式提交 Spark 任务时ApplicationMaster 尝试启动两次失败

### 问题现象

Yarn-client模式提交任务AppMaster尝试启动两次失败。

### 原因分析

1. Driver端异常:16/05/11 18:10:56 INFO Client:client token: N/Adiagnostics: Application application_1462441251516_0024 failed 2 times due to AM Container forappattempt_1462441251516_0024_000002 exited with exitCode: 10For more detailed output, check the application tracking page:https://hdnode5:26001/cluster/app/application_1462441251516_0024 Then click on links to logs of each attempt.Diagnostics: Exception from container-launch.Container id: container_1462441251516_0024_02_000001

2. 在ApplicationMaster日志中，异常如下:2016-05-12 10:21:23,715 | ERROR | [main] | Failed to connect to driver at 192.168.30.57:23867,retrying ... | org.apache.spark.Logging$class.logError(Logging.scala:75)2016-05-12 10:21:24,817 | ERROR | [main] | Failed to connect to driver at 192.168.30.57:23867,retrying ... | org.apache.spark.Logging$class.logError(Logging.scala:75)2016-05-12 10:21:24,918 | ERROR | [main] | Uncaught exception: | org.apache.spark.Logging$class.logError(Logging.scala:96)org.apache.spark.SparkException: Failed to connect to driver!at org.apache.spark.deploy.yarn.ApplicationMaster.waitForSparkDriver(ApplicationMaster.scala:426)at org.apache.spark.deploy.yarn.ApplicationMaster.runExecutorLauncher(ApplicationMaster.scala:292)2016-05-12 10:21:24,925 | INFO | [Thread-1] | Unregistering ApplicationMaster with FAILED (diagmessage: Uncaught exception: org.apache.spark.SparkException: Failed to connect to driver!) |org.apache.spark.Logging$class.logInfo(Logging.scala:59)

Spark-client模式任务Driver运行在客户端节点上(通常是集群外的某个节点)，启动时先在集群中启动AppMaster进程，进程启动后要向Driver进程注册信息，注册成功后，任务才能继续。从AppMaster日志中可以看出，无法连接至Driver，所以任务失败。

### 解决办法

步骤1 请检查Driver进程所在的IP是否可以ping通。

步骤2 启动一个Spark PI任务，会有类似如下打印信息。16/05/11 18:07:20 INFO Remoting: Remoting started; listening on addresses :[akka.tcp://sparkDriver@192.168.1.100:23662]16/05/11 18:07:20 INFO Utils: Successfully started service 'sparkDriver' on port 23662.

步骤3 在该节点，也就是步骤2中示例的192.168.1.100上执行netstat - anp | grep 23662看下此端口是否打开，如下打印信息表明，相关端口是打开的。tcp 0 0 ip:port LISTEN 107274/javatcp 0 0 ip:port ip:port ESTABLISHED 107274/java

步骤4 在AppMaster启动的节点执行telnet 192.168.1.100 23662看下是否可以连通该端口，请使用root用户和omm用户都执行一遍。 如果出现Escape character is '^]'类似打印则说明可以连通，如果出现connection refused则表示失败，无法连接到相关端口。

如果相关端口打开，但是从别的节点无法连通到该端口，则需要排查下相关网络配置。

### 说明

23662这个端口每次都是随机的，所以要根据自己启动任务打开的端口来测试。

----结束

## 20.11 提交 Spark 任务时连接 ResourceManager 异常问题现象

连接ResourceManager异常，导致Spark任务提交失败。

### 原因分析

1. 在Driver端打印异常如下，打印连接两个ResourceManager主备节点的26004端口均被拒绝：15/08/19 18:36:16 INFO RetryInvocationHandler: Exception while invoking getClusterMetrics of classApplicationClientProtocolPBClientImpl over 33 after 1 fail over attempts. Trying to fail over aftersleeping for 17448ms.java.net.ConnectException: Call From ip0 to ip1:26004 failed on connection exception:java.net.ConnectException: Connection refused.INFO RetryInvocationHandler: Exception while invoking getClusterMetrics of classApplicationClientProtocolPBClientImpl over 32 after 2 fail over attempts. Trying to fail over aftersleeping for 16233ms.java.net.ConnectException: Call From ip0 to ip2:26004 failed on connection exception:java.net.ConnectException: Connection refused;

2. 在MRS Manager页面查看ResourceManager此时是否功能正常，如果Yarn服务状态故障或某个Yarn服务的实例出现未知之类的异常说明此时集群的ResourceManager可能异常。

3. 排查使用的客户端是否是集群最新的客户端。排查集群是否做过实例ResourceManager迁移相关操作（先卸载某个ResourceManager实例，然后在其他节点添加）。

4. 在MRS Manager页面查看审计日志，是否有相关操作的记录。使用ping命令，查看IP是否可连通。

### 解决办法

● 如果ResourceManager出现异常，可参考相关告警章节查看解决方法。

● 如果客户端不是最新，请重新下载安装客户端。

● 若使用ping命令查看IP不通，需要协调网络管理相关人员协助排查网络。

若集群开启高可用，尝试将Yarn参数“yarn.client.failover-sleep-base-ms”调小。
----结束

## 20.12 通过 DataArts Studio 调度 Spark 作业失败

### 问题现象

DataArts Studio作业调度失败，显示读取“/thriftserver/active_thriftserver”路径下的数据失败。

报错信息为：

Can not get JDBC Connection, due to KeeperErrorCode = NoNode for /thriftserver/active_thriftserver。

### 原因分析

DataArts Studio提交Spark作业时调用Spark的JDBC方式，而Spark会启动一个名为thriftserver的进程以供客户端提供JDBC连接，JDBCServer在启动时会在ZooKeeper的“/thriftserver”目录下创建子目录“active_thriftserver”，并且注册相关连接信息。如果读不到该连接信息就会JDBC连接异常。

### 处理步骤

检查ZooKeeper下面是否有目标目录和注册的信息

步骤1 以root用户登录任意一个Master节点并初始化环境变量。

source /opt/client/bigdata_env

步骤2 执行zkCli.sh -server 'ZooKeeper实例IP地址:ZooKeeper连接端口'命令登录ZooKeeper。

ZooKeeper连接端口通常为2181，可通过查看ZooKeeper服务配置参数“clientPort”获取。

步骤3 执行ls /thriftserver查看是否有“active_thriftserver”目录。

● 如果有active_thriftserver目录，执行get /thriftserver/active_thriftserver查看该目录下是否有注册的配置信息。

– 如果有注册的配置信息，联系华为云支持人员处理。

\- 如果没有注册的配置信息，执行步骤4

● 如果没有active_thriftserver目录，执行步骤4。

步骤4 登录Manager界面，查看Spark的JDBCServer实例的主备状态是否未知。

● 是，执行步骤5。

● 否，联系运维人员处理。

步骤5 重启两个JDBCServer实例，查看主备实例状态恢复正常且zk下面有了目标目录和数据，作业即可恢复正常。若实例状态没有恢复请联系华为云支持人员处理。

----结束

## 20.13 通过 API 提交 Spark 作业后作业状态为 error

### 问题现象

使用API提交Spark作业后，作业状态显示为error。

修改“/opt/client/Spark/spark/conf/log4j.properties”中的日志级别，使用API V1.1接口作业提交后，状态显示为error。

### 原因分析

executor会监控作业日志回显，确定作业执行结果，改为error后，检测不到输出结果，因此过期后判断作业状态为异常。

### 处理步骤

将“/opt/client/Spark/spark/conf/log4j.properties”中的日志级别修改为info。

### 建议与总结

建议使用V2接口提交作业接口。
----结束

## 20.14 MRS 集群反复上报 JobHistory 进程堆内存使用超出阈值告警

### 问题现象

集群出现告警“ALM-43006 JobHistory进程堆内存使用超出阈值”并且按照指导处理以后，运行一段时间又会出现同样的告警。

### 原因分析

可能存在JobHistory内存泄露问题，需要安装相应的补丁修复。

### 处理步骤

● 适当调大JobHistory进程堆内存。

● 如果已经调大堆内存，可以通过重启JobHistory实例规避。
----结束

## 20.15 在 spark-beeline 中创建或删除表失败

### 问题现象

在spark-beeline频繁创建和删除大量用户的场景下，个别用户偶现创建/删除表失败。

创建表过程：

CREATE TABLE wlg_test001 (start_time STRING,value INT);

报错:

Error: org.apache.spark.sql.AnalysisException:
org.apache.hadoop.hive.ql.metadata.HiveException: MetaException(message:Failed to grant permission on
HDFSjava.lang.reflect.UndeclaredThrowableException); (state=,code=0)

### 原因分析

1. 查看MetaStore日志。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/8190f4271de0c52921dff4122c6bd652abe2156c97572e511d1685b801c5f616.jpg)

2. 查看HDFS日志。

2020-08-31 14:41:38,568 | INF0 | Socket Reader #1 for port 9820 | Authorization successful for hive/hadoop.036a3461 d09b 494f a32 c af273307d943.com@036A3461 D09B 494F A32C AF273307D943.COM (auth:KERBER0S) for protocol=interface org.apache.hadoop.hdfs.protocol .ČlientProtocol | ServiceAuthorizationManager.java:135
2020-08-31 14:41:38,586 | INF0 | IPC Server handler 7 on 9820 | IPC Server handler 7 on 9820, call Call#3822197 Retry#0 org.apach e.hadoop.hdfs.protocol.ClientProtocol.checkAccess from 192.168.1.66:50540: org.apache.hadoop.security.AccessControlException: Perm ission denied: user=hive, access=READ, inode="/user/hive/warehouse/hive_csb_csb_3f8_x48ssrbt_5lbi2edu.db/wlg_test001":spark:hive:d rwx-.- --| Server.java:2523
2020-08-31 14:41:38,852 | INF0 Socket Reader #1 for port 9820 |Auth successful for hwstaff_pub_0tw00ru6@036A3461 D09B_494F_A32 C_AF273307D943.COM (auth:TOKEN Server.java:1700
2020-08-31 14:41:38,911 | INF0 Socket Reader #1 for port 9820 | Authorization successful for hwstaff_pub_0tw00ru6@036A3461_D09B

3. 权限对比（test001为异常用户创建表，test002为正常用户创建表）。

drwx- spark hive 0 2020-08-31 14:41 /user/hive/warehouse/hive_csb_csb_3f8_x48ssrbt_5lbi2edu.db/wl g test001
drwxrwx---+ spark hive 0 2020-08-31 15:07 /user/hive/warehouse/hive_csb_csb_3f8_x48ssrbt_5lbi2edu.db/wl g_test002

4. drop表时报类似下面的错。

dataplan_modela_csbch2;
Error: Error while compiling statement: FAILED:
SemanticException Unable to fetch table dataplan_modela_csbch2.
java.security.AccessControlException: Permission denied: user=CSB_csb_3f8_x48ssrbt, access=READ,
inode="/user/hive/warehouse/hive_csb_csb_3f8_x48ssrbt_5lbi2edu.db/
dataplan_modela_csbch2":spark:hive:drwx--

5. 根因分析。

创建集群时创建的默认用户使用了相同的uid，造成用户错乱。在大量创建用户的场景下，触发了该问题，导致在创建表时偶现Hive用户没有权限。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/9f4d0cf60652ec162e0587e9866f272c5765d3c45ed57d4c08f5691827ad3a9f.jpg)

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/7cc00c97a2850d7ec98f9142164a414e0807f4459b899f714d8d50e8fd1dc90d.jpg)

### 处理步骤

重启集群sssd进程。

以root用户执行service sssd restart命令重启sssd服务，执行ps -ef | grep sssd命令，查看sssd进程是否正常。

正常状态为存在/usr/sbin/sssd进程和三个子进程/usr/libexec/sssd/sssd_be、/usr/libexec/sssd/sssd_nss、/usr/libexec/sssd/sssd_pam。
----结束

## 20.16 集群外节点提交 Spark 作业时报错无法连接 Driver

### 问题现象

集群外节点和集群各个节点网络已经互通，在集群外节点使用client模式提交Spark任务到Yarn上，任务失败，报错信息为无法连接Driver。

### 原因分析

使用client模式提交Spark任务的时候，Spark的driver进程是在客户端这边，而后面的executor都需要和Driver进行交互来运行作业。

如果NodeManager连不上客户端所在的节点，就会报错：

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/515da220b4b631d20ba41156b43a4a40e5fd7473bd66f33bc31dd5eca4dea066.jpg)

### 处理步骤

在客户端的Spark配置中指定Driver的IP地址：

“<客户端安装位置>/Spark/spark/conf/spark-defaults.conf”中添加参数

“spark.driver.host=driverIP”，重新运行Spark任务即可。

### 建议与总结

建议通过cluster模式提交作业。
----结束

## 20.17 运行 Spark 任务发现大量 shufle 结果丢失

### 问题现象

Spark任务运行失败，查看任务日志发现大量打印shufle文件丢失。

### 原因分析

Spark运行的时候会将临时产生的shufle文件放在executor的临时目录中，方便后面获取。

而当某个executor异常退出时，NodeManager会把这个executor所在的container临时目录删除，随后其他executor再来申请这个executor的shufle结果就会报文件找不到。

因此，遇到这样的问题需要确认是否executor异常退出，可以根据spark任务页面的executors便签页查看是否有dead状态的executor，查看各个dead状态的executor日志，确认异常退出的原因（其中可能有部分executor退出原因就是因为shufle文件找不到，需要找到最早异常退出的executor）。

常见的异常退出：

● executor发生OOM

● executor运行时出现多个task任务失败

● executor所在节点被清理

### 处理步骤

根据executor异常退出的实际原因调整或者修改任务参数或代码，重新运行Spark任务即可。
----结束

## 20.18 JDBCServer 长时间运行导致磁盘空间不足

### 用户问题

连接Spark的JDBCServer服务提交spark-sql任务到yarn集群上，在运行一段时间以后会出现Core节点的数据盘被占满的情况。

### 问题现象

客户连接Spark的JDBCServer服务提交spark-sql任务到yarn集群上，在运行一段时间以后会出现Core节点的数据盘被占满的情况。

后台查看磁盘使用情况，主要是JDBCServer服务的APP临时文件（shufle生成的文件）太多，并且没有进行清理占用了大量内存。

### 原因分析

查询Core节点有大量文件的目录，发现大部分都是类似“blockmgr-033707b6-fbbb-45b4-8e3a-128c9bcfa4bf”的目录，里面存放了计算过程中产生的shufle临时文件。

因为JDBCServer启动了Spark的动态资源分配功能，已经将shufle托管给

NodeManager，NodeManager只会按照APP的运行周期来管理这些文件，并不会关注单个executor所在的container是否存在。因此，只有在APP结束的时候才会清理这些临时文件。任务运行时间较长时导致临时文件过多占用了大量磁盘空间。

### 处理步骤

MRS 3.2.1-LTS之前的版本：

启动一个定时任务来清理超过一定时间的shufle文件，例如每个整点清理超过6个小时的文件：

步骤1 创建脚本“clean_appcache.sh”，若存在多个数据盘，请根据实际情况修改BASE_LOC中data1的值。

● 安全集群

!/bin/bash

BASE_LOC=/srv/BigData/data1/nm/localdir/usercache/spark2x/appcache/application_*/blockmgr* find $BASE_LOC/ -mmin +360 -exec rmdir {} \;
find $BASE_LOC/ -mmin +360 -exec rm {} \;

● 普通集群

!/bin/bash

BASE_LOC=/srv/BigData/data1/nm/localdir/usercache/omm/appcache/application_*/blockmgr* find $BASE_LOC/ -mmin +360 -exec rmdir {} \;
find $BASE_LOC/ -mmin +360 -exec rm {} \;

### 注意

● 在执行前，需要检查待执行的脚本与文档是否一致，避免人工失误导致其他路径数据被误删。

● 脚本执行前需确认BASE_LOC变量对应的路径在集群中是否存在，不存在需修改为对应的路径。

步骤2 修改脚本权限。

chmod 755 clean_appcache.sh

dos2unix clean_appcache.sh

步骤3 增加一个定时任务来启动清理脚本，脚本路径请根据实际脚本存放位置修改。

查看定时任务：crontab -l

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/a2bfda83d96a9a55ad969b3395c801d63fe5a978c29b216c07e0a01e7e64b7c5.jpg)
----结束

## 20.19 通过 spark-shell 加载数据到 Hive 表失败

### 用户问题

使用spark-shell命令执行SQL或者spark-submit提交的Spark任务里面有SQL的load命令，并且原数据和目标表存储位置不是同一套文件系统，上述两种方式MapReduce任务启动时会报错。

### 原因分析

当使用load导入数据到Hive表的时候，属于需要跨文件系统的情况（例如原数据在HDFS上，而Hive表数据存放在OBS上），并且文件长度大于阈值（默认32 MB），则会触发使用distcp的MapReduce任务来执行数据迁移操作。这个MapReduce任务配置直接从Spark任务配置里面提取，但是Spark任务的
net.topology.node.switch.mapping.impl配置项不是hadoop的默认值，需要使用Spark的jar包，因此MapReduce会报类找不到。

### 处理步骤

方案一：

如果文件较小，则可以将默认长度设置得大于文件最大长度，例如最大的文件是95MB，则设置：

hive.exec.copyfile.maxsize=104857600

方案二：

如果确实文件较大，需要使用distcp任务来提高数据迁移效率，则可以在Spark任务启动的时候增加设置参数：

--conf spark.hadoop.net.topology.node.switch.mapping.impl=org.apache.hadoop.net.ScriptBasedMapping
----结束

## 20.20 Spark 任务提交失败

### 问题现象

● Spark提交任务直接提示无法提交任务。

● Spark提示无法获取到yarn的相关jar包。

● 提示多次提交一个文件。

### 原因分析

● 问题1：

最常见的无法提交任务原因是认证失败，

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/068548b6b7aac079610de5e80c4ff2728e8a3e6c438360a86da51f6411956cdf.jpg)

还有可能是参数设置不正确。

● 问题2：

集群默认会把分析节点的hadoop相关jar包添加到任务的classpath中，如果提示yarn的包找不到，一般都是因为hadoop的相关配置没有设置。

● 问题3：

常见的场景是使用--files上传了user.keytab，然后使用--keytab又指定了同一个文件，导致一个文件多次被上传。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/9c76ffcaa7f6e4c1126611b04e1821889eb2f7112d183dcb4becefffc8206c89.jpg)

### 处理步骤

● 问题1：

重新kinit一个用户并修改相应的配置参数。

● 问题2：

查看hadoop相关的配置项是否正确，查看spark的conf目录下的core-site.xml，hdfs-site.xml，yarn-site.xml，mapred-site.xml等配置文件是否存在问题。

● 问题3：

重新复制一个user.keytab，例如：

cp user.keytab user2.keytab

spark-submit --master yarn --files user.keytab --keytab user2.keytab ...
----结束

## 20.21 Spark 任务运行失败

### 问题现象

● 报错显示executor出现OOM。

● 失败的task信息显示失败原因是lost task xxx。

### 原因分析

### 问题1：一般出现executor OOM，都是因为数据量过大，也有可能是因为同一个executor上面同时运行的task太多。

### 问题2：有些task运行失败会报上述错误。当看到这个报错的时候，需要确认的是丢失的这个task在哪个节点上面运行，一般的情况是这个丢失的task异常退出导致的。

### 处理步骤

● 问题1：

对于数据量过大，需要调整executor的内存大小的，使用--executor-memory指定内存大小；

– 对于同时运行的task太多，主要看--executor-cores设置的vcore数量。

● 问题2：

需要在相应的task的日志里面查找异常原因。如果有OOM的情况，请参照问题1。
----结束

## 20.22 JDBCServer 连接失败

### 问题现象

● 提示ha-cluster不识别（unknownHost或者必须加上端口）。

● 提示连接JDBCServer失败。

### 原因分析

### 问题1：使用spark-beeline命令连接JDBCServer，因为MRS\_3.0以前的JDBCServer是HA模式，因此需要使用特定的URL和MRS Spark的自带的jar包来连接JDBCServer。

● 问题2：确认JDBCServer服务是否正常，查看对应的端口是否正常监测。

### 处理步骤

● 问题1：需要使用特定的URL和MRS Spark的自带的jar包来连接JDBCServer。

● 问题2：确认JDBCServer服务是否正常，查看对应的端口是否正常监测。
----结束

## 20.23 查看 Spark 任务日志失败

### 问题现象

● 任务运行中查看日志失败。

● 任务运行完成，但是查看不到日志。

### 原因分析

● 问题1：可能原因是MapReduce服务异常。

● 问题2：可能原因如下：

– Spark的JobHistory服务异常。

日志太大，NodeManager在做日志汇聚的时候出现超时。

– HDFS存放日志目录权限异常（默认/tmp/logs/用户名/logs）。

日志已被清理（spark的JobHistory默认存放7天的eventLog，配置项为spark.history.fs.cleaner.maxAge；MapReduce默认存放15天的任务日志，配置项为mapreduce.jobhistory.max-age-ms）。

如果Yarn页面上也找不到，可能是被Yarn清理了（默认存放10000个历史任务，配置项为yarn.resourcemanager.max-completed-applications）。

### 处理步骤

### 问题1：确认MapReduce服务是否正常，如果异常，尝试重启服务。如果还是不能恢复，需要查看后台JobhistoryServer日志。

● 问题2：依次排查可能的情况：

a. 查看Spark的JobHistory是否运行正常；

b. 通过查看yarn的app详情页面，确认日志文件是否过大，如果日志汇聚失败，页面的“Log Aggregation Status:”应该显示为失败或者超时；

c. 查看对应目录权限是否异常；

d. 查看目录下是否有对应的appid文件（Spark的eventlog存放目录：MRS 3.x及以后版本的目录是hdfs://hacluster/spark2xJobHistory2x，MRS 3.x以前版本的目录是hdfs://hacluster/sparkJobHistory，任务运行日志存放目录是hdfs://hacluster/tmp/logs/用户名/logs）;

e. 查看appid和当前作业的id是否超过历史记录最大值。
----结束

## 20.24 运行中的 Spark 作业打不开 SparkUI 界面

### 问题现象

MRS集群中的Spark作业运行期间，在Yarn WebUI界面访问SparkUI无法跳转，页面长时间加载中。

作业运行结束后，SparkUI可以正常访问。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/45c9027ee99db9e0c4f754c298a06e0917856971dce364ba958a9bf5271b1455.jpg)

### 原因分析

这种情况通常是由于Driver异常导致的，优先检查Driver的GC日志，很可能会看到频繁Full GC的日志。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/3a40819a92280737a3f9cd8f5fab8c3524537016cfdd2bf7c906c57e72560992.jpg)

### 处理步骤

步骤1 Driver内存不足，频繁Full GC导致打不开SparkUI，建议通过调整“spark.driver.memory”参数增大Driver内存。

步骤2 检查上层业务代码是否存在不合理情况，例如以下场景：

1. 有调用collect()、show()之类的算子，这些算子会把集群内所有数据都抽取到Driver内存。

2. 在select大表或者大分区的时候，没有加限制条件，导致数据量过大。

----结束

## 20.25 Spark Streaming 任务提交失败

### 问题现象

● 连接Kafka时系统报类找不到的错误。

● 连接带Kerberos的Kafka，报认证错误。

● SparkStreaming任务运行一段时间后开始报TOKEN过期问题。

### 原因分析

### 问题1：Spark提交任务默认不会加载kafka的相关包，所以需要在启动命令中增加--jars来指定对应kafka版本的jar包

### 问题2：连接Kafka无法使用Spark的认证信息，需要将相关的认证使用JVM的参数设置进去。

### 问题3：Spark默认使用当前客户端的认证信息提交任务，也可以使用代码login的方式。但是这两种认证方式都无法更新任务使用的Token，当提交的时候生成的Token信息过期以后就无法再使用，因此报错。解决办法是使用--keytab和--principal将keytab文件和对应用户带入任务中。

### 处理步骤

### 问题1：启动命令中增加--jars来指定对应kafka版本的jar包，一般是在Spark客户端目录/jars/streamingClient（0.8版本Kafka）和Spark客户端目录/jars/streamingClient010（0.10版本Kafka）。

● 问题2：参考指导文档编辑并运行程序。

### 问题3：使用--keytab和--principal将keytab文件和对应用户带入任务中。如果此处的keytab文件和之前Kafka的jaas.conf中配置的是同一个，则Spark会报一个文件多次上传的问题。解决办法是复制一份keytab文件，使得--files和--keytab上传不同的文件。
----结束

## 20.26 Spark 连接 HBase 认证错误

### 问题现象

● Spark连接HBase，报认证失败或者连接不到HBase表。

● Spark连接HBase报找不到jar包。

### 原因分析

### 问题1：HBase没有获取到当前任务的认证信息，导致连接HBase的时候认证失败，无法读取到相应数据。

● 问题2：Spark默认没有加载HBase相关的jar包，需要使用--jars添加到任务中。

### 处理步骤

● 问题1：可以尝试开启HBase认证开关：

spark.yarn.security.credentials.hbase.enabled=true。但不建议直接用HBase客户端的hbase-site.xml替换Spark客户端下的hbase-site.xml，两者并不是完全相同。

● 问题2：需要将HBase相关的包使用--jars上传。
----结束

## 20.27 Spark 连接 Kafka 认证错误

### 问题现象

MRS 2.1.0版本集群中Spark消费kafka数据，过一天以后就会出现认证失败的报错：

2021-06-23 10:36:00,218  INFO  Driver  Final app status: FAILED, exitCode: 15, (reason: User class threw exception: org.apache.spark.SparkException: Job aborted due to
stage failure: Task 1 in stage 1515.0 failed 4 times, most recent failure: Lost task 1.3 in stage 1515.0 (TID 3036, node-ana-coreiUMb, executor 1):
org.apache.kafka.common.errors.SaslAuthenticationException: An error: (java.security.PrivilegedActionException: javax.security.sasl.SaslException: GSS initiate failed [Caused
by GSSException: No valid credentials provided (Mechanism level: Failed to find any Kerberos tgt)]) occurred when evaluating SASL token received from the Kafka Broker. Kafka
Client will go to AUTHENTICATION FAILED state.
Caused by: javax.security.sasl.SaslException: GSS initiate failed [Caused by GSSException: No valid credentials provided (Mechanism level: Failed to find any Kerberos tgt)]
at org.apache.kafka.common.security.authenticator.SaslClientAuthenticator$2.run(SaslClientAuthenticator.java:362)
at org.apache.kafka.common.security.authenticator.SaslClientAuthenticator$2.run(SaslClientAuthenticator.java:360)
at java.security.AccessController.doPrivileged(Native Method)
at javax.security.auth.Subject.doAs(Subject.java:422)
at org.apache.kafka.common.security.authenticator.SaslClientAuthenticator.createSaslToken(SaslClientAuthenticator.java:360)
at org.apache.kafka.common.security.authenticator.SaslClientAuthenticator.sendSaslClientToken(SaslClientAuthenticator.java:270)
at org.apache.kafka.common.security.authenticator.SaslClientAuthenticator.authenticate(SaslClientAuthenticator.java:207)
at org.apache.kafka.common.network.KafkaChannel.prepare(KafkaChannel.java:81)
at org.apache.kafka.common.network.Selector.pollSelectionKeys(Selector.java:486)
at org.apache.kafka.common.network.Selector.poll(Selector.java:424)
at org.apache.kafka.clients.NetworkClient.poll(NetworkClient.java:460)
at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:261)
at org-apache.kafka.clients.consumer.internala.ConsumerNetworkClient.poll(ConsumerNetworkClient.iava:233)
at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.poll(ConsumerNetworkClient.java:224)
at org.apache.kafka.clients.consumer.internals.ConsumerNetworkClient.awaitMetadataUpdate(ConsumerNetworkClient.java:l56)
at org.apache.kafka.clients.consumer.internals.ConsumerCoordinator.poll(ConsumerCoordinator.java:304)
at org.apache.kafka.clients.consumer.KafkaConsumer.pollOnce(KafkaConsumer.java:ll49)
at org.apache.kafka.clients.consumer.KafkaConsumer.poll(KafkaConsumer.java:lll5)
at org.apache.spark.streaming.kafka010.CachedKafkaConsumer.poll(CachedKafkaConsumer.scala:154)
at org.apache.spark.streaming.kafka0l0.CachedKafkaConsumer.get(CachedKafkaConsumer.scala:86)
at org.apache.spark.streaming.kafka0l0.KafkaRDDIterator.next(KafkaRDD.scala:279)
at org-anache.anark.atreaming.kafka010.KafkaRDDTterator-next(KafkaRDD.acala:231)

### 原因分析

集群版本和运行的程序包版本不匹配。

### 处理步骤

1. 参考运行Spark Streaming 对接Kafka0-10样例程序进行相关配置。

2. 当前集群为MRS 2.1.0版本，请如需使用Maven库中的提供的样例程序，请获取spark-streaming-kafka-0-10_2.11-2.3.2-mrs-2.1.jar包。
----结束

## 20.28 SparkSQL 读取 ORC 表报错

### 问题现象

Hive创建ORC存储格式的表，用SparkSQL读取该表时报错：

Caused bv: iava.util.concurrent.ExecutionException: iava.lang,IndexOutOfBoundsException: Index: 0
at java.util.concurrent.FutureTask.report(FutureTask.java:l22)
at java.util.concurrent.FutureTask.get(FutureTask.java:l92)
at org.apache.hadoop.hive.gl.io.orc.OrcInputFormat.generateSplitsInfo(OrcInputFormat.java:l016)
... 51 more
Caused by: java.lang.IndexOutOfBoundsException: Index: 0
at java.util.Collections$EmptyList.get(Collections.java:4456)
at org.apache.hadoop.hive.ql.io.orc.OrcProto$Type.getSubtypes(OrcProto.java:l2240)
at org.apache.hadoop.hive.ql.io.orc.ReaderImpl.getColumnIndicesFromNames(ReaderImpl.java:651)
at org.apache.hadoop.hive.ql.io.orc.ReaderImpl.getRawDataSizeOfColumns(ReaderImpl.java:634)
at org.apache.hadoop.hive.ql.io.orc.OrcInputFormat$SplitGenerator.populateAndCacheStripeDetails(OrcInputFormat.java:927)
at org.apache.hadoop.hive.ql.io.orc.OrcInputFormat$SplitGenerator.call(OrcInputFormat.java:836)
at org.apache.hadoop.hive.ql.io.orc.OrcInputFormat$SplitGenerator.call(OrcInputFormat.java:702)
at java.util.concurrent.FutureTask.run(FutureTask.java:266)
at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:ll49)
at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
at java.lang.Thread.run(Thread.java:748)

### 原因分析

该问题为一个开源社区问题：https://issues.apache.org/jira/browse/HIVE-11102，使用开源的hive 1.2.1版本包就有可能触发此问题。

MRS的Hive for Spark相关模块已修复该问题。

### 处理步骤

使用MRS集群自带的Hive for Spark包：

hive-beeline-1.2.1.spark_2.2.1-mrs-x.x.x.jar
hive-cli-1.2.1.spark_2.2.1-mrs-x.x.x.jar
hive-common-1.2.1.spark_2.2.1-mrs-x.x.x.jar
hive-exec-1.2.1.spark_2.2.1-mrs-x.x.x.jar
hive-jdbc-1.2.1.spark_2.2.1-mrs-x.x.x.jar
hive-metastore-1.2.1.spark_2.2.1-mrs-x.x.x.jar

华为云Maven库请参考指导通过开源镜像站获取样例工程。
----结束

## 20.29 Spark WebUI 页面无法跳转到任务日志页面

### 问题现象

使用MRS 3.x版本集群，运行Spark任务，在Spark2x服务的WebUI页面上无法直接单击stderr和stdout跳转到日志页面。

### 原因分析

配置项“spark.httpdProxy.enable”未开启。

### 修改配置项查看日志处理步骤

步骤1 在客户端修改spark-defaults.conf的配置项：spark.httpdProxy.enable = true，该配置项取值默认为false。

步骤2 登录Manager界面，选择“集群 > 服务 > Spark2x > 配置 > 全部配置 > JobHistory2x> 自定义 > custom”，增加自定义配置项：spark.httpdProxy.enable=true。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/26847ce60ca8b8e03d74fe11be314a806049e731d3b38d3dc032cfce3653df68.jpg)

图20-3 自定义配置项

步骤3 参考上一步，分别选择“集群 > 服务 > Spark2x > 配置 > 全部配置 > JDBCServer2x >自定义 > custom”和“集群 > 服务 > Spark2x > 配置 > 全部配置 > SparkResource2x> 自定义 > custom”添加自定义配置：spark.httpdProxy.enable=true。

步骤4 单击“保存”保存配置，并在“集群 > 服务 > Spark2x > 概览”页签右上角，选择“更多> 滚动重启服务”。

步骤5 登录Spark2x原生页面即可单击stdout或者stderr访问到executor日志页面。
----结束

### 不修改配置项查看日志处理步骤

● 查看运行完成任务日志

在Spark2x原生页面最上方有一个按钮，可以查看汇聚后任务日志：AggregatedLogs

Spark2.4.5-hw-e1.302023

<table><tr><td>Metric</td><td>Min</td><td>25th percentile</td><td>Median</td><td>75th percentile</td><td>Max</td></tr><tr><td>Duration</td><td>0.8 s</td><td>0.9 s</td><td>1s</td><td>1s</td><td>1s</td></tr><tr><td>GC Time</td><td>0 ms</td><td>0 ms</td><td>0 ms</td><td>13 ms</td><td>13 ms</td></tr></table>

图 20-4 AggregatedLogs
Spark 245w0-02023

Aggregated Logs of Containers:

<table><tr><td rowspan=1 colspan=1>Process Name</td><td rowspan=1 colspan=1>Container ID</td><td rowspan=1 colspan=1>Logs</td></tr><tr><td rowspan=1 colspan=1>ApplicationMaster 1</td><td rowspan=1 colspan=1>container_e04_1627976981617_0001_01_000001</td><td rowspan=1 colspan=1>logs</td></tr><tr><td rowspan=1 colspan=1>Executor 1</td><td rowspan=1 colspan=1>container_e04_1627976981617_0001_01_000002</td><td rowspan=1 colspan=1>logs</td></tr><tr><td rowspan=1 colspan=1>Executor 4</td><td rowspan=1 colspan=1>container_e04_1627976981617_0001_01_000003</td><td rowspan=1 colspan=1>logs</td></tr><tr><td rowspan=1 colspan=1>Executor 5</td><td rowspan=1 colspan=1>container_e04_1627976981617_0001_01_000004</td><td rowspan=1 colspan=1>logs</td></tr><tr><td rowspan=1 colspan=1>Executor 2</td><td rowspan=1 colspan=1>container_e04_1627976981617_0001_01_000005</td><td rowspan=1 colspan=1>logs</td></tr><tr><td rowspan=1 colspan=1>Executor 3</td><td rowspan=1 colspan=1>container_e04_1627976981617_0001_01_000006</td><td rowspan=1 colspan=1>logs</td></tr><tr><td rowspan=1 colspan=1>Executor 6</td><td rowspan=1 colspan=1>container_e04_1627976981617_0001_01_000007</td><td rowspan=1 colspan=1>logs</td></tr></table>

- 查看运行中的任务日志

在Spark2x原生页面，通过“Jobs > Stage > Task”找到对应的executor，单击后面的stdout或者stderr查看整个executor日志。

图 20-5 Jobs

Spark 24.5.4wwe-32023

Spark Jobs (?)

<table><tr><td rowspan=1 colspan=1>Job ld </td><td rowspan=1 colspan=1>Description</td><td rowspan=1 colspan=1>Submitted</td><td rowspan=1 colspan=1>Duration</td><td rowspan=1 colspan=1>Stages: Succeeded/Total</td></tr><tr><td rowspan=1 colspan=1>0</td><td rowspan=1 colspan=1>count at <console>:25count at <console>:25</td><td rowspan=1 colspan=1>2021/08/03 16:17:31</td><td rowspan=1 colspan=1>3s</td><td rowspan=1 colspan=1>1/1</td></tr></table>

图 20-6 Stage

Details for Job 0

Completed Stages (1)

<table><tr><td rowspan=1 colspan=1>Stage Id</td><td rowspan=1 colspan=1>Description</td><td rowspan=1 colspan=1>Submitted</td><td rowspan=1 colspan=1>Duration</td><td rowspan=1 colspan=1>Tasks: Succeeded</td></tr><tr><td rowspan=1 colspan=1>o</td><td rowspan=1 colspan=1>count at <console>:25</td><td rowspan=1 colspan=1>2021/08/03 16:17:31</td><td rowspan=1 colspan=1>3s</td><td rowspan=1 colspan=1></td></tr></table>

图 20-7 Task

Spark2.4.5-hw-el-302023

<table><tr><td>Executor ID -</td><td>Address</td><td>Task Time</td><td>Total Tasks</td><td>Failed Tasks</td><td>Killed Tasks</td><td>Succeeded Tasks</td><td>Blacklisted</td><td>琴豪教套藝</td></tr><tr><td>1</td><td>node-ana-coreZleL0003.8165c96c-e74d-4514-bafc-ab3941191507.com:22646</td><td>2s</td><td>2</td><td>0</td><td>0</td><td></td><td>false</td><td></td></tr><tr><td>2</td><td>node-ana-coreZleL0002.8f65c96c-e74d-45r4-bafc-ab3941191507.com:22856</td><td>3 s</td><td>2</td><td>0</td><td>0</td><td></td><td>false</td><td></td></tr></table>

<table><tr><td rowspan=1 colspan=1>0</td><td rowspan=1 colspan=1>0</td><td rowspan=1 colspan=1>0</td><td rowspan=1 colspan=1>SUCCESS</td><td rowspan=1 colspan=1>PROCESS_LOCAL</td><td rowspan=1 colspan=1>1</td><td rowspan=1 colspan=1>node-ana-coreZleL0003.8165c96c-e74d-45f4-bafc-ab394f191507.com</td><td rowspan=1 colspan=1>stdoutstderr</td><td rowspan=1 colspan=1>2021/08/03 16:17:32</td><td rowspan=1 colspan=1>0.8 s</td><td rowspan=1 colspan=1></td><td rowspan=1 colspan=1></td></tr><tr><td rowspan=1 colspan=1>1</td><td rowspan=1 colspan=1>1</td><td rowspan=1 colspan=1>0</td><td rowspan=1 colspan=1>SUCCESS</td><td rowspan=1 colspan=1>PROCESS_LOCAL</td><td rowspan=1 colspan=1>2</td><td rowspan=1 colspan=1>node-ana-coreZleL0002.8165c96c-e74d-45f4-bafc-ab394f191507.com</td><td rowspan=1 colspan=1>st</td><td rowspan=1 colspan=1>2021/08/03 16:17:32   0.9</td><td rowspan=1 colspan=1>s</td><td rowspan=1 colspan=1>13 ms</td><td rowspan=1 colspan=1></td></tr><tr><td rowspan=1 colspan=1>2</td><td rowspan=1 colspan=1>2</td><td rowspan=1 colspan=1>0</td><td rowspan=1 colspan=1>SUCCESS</td><td rowspan=1 colspan=1>PROCESS_LOCAL</td><td rowspan=1 colspan=1>1</td><td rowspan=1 colspan=1>node-ana-coreZleL0003.8165c96c-e74d-45f4-bafc-ab394f191507.com</td><td rowspan=1 colspan=1>stdoutstderr</td><td rowspan=1 colspan=1>2021/08/03 16:17:33</td><td rowspan=1 colspan=1>1s</td><td rowspan=1 colspan=1></td><td rowspan=1 colspan=1></td></tr><tr><td rowspan=1 colspan=1>3</td><td rowspan=1 colspan=1>3</td><td rowspan=1 colspan=1>0</td><td rowspan=1 colspan=1>SUCCESS</td><td rowspan=1 colspan=1>PROCESS_LOCAL</td><td rowspan=1 colspan=1>2</td><td rowspan=1 colspan=1>node-ana-coreZleL0002.8f65c96c-e74d-45f4-bafc-ab394f191507.com</td><td rowspan=1 colspan=1>stdoutstderr</td><td rowspan=1 colspan=1>2021/08/03 16:17:33</td><td rowspan=1 colspan=1>1s</td><td rowspan=1 colspan=1></td><td rowspan=1 colspan=1></td></tr></table>

### 参考信息

通过单击stdout或者stderr进入日志页面以后只会展示stdout或者stderr的日志，如果需要查看完整日志，可以通过将url里面的stdout或者stderr去掉，然后就可以直接访问这个executor的所有日志。

例如：

https://<EIP>:9022/component/Yarn/NodeManager/15/node/containerlogs/ container_e04_1627976981617_0002_01_000002/root/stderr?start=-4096

修改为：

https://<EIP>:9022/component/Yarn/NodeManager/15/node/containerlogs/ container_e04_1627976981617_0002_01_000002/root/?start=-4096

即可看到所有日志文件。

图 20-8 所有日志文件

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/5cadf1420a5bfa857721e34a91fe7cb3cb0977cef7efa735b231b03f34d486b4.jpg)

Logs for container_e04_1627976981617_0002_01_000002

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/1399b55e1061b14a18fb400f56d2282637605257d50c82f52b82f0521ab6a494.jpg)
----结束

## 20.30 spark-beeline 查询 Hive 视图报错

### 用户问题

MRS 3.1.2版本，spark-beeline查询Hive视图报错，报错如下：

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/c571789de4174a7897ff233169b745744e08b9ba4c3aaee62ca4ece0a03c042a.jpg)

根据提示set spark.sql.hive.manageFilesourcePartitions=false后，查不到数据（但是实际在Hive查询中是有数据的）。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/eae881c8883efe9f209361b67b96dd2d7271c033c84a46fe6226d3b8d211fd7c.jpg)

### 原因分析

转换格式失败，spark-sql使用其内置的Metastore，而不是Hive中使用的Metastore，所以读取元数据时失败，spark-sql内部读取的是Partque格式的数据，而Hive中默认是ORC的。

### 处理步骤

步骤1 登录Spark客户端节点，执行如下命令，进入spark-sql：cd {客户端安装目录}source bigdata_envsource Spark2x/component_envkinit 组件业务用户（普通模式无需执行kinit）spark-sql

步骤2 执行如下命令设置spark.sql.hive.convertMetastoreOrc=false。set spark.sql.hive.convertMetastoreOrc=false;

步骤3 重新查询Hive视图，显示正常。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/795b3c2076f06c814439ea7edc5a5517d3339c73db2bba3049ce83a3ada4a7ee.jpg)
----结束

## 20.31 Spark Streaming 任务失败但是 Yarn WebUI 中显示状态为成功

### 问题现象

MRS 3.3.0-LTS版本集群，提交Spark Streaming任务后，由于NodeAgent重启导致对应节点上任务失败，但是在Yarn WebUI页面中查看整个任务状态为“succeeded”。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/e44ec6be73f8600163cc8db8909cfa21a1441e61fb752248dd319ee392761a6a.jpg)

### 原因分析

Spark AM退出时，因为服务配置参数

“spark.streaming.stopGracefullyOnShutdown”默认为“false”，系统不会完全等待AM正常退出，所以概率性地会出现有时能正常退出，任务状态显示失败，有时异常退出，状态未来得及上报的情况。

### 处理步骤

执行Spark Streaming任务时，添加Spark任务参数“--confspark.streaming.stopGracefullyOnShutdown=true”，指定

“spark.streaming.stopGracefullyOnShutdown”参数为“true”。
----结束

## 20.32 访问 Spark 应用获取的 restful 接口信息有误

### 问题现象

当Spark应用结束后，访问该应用的restful接口获取job信息，发现job信息中“numActiveTasks”的值是负数，如图20-9所示。

图 20-9 job 信息

[{
jobId" : 0,
"name" : "reduce at SparkPi.scala:36",
"submissionTime" : "2016-05-28T09:35:34.415GMT"
completionTime" :"2016-05-28T09:35:35.686GMT"
stageIds" : [ 0 ],
"st atus" : "SUCCEEDED",
numTasks" : 2,
"numActiveTasks" : -1,
numCompletedTasks" :
"numSkippedTasks" : 2,
numFailedTasks" : 0,
numActiveStages" : 0,
"numCompletedStages" : 1,
"numSkippedStages" : 0,
"numFailedStages" : 0
1]

### 说明

numActiveTasks是指当前正在运行task的个数。

### 处理步骤

通过下面两种途径获取上面的job信息：

● 配置spark.history.briefInfo.gather=true，查看JobHistory的brief信息。

● 使用Spark JobHistory2x页面访问：https://IP:port/api/v1/<appid>/jobs/。

job信息中“numActiveTasks”的值是根据eventlog文件中SparkListenerTaskStart和SparkListenerTaskEnd事件的个数的差值计算得到的。如果eventLog文件中有事件丢失，就可能出现上面的现象。
----结束

## 20.33 从 Yarn Web UI 页面无法跳转到 Spark Web UI 界面

### 问题现象

在客户端采用yarn-client模式运行Spark应用，然后从Yarn的页面打开该应用的WebUI界面，出现下面的错误：

Error Occurred.

Problem accessing /proxy/application_

Powered by Jetty://

从YARN ResourceManager的日志看到：
2016-07-21 16:35:27,099 | INFO | Socket Reader #1 for port 8032 | Auth successful for mapred/hadoop.<系
@ (auth:KERBEROS) | Server.java:1388
2016-07-21 16:35:27,105 | INFO | 1526016381@qtp-1178290888-1015 | admin is accessing unchecked
http://10.120.169.53:23011 which is the app master GUI of
application_1468986660719_0045 owned by spark | WebAppProxyServlet.java:393
2016-07-21 16:36:02,843 | INFO | Socket Reader #1 for port 8032 | Auth successful for hive/hadoop.<系统域
@ (auth:KERBEROS) | Server.java:1388
2016-07-21 16:36:02,851 | INFO | Socket Reader #1 for port 8032 | Auth successful for hive/hadoop.<系统域
@ (auth:KERBEROS) | Server.java:1388
2016-07-21 16:36:12,163 | WARN | 1526016381@qtp-1178290888-1015 | /proxy/
application_1468986660719_0045/: java.net.ConnectException: Connection timed out |
Slf4jLog.java:76
2016-07-21 16:37:03,918 | INFO | Socket Reader #1 for port 8032 | Auth successful for hive/hadoop.<系统域
@ (auth:KERBEROS) | Server.java:1388
2016-07-21 16:37:03,926 | INFO | Socket Reader #1 for port 8032 | Auth successful for hive/hadoop.<系统域
@ (auth:KERBEROS) | Server.java:1388
2016-07-21 16:37:11,956 | INFO | AsyncDispatcher event handler | Updating application attempt
appattempt_1468986660719_0045_000001 with final state: FINISHING,
and exit status: -1000 | RMAppAttemptImpl.java:1253

### 处理步骤

打开FusionInsight Manager页面，看到Yarn服务的业务IP地址为192网段。

从Yarn的日志看到，Yarn读取的Spark Web UI地址为http://10.120.169.53:23011，是10网段的IP地址。由于192网段的IP和10网段的IP不能互通，所以导致访问Spark WebUI界面失败。

修改方案：

登录10.120.169.53客户端机器，修改/etc/hosts文件，将10.120.169.53更改为相对应的192网段的IP地址。再重新运行Spark应用，这时就可以打开Spark Web UI界面。
----结束

## 20.34 HistoryServer 缓存的应用被回收，导致此类应用页面访问时出错

### 问题现象

在History Server页面中访问某个Spark应用的页面时，发现访问时出错。

查看相应的HistoryServer日志后，发现有“FileNotFound”异常，相关日志如下所示：

2016-11-22 23:58:03,694 | WARN | [qtp55429210-232] | /history/application_1479662594976_0001/stages/
stage/ | org.sparkproject.jetty.servlet.ServletHandler.doHandle(ServletHandler.java:628)
java.io.FileNotFoundException: ${BIGDATA_HOME}/tmp/spark/jobHistoryTemp/
blockmgr-5f1f6aca-2303-4290-9845-88fa94d78480/09/temp_shufle_11f82aaf-e226-46dc
b1f0-002751557694 (No such file or directory)

### 处理步骤

在History Server页面加载Task个数较多的Spark应用时，由于无法把全部的数据放入内存中，导致数据溢出到磁盘时，会产生前缀为“temp_shufle”的文件。

HistoryServer默认会缓存50个Spark应用（由配置项

“spark.history.retainedApplications”决定），当内存中的Spark应用个数超过这个数值时，HistoryServer会回收最先缓存的Spark应用，同时会清理掉相应的“temp_shufle”文件。

当用户正在查看即将被回收的Spark应用时，可能会出现找不到“temp_shufle”文件的错误，从而导致当前页面无法访问。

如果遇到上述问题，可参考以下两种方法解决。

● 重新访问这个Spark应用的HistoryServer页面，即可查看到正确的页面信息。

如果用户场景需要同时访问50个以上的Spark应用时，需要调大“spark.history.retainedApplications”参数的值。

请登录FusionInsight Manager管理界面，单击“集群 > 服务 > Spark2x > 配置”，单击“全部配置”，在左侧的导航列表中，单击“JobHistory2x > 界面”，配置如下参数。

表 20-1 参数说明

<table><tr><td rowspan=1 colspan=1>参数</td><td rowspan=1 colspan=1>描述</td><td rowspan=1 colspan=1>取值示例</td></tr><tr><td rowspan=1 colspan=1>spark.history.retainedApplications</td><td rowspan=1 colspan=1>HistoryServer缓存的Spark应用数，当需要缓存的应用个数超过此参数值时，HistoryServer会回收最先缓存的Spark应用。取值范围：大于等于1</td><td rowspan=1 colspan=1>50</td></tr></table>
----结束

## 20.35 加载空的 part 文件时，app 无法显示在 JobHistory的页面上

### 问题现象

在分组模式下执行应用，当HDFS上的part文件为空时，发现JobHistory首页面上不显示该part对应的app。

### 处理步骤

JobHistory服务更新页面上的app时，会根据HDFS上的part文件大小变更与否判断是否刷新首页面的app显示信息。如果文件为第一次查看，则将当前文件大小与0做比较，如果大于0则读取该文件。

分组的情况下，如果执行的app没有job处于执行状态，则part文件为空，即JobHistory服务不会读取该文件，此app也不会显示在JobHistory页面上。但如果part文件大小之后有更新，JobHistory又会显示该app。
----结束

## 20.36 Spark 导出带有相同字段名的表失败

### 问题现象

在Spark的spark-shell上执行如下代码失败：

```kotlin
val acctId = List(("49562", "Amal", "Derry"), ("00000", "Fred", "Xanadu"))
val rddLeft = sc.makeRDD(acctId)
val dfLeft = rddLeft.toDF("Id", "Name", "City")
//dfLeft.show
val acctCustId = List(("Amal", "49562", "CO"), ("Dave", "99999", "ZZ"))
val rddRight = sc.makeRDD(acctCustId)
val dfRight = rddRight.toDF("Name", "CustId", "State")
//dfRight.show
val dfJoin = dfLeft.join(dfRight, dfLeft("Id") === dfRight("CustId"), "outer")
dfJoin.show
dfJoin.repartition(1).write.format("com.databricks.spark.csv").option("delimiter", "\t").option("header",
"true").option("treatEmptyValuesAsNulls", "true").option("nullValue", "").save("/tmp/outputDir")
```

### 处理步骤

Spark导出带有相同字段名的表，会导出失败。

Spark中对join语句重名字段做了判断，需要修改代码保证保存的数据中无重复字段。
----结束

## 20.37 多次运行 Spark 应用程序引发 JRE 错误

### 问题现象

为什么多次运行Spark应用程序会引发致命JRE错误？

### 处理步骤

多次运行Spark应用程序会引发致命的JRE错误，这个错误由Linux内核导致。
升级内核版本到4.13.9-2.ge7d7106-default来解决这个问题。
----结束

## 20.38 Spark 如何访问外部集群组件

### 问题现象

存在两个集群：cluster1和cluster2，如何使用cluster1中的Spark访问cluster2中的HDFS、Hive、HBase和Kafka组件。

### 处理步骤

1. 可以有条件地实现两个集群间组件互相访问，但是存在以下限制：

仅允许访问一个Hive MetaStore，不支持同时访问cluster1的Hive MetaStore和cluster2的Hive MetaStore。

不同集群的用户系统没有同步，因此访问跨集群组件时，用户的权限管理由对端集群的用户配置决定。比如cluster1的userA没有访问本集群HBase meta

表权限，但是cluster2的userA有访问该集群HBase meta表权限，则cluster1的userA可以访问cluster2的HBase meta表。

– 跨Manager之间的安全集群间组件互相访问，需要先配置系统互信。

2. 以下分别阐述cluster1上使用userA访问cluster2的Hive、HBase、Kafka组件。

### 说明

以下操作皆以用户使用FusionInsight客户端提交Spark2x应用为基础，如果用户使用了自己的配置文件目录，则需要修改本应用配置目录中的对应文件，并注意需要将配置文件上传到executor端。

由于hdfs和hbase客户端访问服务端时，使用hostname配置服务端地址，因此，客户端的/etc/hosts需要保存有所有需要访问节点的hosts配置。用户可预先将对端集群节点的host添加到客户端节点的/etc/hosts文件中。

访问Hive MetaStore：使用cluster2中的Spark2x客户端下“conf”目录下的hive-site.xml文件，替换到cluster1中的Spark2x客户端下“conf”目录下的hive-site.xml文件。

如上操作后可以用sparksql访问hive MetaStore，如需访问hive表数据，需要按照•同时访问两个集群的HDFS：的操作步骤配置且指定对端集群nameservice为LOCATION后才能访问表数据。

访问对端集群的HBase：

i. 先将cluster2集群的所有Zookeeper节点和HBase节点的IP和主机名配置到cluster1集群的客户端节点的/etc/hosts文件中。

ii. 使用cluster2中的Spark2x客户端下“conf”目录的hbase-site.xml文件，替换到cluster1中的Spark2x客户端下“conf”目录hbase-site.xml文件。

访问Kafka，仅需将应用访问的Kafka Broker地址设置为cluster2中的KafkaBroker地址即可。

同时访问两个集群的HDFS：

无法同时获取两个相同nameservice的token，因此两个HDFS的nameservice必须不同，例如：一个为hacluster，一个为test。

1) 从cluster2的hdfs-site.xml中获取以下配置，添加到cluster1的spark2x客户端conf目录的hdfs-site.xml中

dfs.nameservices.mappings、dfs.nameservices、 dfs.namenode.rpc-address.test.*、dfs.ha.namenodes.test、 dfs.client.failover.proxy.provider.test

参考样例如下：

<property>
<name>dfs.nameservices.mappings</name>
<value>[{"name":"hacluster","roleInstances":["14","15"]},
{"name":"test","roleInstances":["16","17"]}]</value>
</property>
<property>
<name>dfs.nameservices</name>
<value>hacluster,test</value>
</property>
<property>
<name>dfs.namenode.rpc-address.test.16</name>
<value>192.168.0.1:8020</value>
</property>
<property>
<name>dfs.namenode.rpc-address.test.17</name>
<value>192.168.0.2:8020</value>
</property>
<property>
<name>dfs.ha.namenodes.test</name>

<value>16,17</value>
</property>
<property>
<name>dfs.client.failover.proxy.provider.test</name>
<value>org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider
</value>
</property>

2) 修改cluster1的spark客户端conf目录下的spark-defaults.conf配置文件中，修改spark.yarn.extra.hadoopFileSystems = hdfs://test，spark.hadoop.hdfs.externalToken.enable = true，如下所示：spark.yarn.extra.hadoopFileSystems = hdfs://testspark.hadoop.hdfs.externalToken.enable = true

3) 应用提交命令中，需要添加--keytab和--principal参数，参数配置为cluster1中提交任务的用户。

4) 使用cluster1的spark客户端提交应用，即可同时访问两个HDFS服务。

同时访问两个集群的HBase：

i. 修改cluster1的spark客户端conf目录下的spark-defaults.conf配置文件中，修改spark.hadoop.hbase.externalToken.enable = true，如下所示：

spark.hadoop.hbase.externalToken.enable = true

ii. 用户访问HBase时，需要使用对应集群的配置文件创建Configuration对象，用于创建Connection对象。

iii. MRS集群中支持同时获取多个HBase服务的token，以解决Executor中无法访问HBase的问题，使用方式如下：

假设需要访问本集群的HBase和cluster2的HBase，将cluster2的hbase-site.xml文件放到一个压缩包内，压缩包命名为
external_hbase_conf***，提交命令时，使用--archives指定这些压缩包。
----结束

## 20.39 对同一目录创建多个外表导致外表查询失败

### 问题现象

假设存在数据文件路径“/test_data_path”，用户userA对该目录创建外表tableA，用户userB对该目录创建外表tableB，当userB对tableB执行insert操作后，userA将查询tableA失败，出现Permission denied异常。

### 处理步骤

当userB对tableB执行insert操作后，会在外表数据路径下生成新的数据文件，且文件属组是userB，当userA查询tableA时，会读取外表数据目录下的所有的文件，此时会因没有userB生成的文件的读取权限而查询失败。

实际上，不只是查询场景，还有其他场景也会出现问题。例如：insert overwrite操作将会把此目录下的其他表文件也一起复写。

由于Spark SQL当前的实现机制，如果对此种场景添加检查限制，会存在一致性问题和性能问题，因此未对此种场景添加限制，但是用户应避免此种用法，以避免此场景带来的各种问题。
----结束

## 20.40 访问 Spark JobHistory 中某个应用的原生页面时页面显示错误

### 问题现象

提交一个Spark应用，包含单个Job百万个task。应用结束后，在JobHistory中访问该应用的原生页面，浏览器会等待较长时间才跳转到应用原生页面，如果10分钟内无法跳转，则页面会显示Proxy Error信息。

图20-10 错误信息样例

Proxy Error

### 原因分析

在JobHistory界面中跳转到某个应用的原生页面时，JobHistory需要回放该应用的Event log，如果应用包含的事件日志较大，则回放时间较长，浏览器需要较长时间的等待。

当前浏览器访问JobHistory原生页面需经过httpd代理，代理的超时时间是10分钟，因此，如果JobHistory在10分钟内无法完成Event log的解析并返回，httpd会主动向浏览器返回Proxy Error信息。

### 处理步骤

由于当前JobHistory开启了本地磁盘缓存功能，访问应用时，会将应用的Event log的解析结果缓存到本地磁盘中，第二次访问时，能大大加快响应速度。因此，出现此种情况时，仅需稍作等待，重新访问原来的链接即可，此时不会再出现需要长时间等待的现象。
----结束

## 20.41 通过 spark-beeline 指定 location 到 OBS 建表失败

### 问题现象

对接OBS ECS/BMS集群，spark-beeline登录后，指定location到OBS建表报错失败。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/4f1ee4116f4d92e718e4281f3fbcd1e96768fbd1979acfabffe364eeb9ff3268.jpg)

### 原因分析

HDFS上ssl.jceks文件权限不足，导致建表失败。

Caused by: org-apache-hadoop-segurity.AccessControlException: Permission denied: user=root, acceas=BrAd, inode="/user/spark2x/iara/8.0.2/ssl.iceks":spark2x:hadoopi-rW--zz---
at org.apache.hadoop.hdfs.server.namenode.FSPermissionChecker.check(FSPermissionChecker.java:410)
at org.apache.hadoop.hdfs.server.namenode.FSPermissionChecker.checkPermission(FSPermissionChecker.java:264)
at com.: ..hadoop.adapter.hdfs.plugin.HWAccessControlEnforce.checkPermission( .java:54)
at org.apache.hadoop.hdfs.server.namenode.FSPermissionChecker.checkPermission(FSPermissionChecker.java:l94)
at org.apache.hadoop.hdfs.server.namenode.FSDirectory.checkPermission(FsDirectory.java:1957)
at org.apache.hadoop.hdfa.server.namenode.FSDirectory.checkPermission(FSDirectory.java:1941)
at org.apache.hadoop.hdfs.server.namenode.FSDirectory.checkPathAccess(FSDirectory.java:l891)
at org.apache.hadoop.hdfs.server.namenode.FSDirStatAndListingOp.getBlockLocations(FSDirStatAndListingOp.java:l75)
at org.apache.hadoop.hdfs.server.namenode.FSNamesystem.getBlockLocations(FSNamesvstem.java:1990)
at org,apache,hadoop,hdfs,server,namenode,NameNodeRpcServer,getBlockLocations (NameNodeRpcServer,1ava:762)
at org,apache,hadoop,hdfs,protocolPB.ClientNamenodeProtocolServerSideTranslatorPB,getBlockLocations(ClientNamenodeProtocolServerSideTranslatorPB,iava:445)
at org,apache,hadoop,hdfs,protocol,proto,ClientNamenodeProtocolProtos$ClientNamenodeProtocol$2,callBlockingMethod(ClientNamenodeProtocolProtos,java)
at org-apache-hadoop.1pc.BPCsServer.cal1(RPC.1ava:1036)
at org.apache.hadoop.ipc.Server$RpcCall.run(Server.java:985)
at org.apache.hadoop.ipc.Server$RpcCall.run(Server.java:913)
at org.apache.hadoop.security.UserGroupInformation.doAs(UserGroupInformation.java:l737)
at org.apache.hadoop.ipc.Server$Handler.run(Server.java:2876)

### 处理步骤

1. 使用omm用户登录Spark2x所在节点，执行如下命令：vi ${BIGDATA_HOME}/FusionInsight_Spark2x_xxx/install/FusionInsight-Spark2x-*/spark/sbin/fake_prestart.sh

2. 将“eval "${hdfsCmd}" -chmod 600 "${InnerHdfsDir}"/ssl.jceks >> "${PRESTART_LOG}" 2>&1”修改成“eval "${hdfsCmd}" -chmod 644 "${InnerHdfsDir}"/ssl.jceks >> "${PRESTART_LOG}" 2>&1”。

3. 重启SparkResource实例。
----结束

## 20.42 Spark shufle 异常处理

### 问题现象

在部分场景Spark shufle阶段会有如下异常：

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/843cbf1a2222b3dd87687533702ad2e2a6571bdff7b097066ca2637011ae700f.jpg)

### 处理步骤

- JDBC连接：

登录FusionInsight Manager管理界面，修改JDBCServer的参数“spark.authenticate.enableSaslEncryption”值为“false”，并重启对应的实例。

● 客户端作业：

客户端应用在提交应用的时候，修改spark-defaults.conf配置文件的“spark.authenticate.enableSaslEncryption”值为“false”。
----结束

## 20.43 JDBCServer 节点磁盘空间不足导致实例异常

### 问题现象

JDBCServer启动的Yarn任务长时间运行后将部分节点的磁盘打满，磁盘空间不足，导致节点上的JDBCServer实例异常。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/5f9e4294c4db6b514bad3eeed2450df66402dc501c186a2ad9b82aea218a79c0.jpg)

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/0d4eb82a8490b53654cb223dae76c9cab6f444778cb1f35b697dc00a24334f5d.jpg)

### 处理步骤

● MRS 3.1.2-LTS之前版本：

登录FusionInsight Manager界面，选择“集群 > 服务 > Spark >实例”，重启对应JDBCServer实例即可清理磁盘。

● MRS 3.1.2-LTS及之后版本：

登录FusionInsight Manager界面，选择“集群 > 服务 > Spark > 配置 > 全部配置 > JDBCServer（角色） > 自定义”，在“custom”中添加参数“spark.shufle.service.removeShufle”值为“true”，保存配置，并重启对应的实例。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/61a963b7d9b61381173405abc2acb39ff7e5da8dfcac3d15a2244aeefc2f4f13.jpg)

图 20-12 添加参数

表 20-2 参数解释

<table><tr><td rowspan=1 colspan=1>参数</td><td rowspan=1 colspan=1>描述</td><td rowspan=1 colspan=1>取值示例</td></tr><tr><td rowspan=1 colspan=1>spark.shuffle.service.removeShuffle</td><td rowspan=1 colspan=1>是否在不再需要shuffle时使用ExternalShuffleService来删除已释放executors的shuffle块。若不启用此选项，已释放executors上的shuffle数据将保留在磁盘上，直到应用程序结束。默认为false，表示不启用该功能。</td><td rowspan=1 colspan=1>true</td></tr></table>
----结束

## 20.44 使用集群外客户端连接 Spark 端口失败

### 问题现象

安装集群外客户端或使用集群外客户端时，有时会出现连接Spark任务端口失败的问题。

异常信息：Failed to bind SparkUi

Cannot assign requested address: Service ‘sparkDriver’ failed after 16 retries (on a random free port)! Consider explicitly setting the appropriate binding address for the service ‘sparkDriver’ (for example spark.driver.bindAddress for SparkDriver) to the correct binding address.

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/a7797f0fbad27113f2b33adf0c78b7a6b4d163e914a9e550406365876a72ea31.jpg)

### 处理步骤

应用无法访问到SparkUI的IP:PORT。可能有以下原因：

● 可能原因一：集群节点与客户端节点网络不通。

解决方法：

查看客户端节点“/etc/hosts”文件中是否配置集群节点映射，在客户端节点执行命令：

ping sparkui的IP

如果ping不通，检查映射配置与网络设置。

● 可能原因二：客户端节点防火墙未关闭。

解决方法：

执行如下命令可查看是否关闭：

systemctl status firewalld（不同的操作系统查询命令不一致，此命令以CentOS为例）

如下图所示：dead表示关闭。

Loaded: not-found (Reason: No such file or directory) Active: inactive(dead)

防火墙开则影响通信，执行如下命令关闭防火墙：

service firewalld stop（不同的操作系统查询命令不一致，此命令以CentOS为例）

### 可能原因
三：端口被占用，每一个Spark任务都会占用一个SparkUI端口，默认为22600，如果被占用则依次递增端口重试。但是有个默认重试次数，为16次。16次重试都失败后，会放弃该任务的运行。

查看端口是否被占用：

ssh -v -p port username@ip

如果输出“Connection established”，则表示连接成功，端口已被占用。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/a32353639c82675183779f9bb45fa8aa7e5d438bc6e93709640d913597e05399.jpg)

Spark UI端口范围由配置文件spark-defaults.conf中的参数

“spark.random.port.min”和“spark.random.port.max”决定，如果该范围端口都已被占用，则

导致无端口可用从而连接失败。

解决方法：调节重连次数spark.port.maxRetries=50，并且调节executor随机端口范围spark.random.port.max+100

● 可能原因四：客户端Spark配置参数错误。

解决方法：

在客户端节点执行命令cat spark-env.sh，查看SPARK_LOCAL_HOSTNAME，是否为本机IP。

该问题容易出现在从其他节点直接复制客户端时，配置参数未修改。

需修改SPARK_LOCAL_HOSTNAME为本机IP。

注：如果集群使用EIP通信，则需要设置以下参数。

a. spark-default.conf中添加spark.driver.host = EIP （客户端节点弹性公网IP）

b. spark-default.conf中添加spark.driver.bindAddress=本地IP

c. spark-env.sh中修改SPARK_LOCAL_HOSTNAME=EIP （客户端节点弹性公网IP)

- 可能原因五：代码问题。

解决方法：

Spark在启动任务时会在客户端创建sparkDriverEnv并绑定

DRIVER_BIND_ADDRESS，该逻辑并没有走到服务端，所以该问题产生的原因也是客户端节点操作系统环境问题导致sparkDriver获取不到对应的主机IP。

可以尝试设置spark.driver.bindAddress=127.0.0.1，使提交任务driver端可以加载到loopbackAddress，从而规避问题。
----结束

## 20.45 Datasource Avro 格式查询异常

### 问题现象

Datasource Avro格式查询报错，提示Caused by:

org.apache.spark.sql.avro.IncompatibleSchemaException。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/0f8f597edc8254ff7e09d1eedb735c37b85f528f493c8c5185ae3707e374f8f1.jpg)

### 处理步骤

针对avro格式表查询报错，根本原因是avro格式表schema不匹配导致，需要考虑增量和存量avro格式表查询两个场景：

1. 增量avro格式表，需要创建表之前设置参数spark.sql.forceConvertSchema.enabled=true，会将avro表格式强转指定数据类型，一次性修改schema。

2. 存量avro格式表，查询avro表之前设置参数spark.sql.forceConvertSchema.enabled=true，如果查询失败，可能avro格式表schema被缓存，执行refresh table命令，清除缓存后再设置参数进行查询，会将avro表格式强转指定数据类型，客户端临时修改schema。
----结束

## 20.46 通过 Spark-sql 创建 Hudi 表或者 Hive 表，未插入数据前查询表统计信息为空

### 问题现象

通过spark-sql创建Hudi表或者Hive表，未插入数据之前，查询表统计信息都为空。

### 处理步骤

可以通过以下两种方式生成：

1. 手动通过analyze命令，触发统计信息收集。如果没有插入数据，analyze命令执行完之后，再通过desc formatted table_name命令查询totalsize等于0。

2. 配置spark.sql.statistics.size.autoUpdate.enabled=true，再插入数据，后台会触发统计信息收集。
----结束

## 20.47 建表语句分区列为 timestamp 时，使用非标准格式的时间指定分区查询表统计失败

### 问题现象

建表语句分区列为timestamp时，使用非标准格式的时间指定分区查询表统计失败以及show partitions table结果编码不对。

执行desc formatted test_hive_orc_snappy_internal_table partition(a='2016-8-1'); 查询报错，如下所示：

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/0fb64f63-64e6-4979-827c-26a393ceff34/f2c9d141655b1ac180746ff4361e1b363168f7ea376a4f2422cd2fc256514d80.jpg)

### 处理步骤

spark.sql.hive.convertInsertingPartitionedTable开关控制了Hive和Datasource表的插入写操作逻辑，使用Hive表时逻辑不会自动格式化时间戳，使用Datasource表时会自动格式化时间戳。

如果写入的分区字段是a='2016-8-1 11:45:5'会自动格式化成a='2016-08-0111:45:05'，此时查询使用a='2016-8-1 11:45:5'会报错。

正确查询方式如下：

spark.sql.hive.convertInsertingPartitionedTable=true时使用datasource表逻辑，使用如下方式即可以正常查询：

desc formatted test_hive_orc_snappy_internal_table partition(a='2016-08-01 11:45:05');
----结束

## 20.48 SQL 语法兼容 TIMESTAMP/DATE 特殊字符

### 问题现象

在Spark 3.2.0社区版本之后，将不再支持TIMESTAMP(*)或DATE(*)的语法，其中*代表如下特殊时间字符：

● epoch

● today

● yesterday

● tomorrow

now

默认只支持timestamp '*' 或者date '*'的格式，如果使用之前的语法插入数据表，会得到NULL值。

### 处理步骤

在Spark客户端中执行以下命令设置“spark.sql.convert.special.datetime”参数即可兼容之前的语法。

set spark.sql.convert.special.datetime=true;

spark-sql> set spark.sql.convert.special.datetime=true;

spark.sql.convert.special.datetime true

Time taken: 0.035 seconds, Fetched 1 row(s)
----结束
