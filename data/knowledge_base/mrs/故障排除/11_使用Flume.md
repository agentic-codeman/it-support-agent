

## 11.1 Flume 向 Spark Streaming 提交作业后报类找不到错误

### 用户问题

Flume向Spark Streaming提交作业，提交到集群后报类找不到的错误。

### 问题现象

Spark Streaming代码打成jar包提交到集群后报类找不到错误，通过以下两种方式依然不生效。

1. 在提交Spark作业的时候使用--jars 命令引用类所在的jar包。

2. 将类所在的jar包引入Spark Streaming的jar包。

### 原因分析

执行Spark作业时无法加载部分jar，导致找不到class。

### 处理步骤

步骤1 使用 --jars 加载flume-ng-sdk-{version}.jar依赖包。

步骤2 同时修改“spark-default.conf”中两个配置项。spark.driver.extraClassPath=$PWD/*:{加上原来配置的值}spark.executor.extraClassPath =$PWD/*

步骤3 作业运行成功。如果还有报错，则需要排查还有哪个jar没有加载，再次执行步骤1和步骤2。
----结束

## 11.2 Flume 客户端安装失败

### 问题现象

安装Flume客户端失败，提示JAVA_HOME is null或flume has been installed。

CST 2016-08-31 17:02:51 [flume-client install]: JAVA_HOME is null in current user,please install the JDK and
set the JAVA_HOME
CST 2016-08-31 17:02:51 [flume-client install]: check environment failed.
CST 2016-08-31 17:02:51 [flume-client install]: check param failed.
CST 2016-08-31 17:02:51 [flume-client install]: install flume client failed.

CST 2016-08-31 17:03:58 [flume-client install]: flume has been installed CST 2016-08-31 17:03:58 [flume-client install]: check path failed. CST 2016-08-31 17:03:58 [flume-client install]: check param failed. CST 2016-08-31 17:03:58 [flume-client install]: install flume client failed.

### 原因分析

Flume客户端安装时会检查环境变量，如果没有可用的JAVA，会报错并退出安装。

● 指定的目录下已经安装有Flume客户端。

### 解决办法

步骤1 如果报JAVA_HOME is null错误，需要使用命令：

export JAVA_HOME=java路径

设置JAVA_HOME，重新运行安装脚本。

步骤2 如果指定的目录下已经安装有Flume客户端，需要先卸载已经存在的Flume客户端，或指定其他目录安装。

----结束

## 11.3 Flume 客户端无法连接服务端

### 问题现象

安装Flume客户端并设置Avro Sink与服务端通信，发现无法连接Flume服务端。

### 原因分析

1. 服务端配置错误，监测端口启动失败，例如服务端Avro Source配置了错误的IP，或者已经被占用了的端口。

```csv
查看Flume运行日志：
2016-08-31 17:28:42,092 | ERROR | [lifecycleSupervisor-1-9] | Unable to start
EventDrivenSourceRunner: { source:Avro source avro_source: { bindAddress: 10.120.205.7, port:
21154 } } - Exception follows. | org.apache.flume.lifecycle.LifecycleSupervisor
$MonitorRunnable.run(LifecycleSupervisor.java:253)
java.lang.RuntimeException: org.jboss.netty.channel.ChannelException: Failed to bind to: /
192.168.205.7:21154
```

2. 若采用了加密传输，证书或密码错误。

2016-08-31 17:15:59,593 | ERROR | [conf-file-poller-0] | Source avro_source has been removed due to
an error during configuration |
org.apache.flume.node.AbstractConfigurationProvider.loadSources(AbstractConfigurationProvider.java:3
88)
org.apache.flume.FlumeException: Avro source configured with invalid keystore: /opt/Bigdata/
MRS_XXX/install/FusionInsight-Flume-1.9.0/flume/conf/flume_sChat.jks

3. 客户端与服务端通信异常。

PING 192.168.85.55 (10.120.85.55) 56(84) bytes of data. From 192.168.85.50 icmp_seq=1 Destination Host Unreachable From 192.168.85.50 icmp_seq=2 Destination Host Unreachable From 192.168.85.50 icmp_seq=3 Destination Host Unreachable From 192.168.85.50 icmp_seq=4 Destination Host Unreachable

### 解决办法

步骤1 设置为正确的IP，必须为本机的IP，如果端口被占用，重新配置一个空闲的端口。

步骤2 配置正确的证书路径。

步骤3 联系网络管理员，恢复网络。

----结束

## 11.4 Flume 数据写入组件失败

### 问题现象

Flume进程启动后，Flume数据无法写入到对应组件（本示例以服务端写入到HDFS为例）。

### 原因分析

1. HDFS未启动或故障。

2019-02-26 11:16:33,564 | ERROR | [SinkRunner-PollingRunner-DefaultSinkProcessor] | operation the
hdfs file errors. | org.apache.flume.sink.hdfs.HDFSEventSink.process(HDFSEventSink.java:414)
2019-02-26 11:16:33,747 | WARN | [hdfs-CCCC-call-runner-4] | A failover has occurred since the start
of call #32795 ClientNamenodeProtocolTranslatorPB.getFileInfo over
192-168-13-88/192.168.13.88:25000 | org.apache.hadoop.io.retry.RetryInvocationHandler
$ProxyDescriptor.failover(RetryInvocationHandler.java:220)
2019-02-26 11:16:33,748 | ERROR | [hdfs-CCCC-call-runner-4] | execute hdfs error. {} |
org.apache.flume.sink.hdfs.HDFSEventSink$3.call(HDFSEventSink.java:744)
java.net.ConnectException: Call From 192-168-12-221/192.168.12.221 to 192-168-13-88:25000 failed
on connection exception: java.net.ConnectException: Connection refused; For more details see: http://
wiki.apache.org/hadoop/ConnectionRefused

2. HDFS Sink未启动。

查看Flume运行日志，发现“ flume current metrics”中并没有Sink信息：2019-02-26 11:46:05,501 | INFO | [pool-22-thread-1] | flume current metrics:{"CHANNEL.BBBB":{"ChannelCapacity":"10000","ChannelFillPercentage":"0.0","Type":"CHANNEL","ChannelStoreSize":"0","EventProcessTimedelta":"0","EventTakeSuccessCount":"0","ChannelSize":"0","EventTakeAttemptCount":"0","StartTime":"1551152734999","EventPutAttemptCount":"0","EventPutSuccessCount":"0","StopTime":"0"},"SOURCE.AAAA":
{"AppendBatchAcceptedCount":"0","EventAcceptedCount":"0","AppendReceivedCount":"0","MonTime":"0","StartTime":"1551152735503","AppendBatchReceivedCount":"0","EventReceivedCount":"0","Type":"SOURCE","TotalFilesCount":"1001","SizeAcceptedCount":"0","UpdateTime":"605410241202740","AppendAcceptedCount":"0","OpenConnectionCount":"0","MovedFilesCount":"1001","StopTime":"0"}} |org.apache.flume.node.Application.getRestartComps(Application.java:467)

### 解决办法

步骤1 若Flume数据写入的组件未启动，启动对应组件；若组件异常，请联系服务技术支持。

步骤2 Sink未启动，检查配置文件是否配置正确，若配置错误，则正确修改配置文件后重启Flume进程，如果配置正确，则查看日志错误信息，根据具体错误信息制定解决办法。

----结束

## 11.5 Flume 服务端进程故障

### 问题现象

Flume运行一段时间后，Manager界面Flume实例显示运行状态“故障”。

### 原因分析

Flume文件或文件夹权限异常，重启后Manager界面提示如下信息：

[2019-02-26 13:38:02]RoleInstance prepare to start failure [{ScriptExecutionResult=ScriptExecutionResult [exitCode=126, output=, errMsg=sh: line 1: /opt/Bigdata/MRS_XXX/install/FusionInsight-Flume-1.9.0/ flume/bin/flume-manage.sh: Permission denied

### 解决办法

与运行正常的Flume节点进行文件和文件夹权限对比，更改错误文件或文件夹权限。
----结束

## 11.6 Flume 数据采集慢

### 问题现象

Flume启动后，Flume数据采集慢。

### 原因分析

1. Flume堆内存设置不合理，导致Flume进程一直处于频繁GC。查看Flume运行日志：2019-02-26T13:06:20.666+0800: 1085673.512: [Full GC:[CMS: 3849339k->3843458K(3853568K),2.5817610 secs] 4153654K->3843458K(4160256K), [CMS Perm : 27335K->27335K(45592K),2.5820080SECS] [Times: user=2.63, sys0.00, real=2.59 secs]

2. 用户业务配置的Spooldir source的deletePolicy策略是立即删除（immediate）。

### 解决办法

步骤1 适当调大堆内存（xmx）的值。

步骤2 将Spooldir source的deletePolicy策略更改为永不删除（never）。

----结束

## 11.7 Flume 启动失败

### 问题现象

安装Flume服务或重启Flume服务失败。

### 原因分析

1. Flume堆内存设置的值大于机器剩余内存，查看Flume启动日志：[CST 2019-02-26 13:31:43][INFO] [[checkMemoryValidity:124]] [GC_OPTS is invalid:Xmx(40960000MB) is bigger than the free memory(56118MB) in system.] [9928]

2. Flume文件或文件夹权限异常，界面或后台会提示如下信息：[2019-02-26 13:38:02]RoleInstance prepare to start failure[{ScriptExecutionResult=ScriptExecutionResult [exitCode=126, output=, errMsg=sh: line 1: /opt/Bigdata/MRS_XXX/install/FusionInsight-Flume-1.9.0/flume/bin/flume-manage.sh: Permission denied

3. JAVA_HOME配置错误，查看Flume agent启动日志：Info: Sourcing environment configuration script /opt/FlumeClient/fusioninsight-flume-1.9.0/conf/flume-env.sh+ '[' -n '' ']' + 'T' -n " ]'

+ exec /tmp/MRS-Client/MRS_Flume_ClientConfig/JDK/jdk-8u18/bin/java '-
XX:OnOutOfMemoryError=bash /opt/FlumeClient/fusioninsight-flume-1.9.0/bin/
out_memory_error.sh /opt/FlumeClient/fusioninsight-flume-1.9.0/conf %p' -Xms2G -Xmx4G -
XX:CMSFullGCsBeforeCompaction=1 -XX:+UseConcMarkSweepGC -XX:+CMSParallelRemarkEnabled -
XX:+UseCMSCompactAtFullCollection -Dkerberos.domain.name=hadoop.hadoop.com -verbose:gc -
XX:+UseGCLogFileRotation -XX:NumberOfGCLogFiles=10 -XX:GCLogFileSize=1M -XX:+PrintGCDetails -
XX:+PrintGCDateStamps -Xloggc:/var/log/Bigdata//flume-client-1/flume/flume-root-20190226134231-
%p-gc.log -Dproc_org.apache.flume.node.Application -Dproc_name=client -Dproc_conf_file=/opt/
FlumeClient/fusioninsight-flume-1.9.0/conf/properties.properties -Djava.security.krb5.conf=/opt/
FlumeClient/fusioninsight-flume-1.9.0/conf//krb5.conf -Djava.security.auth.login.config=/opt/
FlumeClient/fusioninsight-flume-1.9.0/conf//jaas.conf -Dzookeeper.server.principal=zookeeper/
hadoop.hadoop.com -Dzookeeper.request.timeout=120000 -Dflume.instance.id=884174180 -
Dflume.agent.name=clientName1 -Dflume.role=client -Dlog4j.configuration.watch=true -
Dlog4j.configuration=log4j.properties -Dflume_log_dir=/var/log/Bigdata//flume-client-1/flume/ -
Dflume.service.id=flume-client-1 -Dbeetle.application.home.path=/opt/FlumeClient/fusioninsight
flume-1.9.0/conf/service -Dflume.called.from.service -Dflume.conf.dir=/opt/FlumeClient/fusioninsight
flume-1.9.0/conf -Dflume.metric.conf.dir=/opt/FlumeClient/fusioninsight-flume-1.9.0/conf -
Dflume.script.home=/opt/FlumeClient/fusioninsight-flume-1.9.0/bin -cp '/opt/FlumeClient/
fusioninsight-flume-1.9.0/conf:/opt/FlumeClient/fusioninsight-flume-1.9.0/lib/*:/opt/FlumeClient/
fusioninsight-flume-1.9.0/conf/service/' -Djava.library.path=/opt/FlumeClient/fusioninsight-flume-1.9.0
plugins.d/native/native org.apache.flume.node.Application --conf-file /opt/FlumeClient/fusioninsight
flume-1.9.0/conf/properties.properties --name client
/opt/FlumeClient/fusioninsight-flume-1.9.0/bin/flume-ng: line 233: /tmp/FusionInsight-Client/Flume/
FusionInsight_Flume_ClientConfig/JDK/jdk-8u18/bin/java: No such file or directory

### 解决办法

步骤1 适当调大堆内存（xmx）的值。

步骤2 与正常启动Flume的节点进行文件和文件夹权限对比，更改错误文件或文件夹权限。

步骤3 重新配置JAVA_HOME。

客户端替换“${install_home}/fusioninsight-flume-flume组件版本号/conf/ENV_VARS文件中JAVA_HOME”的值，服务端替换“etc”目录下“ENV_VARS”文件中“JAVA_HOME”的值。

其中“JAVA_HOME”的值可通过登录正常启动Flume的节点，执行echo ${JAVA_HOME}获取。

### 说明

${install_home}为Flume客户端的安装路径。

----结束
