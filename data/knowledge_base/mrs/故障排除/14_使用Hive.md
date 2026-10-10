

## 14.1 Hive 常见日志说明

### 审计日志

对于审计日志来说，记录了某个时间点某个用户从哪个IP发起对HiveServer或者MetaStore的请求以及记录执行的语句是什么。

如下的HiveServer审计日志，表示在2016-02-01 14:51:22 用户user_chen向HiveServer发起了show tables请求，客户端IP为192.168.1.18。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/ebe6f684bb0d34bbf55697a928179aece9270c05616c97d2c01bd1e40db9bacf.jpg)

如下的MetaStore审计日志，表示在2016-01-29 11:31:15 用户hive向MetaStore发起shutdown请求，客户端ip为192.168.1.18。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/731b7f5dd66aae893686a2c6a697e53e87bfa994709682ab1062e37597375a10.jpg)

在遇到诸如下述类问题时，需要查看审计日志：

1. 如客户端发起请求，但是未得到响应。由于不确定任务是卡在客户端还是服务端，可以通过审计日志查看。如果审计日志根本没有相关信息，那么说明任务终止在客户端；如果审计日志有相关信息打印，那么就需要去运行日志里进一步定位原因。

2. 查看指定时间段的任务请求个数，可通过审计日志查看在指定时间段有多少个请求。

### HiveServer 运行日志

HiveServer负责接收客户端请求（SQL语句），然后编译、执行（提交到YARN或运行Local MR）、与MetaStore交互获取元数据信息等。HiveServer运行日志记录了一个SQL完整的执行过程。

通常情况下，当遇到SQL语句运行失败，首先需要查看HiveServer运行日志。

### MetaStore 运行日志

通常情况下，当遇到查看HiveServer运行日志时，如遇到MetaException或者连接MetaStore失败，则需要查看MetaStore运行日志。

### GC 日志查看

HiveServer和MetaStore均有GC日志，当遇到GC问题可以查看GC日志以快速定位是否是GC导致。例如遇到HiveServer或MetaStore频繁重启就需要去看下对应的GC日志。
----结束

## 14.2 Hive 服务启动失败

Hive服务启动失败最常见的原因是metastore实例无法连接上DBservice，可以查看metastore日志中具体的错误信息。

### 可能原因

1. DBservice没有初始化好Hive的元数据库hivemeta。

2. DBservice的浮动IP配置有误，导致metastore节点IP无法正确连接浮动IP，或者是在与该ip建立互信的时候失败导致metastore启动失败。

处理步骤 1

步骤1 执行以下命令：source /opt/Bigdata/MRS_XXX/install/dbservice/.dbservice_profilegsql -h DBservice浮动IP地址 -p 20051 -d hivemeta -U hive -W hive用户密码

步骤2 如果不能正确进入交互界面，说明数据库初始化失败。如果报如下错误说明在DBservice所在的节点的配置文件可能丢失了hivemeta的配置。org.postgresql.util.PSQLException: FATAL: no pg_hba.conf entry for host "192.168.0.146", database"HIVEMETA"。

步骤3 编辑“/srv/BigData/dbdata_service/data/pg_hba.conf”，在文件最后面追加hosthivemeta hive 0.0.0.0/0 sha256配置。

步骤4 执行source /opt/Bigdata/MRS_XXX/install/dbservice/.dbservice_profile命令配置环境变量。

步骤5 执行gs_ctl -D $GAUSSDATA reload #命令使修改后的配置生效。

----结束

处理步骤 2

DBservice的浮动IP配置需要同网段内没有被使用过的IP，也就是在配置前ping不通的IP，请修改DBService浮动IP配置。
----结束

## 14.3 安全集群执行 set 命令的时候报错“Cannot modifyxxx at runtime”

### 问题现象

执行set命令时报以下错误：

0: jdbc:hive2://192.168.1.18:21066/> set mapred.job.queue.name=QueueA;
Error: Error while processing statement: Cannot modify mapred.job.queue.name at list of params that are allowed to be modified at runtime (state=42000,code=1)

### 处理步骤

方案1：

步骤1 登录Manager界面，修改Hive参数。

MRS Manager界面操作：登录MRS Manager页面，选择“服务管理 > Hive > 服务配置 > 全部配置 > HiveServer > 安全”。

FusionInsight Manager界面操作：登录FusionInsight Manager页面，选择“集群 > 服务 > Hive > 配置 > 全部配置 > HiveServer > 安全”。

步骤2 将需要执行的命令参数添加到配置项

“hive.security.authorization.sqlstd.confwhitelist.append”中。

步骤3 单击保存并重启HiveServer后即可。如下图所示：

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/acd3e4fec4cc180a1f45242e916d875b32899bacc185c79f8c8e5a1524caa977.jpg)

方案2：

步骤1 登录Manager界面，修改Hive参数。

MRS Manager界面操作：登录MRS Manager页面，选择“服务管理 > Hive > 服务配置 > 全部配置 > HiveServer > 安全”。

FusionInsight Manager界面操作：登录FusionInsight Manager页面，选择“集群 > 服务 > Hive > 配置 > 全部配置 > HiveServer > 安全”。

步骤2 找到选项“hive.security.whitelist.switch”，选择“OFF”，单击保存并重启HiveServer即可。

----结束

## 14.4 提交Hive任务时如何指定队列？

### 问题现象

怎样在Hive提交任务的时候指定队列？

### 处理步骤

步骤1 在执行语句前通过如下参数设置任务队列，例如，提交任务至队列QueueA。

set mapred.job.queue.name=QueueA;

select count(*) from rc;

说明

队列的名称区分大小写，如写成queueA，Queuea均无效；且该队列为叶子队列，不支持提交任务到非叶子队列。

步骤2 提交任务后，可在Yarn页面看到，如下任务已经提交到队列QueueA。

User: admin
Name: select count(*) from rc(Stage-1)
Àpplication Type: MAPREDUCE
Application Tags:
YarnApplicationState: FINISHED
Queue: QueueA
FinalStatus Reported by AM: SUCCEEDED
Started: Thu Mar 03 09:01:58 +0800 2016
Elapsed: 1mins, Osec
Tracking URL: History
Log Aggregation Status Status
Diagnostics:

----结束

## 14.5 怎么通过客户端设置 Map/Reduce 内存？

### 问题现象

客户端怎么设置Map/Reduce内存？

### 处理步骤

Hive在执行SQL语句前，可以通过set命令来设置Map/Reduce相关客户端参数。

以下为与Map/Reduce内存相关的参数：

set mapreduce.map.memory.mb=4096;// 每个Map Task需要的内存量
set mapreduce.map.java.opts=-Xmx3276M; // 每个Map Task 的JVM最大使用内存
set mapreduce.reduce.memory.mb=4096; // 每个Reduce Task需要的内存量
set mapreduce.reduce.java.opts=-Xmx3276M; // 每个Reduce Task 的JVM最大使用内存
set mapred.child.java.opts=-Xms1024M -Xmx3584M;//此参数为全局参数，即对Map和Reduce统一设置

### 说明

参数设置只对当前session有效。
----结束

## 14.6 如何在导入 Hive 表时指定输出的文件压缩格式？

### 问题现象

如何在导入Hive表时指定输出的文件压缩格式？

### 处理步骤

当前Hive支持以下几种压缩格式：

org.apache.hadoop.io.compress.BZip2Codec
org.apache.hadoop.io.compress.Lz4Codec
org.apache.hadoop.io.compress.DeflateCodec
org.apache.hadoop.io.compress.SnappyCodec
org.apache.hadoop.io.compress.GzipCodec

如需要全局设置，即对所有表都进行压缩，可以在Manager页面对Hive的服务配置参数进行如下全局配置：

– hive.exec.compress.output设置为true

mapreduce.output.fileoutputformat.compress.codec设置为org.apache.hadoop.io.compress.BZip2Codec

说明

hive.exec.compress.output参数必须设置为true，才能使下边的参数选项生效。

● 如需在session级设置，只需要在执行命令前增加如下设置即可：

set hive.exec.compress.output=true;

set

mapreduce.output.fileoutputformat.compress.codec=org.apache.hadoop.i o.compress.SnappyCodec;
----结束

## 14.7 Hive 表 desc 描述过长导致无法完整显示

### 问题现象

desc描述表过长时，如何让描述显示完整？

（可选）
-u <database url> the JDBC URL to connect to
-n <username> the username to connect as
-p <password> the password to connect as
-d <driver class> the driver class to use
-i <init file> script file for initialization
-e <query> query that should be executed
-f <exec file> script file that should be executed
--hiveconf property=value Use value for given property
--color=[true/false] control whether color is used for display
--showHeader=[true/false] show column names in query results
--headerInterval=ROWS; the interval between which heades are displayed
--fastConnect=[true/false] skip building table/column list for tab-completion
--autoCommit=[true/false] enable/disable automatic transaction commit
--verbose=[true/false] show verbose error messages and debug info
--showWarnings=[true/false] display connection warnings
--showNestedErrs=[true/false] display nested errors
--numberFormat=[pattern] format numbers using DecimalFormat pattern
--force=[true/false] continue running script even after errors
--maxWidth=MAXWIDTH the maximum width of the terminal
--maxColumnWidth=MAXCOLWIDTH the maximum width to use when displaying columns
--silent=[true/false] be more silent
--autosave=[true/false] automatically save preferences
--outputformat=[table/vertical/csv2/tsv2/dsv/csv/tsv] format mode for result display
Note that csv, and tsv are deprecated - use csv2, tsv2 instead
--truncateTable=[true/false] truncate table column when it exceeds length
--delimiterForDSV=DELIMITER specify the delimiter for delimiter-separated values output format
(default: |)
--isolation=LEVEL set the transaction isolation level
--nullemptystring=[true/false] set to true to get historic behavior of printing null as empty string
--socketTimeOut=n socket connection timeout interval, in second. The default value is 300.

### 处理步骤

步骤1 启动Hive的beeline时，设置参数maxWidth=20000即可，例如：[root@192-168-1-18 logs]# beeline --maxWidth=20000scan complete in 3msConnecting toBeeline version 1.1.0 by Apache Hive

----结束

## 14.8 Hive 表中增加分区列后再插入数据显示为 NULL

### 问题现象

create table test_table(
col1 string,
col2 string
PARTITIONED BY(p1 string)
STORED AS orc tblproperties('orc.compress'='SNAPPY');

2. 修改表结构，添加分区并插入数据alter table test_table add partition(p1='a');insert into test_table partition(p1='a') select col1,col2 from temp_table;

3. 修改表结构，添加列并插入数据alter table test_table add columns(col3 string);insert into test_table partition(p1='a') select col1,col2,col3 from temp_table;

4. 查询test_table表数据，返回结果中列col3的值全为NULLselect * from test_table where p1='a'

5. 新添加表分区，并插入数据alter table test_table add partition(p1='b');insert into test_table partition(p1='b') select col1,col2,col3 from temp_table;

6. 查询test_table表数据，返回结果中列col3有不为NULL的值select * from test_table where p1='b

### 原因分析

在alter table时默认选项为RESTRICT，RESTRICT只会更改元数据，不会修改此操作之前创建的partition的表结构，而只会修改之后创建的新的partition，所以查询时旧的partition中的值全为NULL。

### 处理步骤

add column时加入cascade关键字即可，例如：alter table test_table add columns(col3 string) cascade;
----结束

## 14.9 集群中创建的新用户执行查询Hive操作时无权限

### 问题现象

创建了新用户，但是执行查询的时候报无权限的错。

Error: Error while compiling statement: FAILED: HiveAccessControlException Permission denied: Principal [name=hive, type=USER] does not have following privileges for operation QUERY [[SELECT] on Object [type=TABLE_OR_VIEW, name=default.t1]] (state=42000,code=40000)

### 原因分析

创建的新用户没有Hive组件的操作权限。

### 解决方案

MRS Manager界面操作：

步骤1 登录MRS Manager页面，选择“系统配置 > 角色管理 > 添加角色”。

步骤2 输入角色名称。

步骤3 在“权限”区域选择Hive，出现Hive管理员权限和Hive表的读写权限。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/2f8d8474a8aed5561a8d78f0250aff5d7ca7ed7387c428a995d009c680792cfd.jpg)

步骤4 选择“Hive Read Write Privileges”Hive表的读写权限，此时显示列Hive中的所有数据库。

步骤5 勾选角色需要的权限并单击“确定”完成角色创建。

步骤6 在MRS Manager页面，选择“系统配置 > 用户管理”。

步骤7 在已创建的新用户对应的“操作”列单击“修改”。

步骤8 单击“选择添加的用户组”，如需使用Hive服务，必须添加Hive组。

步骤9 单击“选择并绑定角色”，勾选步骤5中已创建的角色。

步骤10 单击“确定”完成用户权限的配置。

----结束

FusionInsight Manager界面操作：

步骤1 登录FusionInsight Manager。选择“系统 > 权限 > 角色”。

步骤2 单击“添加角色”，输入“角色名称”和“描述”。

步骤3 设置角色“配置资源权限”，选择“Hive读写权限”Hive表的读写权限，此时显示列Hive中的所有数据库。

步骤4 勾选角色需要的权限并单击“确定”完成角色创建。

步骤5 在FusionInsight Manager页面，选择“系统 > 权限 > 用户”。

步骤6 在已创建的新用户对应的“操作”列单击“修改”。

步骤7 单击“用户组”右侧的“添加”，如需使用Hive服务，必须添加Hive组。

步骤8 单击“角色”右侧的“添加”，勾选4中已创建的角色。

步骤9 单击“确定”完成用户权限的配置。

----结束

## 14.10 执行 SQL 提交任务到指定队列时报错

### 问题现象

执行SQL提交任务到Yarn报如下错误：

Failed to submit application_1475400939788_0033 to YARN :
org.apache.hadoop.security.AccessControlException: User newtest cannot submit applications to queue
root.QueueA

### 原因分析

当前登录的用户无YARN队列提交权限。

### 解决方案

用户无YARN队列提交权限，需要赋予YARN相应队列的提交权限。在Manager页面的“系统 >权限 > 用户”中给用户绑定队列提交权限的角色。
----结束

## 14.11 执行 load data inpath 命令报错

### 问题现象

执行load data inpath报如下错误：

错误1：
HiveAccessControlException Permission denied. Principal [name=user1, type=USER] does not have
following privileges on Object [type=DFS_URI, name=hdfs://hacluster/tmp/input/mapdata] for
operation LOAD : [OBJECT OWNERSHIP]

● 错误2：

HiveAccessControlException Permission denied. Principal [name=user1, type=USER] does not have following privileges on Object [type=DFS_URI, name=hdfs://hacluster/tmp/input/mapdata] for operation LOAD : [INSERT, DELETE]

● 错误3：

SemanticException [Error 10028]: Line 1:17 Path is not legal ''file:///tmp/input/mapdata'': Move from: file:/tmp/input/mapdata to: hdfs://hacluster/user/hive/warehouse/tmp1 is not valid. Please check that values for params "default.fs.name" and "hive.metastore.warehouse.dir" do not conflict.

### 原因分析

当前登录的用户不具备操作此目录的权限或者文件目录格式不正确。

### 解决方案

Hive对load data inpath命令有如下权限要求，请对照下述要求是否满足：

● 文件的owner需要为执行命令的用户。

● 当前用户需要对该文件有读、写权限。

● 当前用户需要对该文件的目录有执行权限。

由于load操作会将该文件移动到表对应的目录中，所以要求当前用户需要对表的对应目录有写权限。

要求文件的格式与表指定的存储格式相同。如创建表时指定stored as rcfile，但是文件格式为txt，则不符合要求。

● 文件必须是HDFS上的文件，不可以用file://的形式指定本地文件系统上的文件。

● 文件名不能以下横线（_）或点（.）开头，以这些开头的文件会被忽略。

如下所示，如果用户test_hive load数据，正确的权限如下：

[root@192-168-1-18 duan]# hdfs dfs -ls /tmp/input2
16/03/21 14:45:07 INFO hdfs.PeerCache: SocketCache disabled.
Found 1 items
-rw-r--r-- 3 test_hive hive 6 2016-03-21 14:44 /tmp/input2/input.txt
----结束

## 14.12 执行 load data local inpath 命令报错

### 问题现象

执行load data local inpath报如下错误：

● 错误1：

HiveAccessControlException Permission denied. Principal [name=user1, type=USER] does not have following privileges on Object [type=LOCAL_URI, name=file:/tmp/input/mapdata] for operation LOAD : [SELECT, INSERT, DELETE]

● 错误2：

HiveAccessControlException Permission denied. Principal [name=user1, type=USER] does not have following privileges on Object [type=LOCAL_URI, name=file:/tmp/input/mapdata] for operation LOAD : [OBJECT OWNERSHIP]

● 错误3：

SemanticException Line 1:23 Invalid path ''/tmp/input/mapdata'': No files matching path file:/tmp/ input/mapdata

### 原因分析

当前登录的用户不具备操作此目录的权限或者在HiveServer所在节点上没有此目录。

### 解决方案

### 说明

通常不建议使用本地文件加载数据到hive表。 建议先将本地文件放入HDFS，然后从集群中加载数据。

Hive对load data local inpath命令有如下权限要求，请对照下述要求是否满足：

● 由于所有的命令都是发送到主HiveServer上去执行的，所以要求此文件在HiveServer节点上。

HiveServer进程是以操作系统上的omm用户启动的，所以要求omm用户对此文件有读权限，对此文件的目录有读、执行权限。

● 文件的owner需要为执行命令的用户。

● 当前用户需要对该文件有读、写权限。

要求文件的格式与表指定的存储格式相同。如创建表时指定stored as rcfile，但是文件格式为txt，则不符合要求。

● 文件名不能以下横线（_）或点（.）开头，以这些开头的文件会被忽略。
----结束

## 14.13 执行 create external table 命令报错

### 问题现象

执行命令：create external table xx(xx int) stored as textfile location '/tmp/aaa/aaa'，报以下错误：

Permission denied. Principal [name=fantasy, type=USER] does not have following privileges on Object [type=DFS_URI, name=/tmp/aaa/aaa] for operation CREATETABLE : [SELECT, INSERT, DELETE, OBJECT OWNERSHIP] (state=42000,code=40000)

### 原因分析

当前登录的用户不具备该目录或者其父目录的读写权限。创建外部表时，会判断当前用户对指定的目录以及该目录下其它目录和文件是否有读写权限，如果该目录不存在，会去判断其父目录，依次类推。如果一直不满足就会报权限不足。而不是报指定的目录不存在。

### 解决方案

请确认当前用户为路径“/tmp/aaa/aaa”的owner有读写权限，如果该路径不存在，确认对其父路径有读写权限。
----结束

## 14.14 在 beeline 客户端执行 dfs -put 命令报错

### 问题现象

执行命令：

dfs -put /opt/kv1.txt /tmp/kv1.txt

报以下错误：

Permission denied. Principal [name=admin, type=USER] does not have following privileges onObject[type=COMMAND_PARAMS,name=[-put, /opt/kv1.txt, /tmp/kv1.txt]] for operation DFS : [ADMIN PRIVILEGE] (state=,code=1)

### 原因分析

当前登录的用户不具备操作此命令的权限。

### 解决方案

如果登录的当前用户具有admin角色，请用set role admin来切换成admin角色操作。
如果不具备admin角色，在Manager页面中给用户绑定对应角色的权限。
----结束

## 14.15 执行 set role admin 命令报无权限

### 问题现象

执行命令：

set role admin

报下述错误：

0: jdbc:hive2://192.168.42.26:21066/> set role admin; Error: Error while processing statement: FAILED: Execution Error, return code 1 from org.apache.hadoop.hive.ql.exec.DDLTask. dmp_B doesn't belong to role admin (state=08S01,code=1)

### 原因分析

当前登录的用户不具有Hive的admin角色的权限。

### 解决方案

步骤1 登录Manager。

● MRS 3.x之前版本，执行步骤7。

MRS 3.x及之后版本，选择“集群 > 服务 > Hive”，在服务“概览”页面右上角单击“更多”，查看“启用Ranger鉴权”是否置灰。

– 是，执行步骤2。

– 否，执行步骤7。

步骤2 选择“集群 > 服务 > Ranger”，单击“基本信息”区域中的“RangerAdmin”，进入Ranger WebUI界面。

步骤3 单击右上角用户名后，选择“Log Out”，退出当前用户后使用rangeradmin用户登录。

步骤4 在首页中单击“Settings”，选择“Roles”。

步骤5 单击“Role Name”为“admin”的角色，在“Users”区域，单击“Select User”，选择指定用户名。

步骤6 单击Add Users按钮，在对应用户名所在行勾选“Is Role Admin”，单击“Save”保存配置，操作结束。

步骤7 选择“系统 > 权限 > 角色”，添加一个拥有Hive管理员权限的角色。

步骤8 在FusionInsight Manager页面，选择“系统 > 权限 > 用户 ”。

步骤9 在指定用户对应的“操作”列单击“修改”。

步骤10 为用户绑定拥有Hive管理员权限的角色，并单击“确定”完成权限添加。

----结束

## 14.16 在 beeline 客户端创建 UDF 时报错

### 问题现象

执行命令：

create function fn_test3 as 'test.MyUDF' using jar 'hdfs:///tmp/udf2/ MyUDF.jar'

报以下错误：

Error: Error while compiling statement: FAILED: HiveAccessControlException Permission denied: Principal [name=admin, type=USER] does not have following privileges for operation CREATEFUNCTION [[ADMIN PRIVILEGE] on Object [type=DATABASE, name=default], [ADMIN PRIVILEGE] on Object [type=FUNCTION, name=default.fn_test3]] (state=42000,code=40000)

### 原因分析

Hive中创建永久函数需要特殊的role admin。

### 解决方案

在执行语句前执行set role admin命令即可解决。
----结束

## 14.17 Hive服务状态为故障如何处理

### 可能原因

● DBservice服务不可用会导致Hive服务状态为Bad。

● HDFS服务不可用会导致Hive服务状态为Bad。

● ZooKeeper服务不可用会导致Hive服务状态为Bad。

● LDAP/KrbServer服务不可用会导致Hive服务状态为Bad。

● MetaStore实例不可用会导致Hive服务状态为Bad。

### 解决方案

● DBservice服务不可用请参考ALM-27001 DBService服务不可用。

● HDFS服务不可用请参考ALM-14000 HDFS服务不可用。

● ZooKeeper服务不可用请参考ALM-13000 ZooKeeper服务不可用。

LDAP/KrbServer服务不可用请参考ALM-25000 LdapServer服务不可用/ALM-25500 KrbServer服务不可用。

MetaStore实例不可用请参考ALM-16004 Hive服务不可用。
----结束

## 14.18 Hive服务健康状态和Hive实例健康状态的区别

### 问题现象

Hive服务健康状态和Hive实例健康状态的区别是什么？

### 解决方案

Hive服务的健康状态（也就是在Manager界面看到的健康状态）有Good，Bad，Partially Healthy，Unknown四种状态 ，四种状态除了取决于Hive本身服务的可用性（会用简单的SQL来检测Hive服务的可用性），还取决于Hive服务所依赖的其他组件的服务状态。

Hive实例分为Hiveserver和Metastore两种，健康状态有Good，Concerning ，Unknown三种状态，这三种状态是通过jmx通信来判定，与实例通信正常时为Good，通信异常时为Concerning，无法通信时为Unknown。
----结束

## 14.19 Shell 客户端连接提示“authentication failed”

### 问题现象

安全集群中，HiveServer服务正常的情况下，Shell客户端中执行beeline命令失败，界面提示“authentication failed”，如下：

Debug is true storeKey false useTicketCache true useKeyTab false doNotPrompt false ticketCache is null
isInitiator true KeyTab is null refreshKrb5Config is false principal is null tryFirstPass is false useFirstPass is
false storePass is false clearPass is false
Acquire TGT from Cache
Credentials are no longer valid
Principal is null
null credentials from Ticket Cache
[Krb5LoginModule] authentication failed
No password provided

### 可能原因

● 客户端用户没有进行安全认证

● kerberos认证超期

### 解决方案

步骤1 登录Hive客户端所在节点。

步骤2 执行source 集群客户端安装目录/bigdata_env命令。

可通过klist命令查看本地是否有有效票据，如下信息表明票据在16年12月24日14:11:42生效，将在16年12月25日14:11:40失效。此期间内可以使用该票据，其他时间则该票据无效。

klist
Ticket cache: FILE:/tmp/krb5cc_0
Default principal: xxx@HADOOP.COM
Valid starting Expires Service principal
12/24/16 14:11:42 12/25/16 14:11:40 krbtgt/HADOOP.COM@HADOOP.COM

步骤3 执行kinit username进行认证，然后再使用客户端。

----结束

## 14.20 客户端提示访问 ZooKeeper 失败

### 问题现象

安全集群中，HiveServer服务正常的情况下，通过jdbc接口连接HiveServer执行sql时报出ZooKeeper认证异常"The ZooKeeper client is AuthFailed"，如下：

14/05/19 10:52:00 WARN utils.HAClientUtilDummyWatcher: The ZooKeeper client is AuthFailed
14/05/19 10:52:00 INFO utils.HiveHAClientUtil: Exception thrown while reading data from znode.The possible reason may be connectionless. This is recoverable. Retrying..
14/05/19 10:52:16 WARN utils.HAClientUtilDummyWatcher: The ZooKeeper client is AuthFailed 14/05/19 10:52:32 WARN utils.HAClientUtilDummyWatcher: The ZooKeeper client is AuthFailed 14/05/19 10:52:32 ERROR st.BasicTestCase: Exception: Could not establish connection to active hiveserver java.sql.SQLException: Could not establish connection to active hiveserver

或者报出无法读取"Hiveserver2 configs from ZooKeeper"，如下：

Exception in thread "main" java.sql.SQLException: org.apache.hive.jdbc.ZooKeeperHiveClientException:
Unable to read HiveServer2 configs from ZooKeeper
at org.apache.hive.jdbc.HiveConnection.<init>(HiveConnection.java:144)
at org.apache.hive.jdbc.HiveDriver.connect(HiveDriver.java:105)
at java.sql.DriverManager.getConnection(DriverManager.java:664)
at java.sql.DriverManager.getConnection(DriverManager.java:247)
at JDBCExample.main(JDBCExample.java:82)
Caused by: org.apache.hive.jdbc.ZooKeeperHiveClientException: Unable to read HiveServer2 configs from
ZooKeeper
at
org.apache.hive.jdbc.ZooKeeperHiveClientHelper.configureConnParams(ZooKeeperHiveClientHelper.java:100)
at org.apache.hive.jdbc.Utils.configureConnParams(Utils.java:509)
at org.apache.hive.jdbc.Utils.parseURL(Utils.java:429)
at org.apache.hive.jdbc.HiveConnection.<init>(HiveConnection.java:142)
... 4 more
Caused by: org.apache.zookeeper.KeeperException$ConnectionLossException: KeeperErrorCode =
ConnectionLoss for /hiveserver2
at org.apache.zookeeper.KeeperException.create(KeeperException.java:99)
at org.apache.zookeeper.KeeperException.create(KeeperException.java:51)
at org.apache.zookeeper.ZooKeeper.getChildren(ZooKeeper.java:2374)
at org.apache.curator.framework.imps.GetChildrenBuilderImpl$3.call(GetChildrenBuilderImpl.java:214)
at org.apache.curator.framework.imps.GetChildrenBuilderImpl$3.call(GetChildrenBuilderImpl.java:203)
at org.apache.curator.RetryLo，op.callWithRetry(RetryLoop.java:107)
at
org.apache.curator.framework.imps.GetChildrenBuilderImpl.pathInForeground(GetChildrenBuilderImpl.java:2
00)
at org.apache.curator.framework.imps.GetChildrenBuilderImpl.forPath(GetChildrenBuilderImpl.java:191)
at org.apache.curator.framework.imps.GetChildrenBuilderImpl.forPath(GetChildrenBuilderImpl.java:38)

### 可能原因

客户端连接HiveServer时，HiveServer的地址是从ZooKeeper中自动获取，当ZooKeeper连接认证异常时，无法从ZooKeeper中获取正确的HiveServer地址。

在连接zookeeper认证时，需要客户端传入krb5.conf，principal，keytab等相关信息。认证失败有如下几种：

– user.keytab路径写错。

– user.principal写错。

– 集群做过切换域名操作但客户端拼接url时使用旧的principal。

有防火墙相关设置，导致客户端本身无法通过kerberos认证，Kerberos需要开放的端口有21730(TCP)、21731(TCP/UDP)、21732(TCP/UDP)。

### 解决方案

步骤1 确保用户可以正常读取客户端节点相关路径下的user.keytab文件。

步骤2 确保用户的user.principal与指定的keytab文件对应。

可通过klist -kt keytabpath/user.keytab查看。

步骤3 如果集群有做过切换域名操作，需要保证url中使用的principal字段是新域名。

如默认为hive/hadoop.hadoop.com@HADOOP.COM，当集群有切换域名的操作时，该字段需要进行相关修改。如域名为abc.com时，则此处应填写hive/hadoop.abc.com@ABC.COM。

步骤4 确保可以正常的认证连接HiveServer。

在客户端执行以下命令

source 客户端安装目录/bigdata_env

kinit username

然后再使用客户端执行beeline，确保可以正常运行。

----结束

## 14.21 使用 UDF 函数时提示“Invalid function”

### 问题现象

在Hive客户端中使用Spark创建UDF函数时，报出"ERROR 10011","invalid function"的异常，如下：

Error: Error while compiling statement: FAILED: SemanticException [Error 10011]: Line 1:7 Invalid function 'test_udf' (state=42000,code=10011)

在多个HiveServer之间使用UDF也存在上述问题。例如，在HiveServer1中使用HiveServer2创建的UDF，如果不及时同步元数据信息，连接HiveServer1的客户端也会提示上述错误信息。

### 可能原因

多个HiveServer之间或者Hive与Spark之间共用的元数据未同步，导致不同HiveServer实例内存数据不一致，造成UDF不生效。

### 解决方案

需要将新建的UDF信息同步到HiveServer中，执行reload function操作即可。
----结束

## 14.22 Hive 服务状态为 Unknown

### 问题现象

Hive服务状态为unknown。

### 可能原因

Hive服务停止。

### 解决方案

尝试重启Hive服务。
----结束

## 14.23 HiveServer 或者 MetaStore 实例的健康状态为unknown

### 问题现象

HiveServer或者MetaStore实例的健康状态为unknown。

### 可能原因

HiveServer或者MetaStore实例被停止。

解决方案

重启HiveServer或者MetaStore实例。
----结束

## 14.24 HiveServer 或者 MetaStore 实例的健康状态为Concerning

### 问题现象

HiveServer或者MetaStore实例的健康状态为Concerning。

### 可能原因

HiveServer或者MetaStore实例在启动的时候发生异常，无法正常启动。如，当修改MetaStore/HiveServer GC参数时，可通过查看对应进程的启动日志，如hiveserver.out(hadoop-omm-jar-192-168-1-18.out)文件排查。 如下异常：

Error: Could not find or load main class Xmx2048M

说明java虚拟机启动时，将Xmx2048M作为java进程的启动参数而不是JVM的启动参数了，如下将符号‘-’误删掉。

METASTORE_GC_OPTS=Xms1024M Xmx2048M -DIgnoreReplayReqDetect -XX\:CMSFullGCsBeforeCompaction\=1 -XX\:+UseConcMarkSweepGC -XX\:+CMSParallelRemarkEnabled -XX\:+UseCMSCompactAtFullCollection -XX\:+ExplicitGCInvokesConcurrent -server -XX\:MetaspaceSize\=128M -XX\:MaxMetaspaceSize\=256M

### 解决方案

因此遇到此类异常应该检查最近的变更项，以确认是否配置有误。

METASTORE_GC_OPTS=Xms1024M -Xmx2048M -DIgnoreReplayReqDetect -XX\:CMSFullGCsBeforeCompaction\=1 -XX\:+UseConcMarkSweepGC

-XX\:+CMSParallelRemarkEnabled -XX\:+UseCMSCompactAtFullCollection -XX\:+ExplicitGCInvokesConcurrent -server -XX\:MetaspaceSize\=128M -XX\:MaxMetaspaceSize\=256M
----结束

## 14.25 TEXTFILE 类型文件使用 ARC4 压缩时查询结果乱码

### 问题现象

Hive查询结果表做压缩存储（ARC4），对结果表做select * 查询时返回结果为乱码。

### 可能原因

Hive默认压缩格式不是ARC4格式或者未开启输出压缩。

### 解决方案

步骤1 在select结果乱码时，在beeline中进行如下设置。

set
mapreduce.output.fileoutputformat.compress.codec=org.apache.hadoop.io.enc ryption.arc4.ARC4BlockCodec;
set hive.exec.compress.output=true;

步骤2 使用块解压的方式先将表导入一个新表中。insert overwrite table tbl_result select * from tbl_source;

步骤3 再进行查询。select * from tbl_result;----结束
----结束

## 14.26 Hive 任务运行过程中失败，重试成功

### 问题现象

当Hive任务在正常运行时失败，在客户端报出错误，类似的错误打印：

Error:Invalid OperationHandler:OperationHandler [opType=EXECUTE_STATEMENT,getHandleIdentifier()=XXX](state=,code=0)

而此任务提交到Yarn上的MapReduce任务运行成功。

[0: jdbc:hive2://189.120.204.104:21066/> select count(*) from test1;
INFo : Number of reduce taaks determined at, conpile tine: l
INFO : In order to change the average load for a reducer (in bytes):
INFO set hive.exec.reducers.bytes.per.reducer=<number>
INFO : In order to limit the naximum number of reducers:
INFO
INFO : In order to set a constant number of reducers:
INFO set mapreduce.job.reduces=<number>
INF0 : number of splits:l
INFO : Submitting tokens for 1ob: job 1484563934624 0003
INF0 : Kind: HDFS_DELEGATION_TOKEN, Service: ha-hdfs:hacluster, Ident: (HDFS_DELEGATION_TOKEN token 7 for admin)
INF0 : Kind: HIVE DELEGATION TOKEN, Service: HiveServer2ImpersonationToken, Ident: 00 05 61 64 6d 69 6e 05 61 64 6d 69 6e 21 68 69 76 65 2f 68 61 64 6f 6f 70 2e 68 85 ce e4 8a 01 59 ce 92 52 e4 8e 07 d8 0c
INF0 : The ur1 to track the job: https://189-120-204-104:26001/proxy/application 1484563934624 0003/
INFO : Starting Job = job_1484563934624_0003, Tracking URL = https://189-120-204-104:26001/proxy/application_1484563934624_0003/
INFO : Kil1 Command = /opt 3igdata/FusionInsight-Hive-1.1.0/hadoop/bin/hadoop job -ki11 job_1484563934624_0003
INFO : Hadoop job information for Stage-l: number of mappers: 1: number of reducers: 1
INF0 : 2017-01-17 11:46:12,579 Stage-1 map = 0%, reduce = 0÷
INF0 : 2017-01-17 11:46:23,243 Stage-1 map = 100%, reduce = 0, Cumulative CPU 2.32 sec
Error: Invalid OperationHandle: OperationHandle [opType=EXECUTE STATEMENT, getHandleIdentifier()=386323de-dfla-4299-826e-96368d4baf80] (state=,code=0) 0:jdbc:hive2://189.120.204.215:21066/>

### 原因分析

出错的集群有两个HiveServer实例，首先查看其中一个HiveServer日志发现里面的报错与客户端中的错误一样均是Error:Invalid OperationHandler，查看另一个HiveServer发现在出错的时间段此实例有如下类似START_UP的打印，说明那段时间进程被停止过，后来又启动成功，提交的任务本来连接的是重启过的HiveServer实例，当这个实例被停止后，任务进程连接到另一个健康的HiveServer上导致报错。
2017-02-15 14:40:11,309 | INFO | main | STARTUP_MSG:
/**********************
STARTUP_MSG: Starting HiveServer2
STARTUP_MSG: host = XXX-120-85-154/XXX.120.85.154
STARTUP_MSG: args = []
STARTUP_MSG: version = 1.3.0

### 解决办法

重新提交一次任务即可，保证在任务执行期间不手动重启HiveServer进程。
----结束

## 14.27 执行 select 语句时报错“Execution Error returncode 2”

### 问题现象

执行语句select count(*) from XXX;时客户端报错：

Error:Error while processing statement :FAILED:Execution Error,return code 2 from ...

这个报错return code2说明是在执行mapreduce任务期间报错导致任务失败。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/1355ed21fb03cc6f858df9b6031f4abd8d011f477b44d8070a80e1997571afb9.jpg)

### 原因分析

1. 进入Yarn原生页面查看MapReduce任务的日志看到报错是无法识别到压缩方式导致错误，看文件后缀是gzip压缩，堆栈却报出是zlib方式。

2017-01-18 16:22:07,566 INF0 lmain org. apache.hadoop.hive. q1.exec. MapOperator: 4 Close done
2017-01-18 16:22:07,572 WARN [main] org.apache.hadoop.mapred. YarnChild: Exception running child : java.io.IOException: java.io. I0Exception: unknowm compression method at oxg. apache. hadoop.hive. io. HiveIOExceptionHandlexChain. handleRecordReaderNextException(HiveIOExceptionHandlerChain. java:121) at oxg.apache.hadoop.hive.io. HiveIOExceptionHandlerUtil.handleRecordReaderNextException(HiveIOExceptionHandlerUtil. java:77) at oxg-apache.hadoop.hive. ql.io. HiveContextäwareRecordReader. doNext (HiveContextAvareRecordReader. java:355) at org. apache.hadoop.hive. ql.io. HiveRecordReader. doNext (HiveRecordReader. java:79) at org, apache, hadoop, hive, al. io. HiveRecordReader, doNext (HiveRecordReader, java: 33) at org.apache.hadoop. hive. ql.io. HiveContextäwareRecordReader.next (HiveContextAwareRecordReader. java:116) at oxg, apache, hadoop, mapred, MapTask$TrackedRecordReader, moveToNext (MapTask, java: 199) at org. apache. hadoop.mapred. MapTask$TrackedRecordReader. next (MapTask. java: 185) at org. apache. hadoop. mapred. MapRunner. run(MapRunner. java: 52) at org. apache. hadoop. mapred. MapTask. run0ldMapper (MapTask. java:453) at org. apache. hadoop. mapred. MapTask. run(MapTask. java:343) at oxg. apache.hadoop.mapred. YarnChild$2.run(YarnChild. java:180) at java, security. AccessController, doPrivileged(Native Method) at javax. security. auth. Subject. doäs (Subject. java:422) at oxg- apache. hadoop. security.UserGroupInformation. doás (UserGroupInfoxnation. java:1726) at oxg. apache.hadoop.mapred. YarnChild. nain(YarnChild. java:174)
Caused by: java.io. I0Exception: unknowm compression method at oxg.apache.hadoop.io.compress.zlib.ZlibDecompressor.inflateBytesDirect(Native Method) at oxg.apache.hadoop.io. compress.zlib.ZlibDecompressor. decompress(ZlibDecompressor. java:225) at oxg.apache.hadoop.io.compress.DecompressorStream.decompress(DecompressorStrean.java:91) at org, apache, hadoop, io, compress, DeconpressorStream, read(DeconpressorStream, iava:85 at java.io. InputStream.read(InputStrean. java:101) at oxg. apache.hadoop.util.LineReader. fillBuffex (LineReader. java:180) at oxg.apache.hadoop.util.LineReader.xreadDefaultLine(LineReader.java:216) at oxg.apache.hadoop.util.LineReader.xeadLine (LineReader. java:174) at org-apache. hadoop.mapred. LineRecordReader.next (LineRecordReader. java:248) at org- apache. hadoop.mapred.LineRecordReader.next (LineRecordReader. java:48) at org. apache. hadoop. hive, gl. io. HiveContextåwareRecordReader. doNext (HiveContextAvareRecordReader. java: 350) ... 13 more

2. 因此怀疑此语句查询的表对应的HDFS上的文件有问题，Map日志中打印出了解析的对应的文件名，将其从HDFS上下载到本地，看到是gz结尾的文件，使用tar命令解压报错，格式不正确无法解压。使用file命令查看文件属性发现此文件来自于FAT系统的压缩而非UNIX。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/3354a9df16928c6e4b073ff52ecd8c45a474e2b3122b2a3c7977fef28d82e885.jpg)

### 解决办法

将格式不正确的文件移出HDFS目录或者替换为正确的格式的文件。
----结束

## 14.28 有大量分区时执行 drop partition 操作失败

问题背景与现象

执行drop partitions操作，执行异常：

MetaStoreClient lost connection. Attempting to reconnect. |
org.apache.hadoop.hive.metastore.RetryingMetaStoreClient.invoke(RetryingMetaStoreClient.java:187)
org.apache.thrift.transport.TTransportException
at org.apache.thrift.transport.TIOStreamTransport.read(TIOStreamTransport.java:132)
at org.apache.thrift.transport.TTransport.xxx(TTransport.java:86)
at org.apache.thrift.transport.TSaslTransport.readLength(TSaslTransport.java:376)
at org.apache.thrift.transport.TSaslTransport.readFrame(TSaslTransport.java:453)
at org.apache.thrift.transport.TSaslTransport.read(TSaslTransport.java:435)

查看对应MetaStore日志，有StackOverFlow异常：

2017-04-22 01:00:58,834 | ERROR | pool-6-thread-208 | java.lang.StackOverflowError at org.datanucleus.store.rdbms.sql.SQLText.toSQL(SQLText.java:330) at org.datanucleus.store.rdbms.sql.SQLText.toSQL(SQLText.java:339) at org.datanucleus.store.rdbms.sql.SQLText.toSQL(SQLText.java:339) at org.datanucleus.store.rdbms.sql.SQLText.toSQL(SQLText.java:339) at org.datanucleus.store.rdbms.sql.SQLText.toSQL(SQLText.java:339)

### 原因分析

drop partition的处理逻辑是将找到所有满足条件的分区，将其拼接起来，最后统一删除。由于分区数过多，拼删元数据堆栈较深，出现StackOverFlow异常。

### 解决办法

分批次删除分区。
----结束

## 14.29 执行 join 操作时 localtask 启动失败

问题背景与现象

1. 执行join等操作，数据量较小时，会启动localtask执行，执行过程会报错：
jdbc:hive2://10.*.*.*:21066/> select a.name ,b.gender from student a join student1 b on (a.name =
b.name);
ERROR : Execution failed with exit status: 1
ERROR : Obtaining error information
ERROR :
Task failed!
Task ID:
Stage-4
Error: Error while processing statement: FAILED: Execution Error, return code 1 from
org.apache.hadoop.hive.ql.exec.mr.MapredLocalTask (state=08S01,code=1)

2. 查看对应HiveServer日志，发现是启动localtask失败：2018-04-25 16:37:19,296 | ERROR | HiveServer2-Background-Pool: Thread-79 | Execution failed withexit status: 1 | org.apache.hadoop.hive.ql.session.SessionState$LogHelper.printError(SessionState.java:1016)2018-04-25 16:37:19,296 | ERROR | HiveServer2-Background-Pool: Thread-79 | Obtaining errorinformation | org.apache.hadoop.hive.ql.session.SessionState$LogHelper.printError(SessionState.java:1016)2018-04-25 16:37:19,297 | ERROR | HiveServer2-Background-Pool: Thread-79 |Task failed!Task ID:Stage-4Logs:| org.apache.hadoop.hive.ql.session.SessionState$LogHelper.printError(SessionState.java:1016)2018-04-25 16:37:19,297 | ERROR | HiveServer2-Background-Pool: Thread-79 | /var/log/Bigdata/hive/hiveserver/hive.log | org.apache.hadoop.hive.ql.session.SessionState$LogHelper.printError(SessionState.java:1016)2018-04-25 16:37:19,297 | ERROR | HiveServer2-Background-Pool: Thread-79 | Execution failed withexit status: 1 |org.apache.hadoop.hive.ql.exec.mr.MapredLocalTask.executeInChildVM(MapredLocalTask.java:342)2018-04-25 16:37:19,309 | ERROR | HiveServer2-Background-Pool: Thread-79 | FAILED: ExecutionError, return code 1 from org.apache.hadoop.hive.ql.exec.mr.MapredLocalTask |org.apache.hadoop.hive.ql.session.SessionState$LogHelper.printError(SessionState.java:1016)2018-04-25 16:37:36,438 | ERROR | HiveServer2-Background-Pool: Thread-88 | Error running hivequery: | org.apache.hive.service.cli.operation.SQLOperation$1$1.run(SQLOperation.java:248)org.apache.hive.service.cli.HiveSQLException: Error while processing statement: FAILED: ExecutionError, return code 1 from org.apache.hadoop.hive.ql.exec.mr.MapredLocalTaskat org.apache.hive.service.cli.operation.Operation.toSQLException(Operation.java:339)at org.apache.hive.service.cli.operation.SQLOperation.runQuery(SQLOperation.java:169)at org.apache.hive.service.cli.operation.SQLOperation.access$200(SQLOperation.java:75)at org.apache.hive.service.cli.operation.SQLOperation$1$1.run(SQLOperation.java:245)at java.security.AccessController.doPrivileged(Native Method)at javax.security.auth.Subject.doAs(Subject.java:422)at org.apache.hadoop.security.UserGroupInformation.doAs(UserGroupInformation.java:1710)at org.apache.hive.service.cli.operation.SQLOperation$1.run(SQLOperation.java:258)at java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:511)at java.util.concurrent.FutureTask.run(FutureTask.java:266)

at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1142) at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:617) at java.lang.Thread.run(Thread.java:745)

3. 查看对应HiveServer日志目录（/var/log/Bigdata/hive/hiveserver）下的hs_err_pid_*****.log，发现有内存不够的错误：

\# There is insuficient memory for the Java Runtime Environment to continue. # Native memory allocation (mmap) failed to map 20776943616 bytes for committing reserved memory.

### 原因分析

Hive在执行join操作，数据量小时会生成MapJoin，执行MapJoin时会生成localtask任务，localtask启动的jvm内存继承了父进程的内存。

当有多个join执行的时候，启动多个localtask，如果机器内存不够，就会导致启动localtask失败。

### 解决办法

步骤1 进入Hive服务配置页面：

MRS 3.x之前版本，单击集群名称，登录集群详情页面，选择“组件管理 > Hive> 服务配置”，单击“基础配置”下拉菜单，选择“全部配置”。

说明

如果集群详情页面没有“组件管理”页签，请先完成IAM用户同步（在集群详情页的“概览”页签，单击“IAM用户同步”右侧的“同步”进行IAM用户同步）。

MRS 3.x及后续版本，登录FusionInsight Manager，然后选择“集群 > 待操作的称 > 服务 > Hive > 配置 > 全部配置”。

步骤2 搜索“hive.auto.convert.join”参数并修改hive的配置hive.auto.convert.join为false，保存配置并重启服务。

该参数修改后会对业务性能有一定影响。继续执行后续步骤可不影响业务性能。

步骤3 搜索“HIVE_GC_OPTS”参数并修改，把Xms调小，具体要根据业务评估，最小设置为Xmx的一半，修改完后保存配置并重启服务。

----结束

## 14.30 修改 hostname 后导致 WebHCat 启动失败

问题背景与现象

用户修改hostname导致WebHCat启动失败。

查看对应节点WebHCat启动日志（ /var/log/Bigdata/hive/webhcat/hive.log），发现报如下错误：

org-apache hadoon.security-authentication.client AuthenticationExcention: GssExcention: No valid credentials provided (Mechanism level:
at org.apache.hadoop.hive.om.utils.WebHCatAuthenticator.doSpnegoSequence(WebHCatAuthenticator.java:302)
at org.apache.hadoop.hive.om.utils.webkcatAuthenticator.authenticate(webkcatAuthenticator.java:149)
at org.apache.hadoop.hive.cm.monitor.WebHcatHealthChecker.renewToken(WebHCatHealthChecker.java:186)
at org.apache.hadoop.hive.cm.monitor.WebHCatHealthChecker.checkwebHCat(WebHCatHealthChecker.java:119)
at org.apache.hadoop.hive.om.monitor.WebHCatHealthChecker.run(webHCatHealthChecker.iava:168)
Caused by: GssException: No valid credentials provided (Mechanism level: Server not found in Kerberos database (7) UNKNOWN SERVER)
at sun.security.igss.GssContextImpl.initsecContext(GsscontextImpl.iava:248)
at sun.security.jgss.GssContextImpl.initsecContext(GssContextImpl.java:179)
at org.apache.hadoop.hive.cm.utils.WebHCatAuthenticators1.run(webHCatAuthenticator.iava:277
at org.apache.hadoop.hive.om.utils.WebHCatAuthenticator$1.run(webHCatAuthenticator.java:253)
at iava.security.Accesscontroller.doPrivileged(Native Method)
at javax.security.auth.Subject.doAs(Subject.java:422)
at sun.security.krb5.KrbTgsReq.getReply(KrbTgsReq.java:251)
at sun.security.krb5.KrbTgsReq.sendAndGetCreds(KrbTgsReq.java:262)
at sun.security.krb5.Credentials.acquireServiceCreds(Credentials.java:458)
at sun.security.igss.krb5.Krb5context.initsecContext(Krb5context.java:693)
at sun.security.krb5.internal.KDCRep.init(KDCRep.java:140)

### 原因分析

1. MRS WebHCat角色的服务端账户中涉及到hostname，如果安装完集群后再修改hostname，就会导致启动失败。

2. “/etc/hosts”中配置了一对多或者多对一的主机名和IP对应关系，导致在执行hostname和hostname -i获取不到正确的IP和hostname。

### 解决办法

步骤1 将修改了节点的hostname全部修改为集群初始的hostname。

步骤2 排查WebHCat所在节点的“/etc/hosts”是否配置正确。

步骤3 重启WebHCat。

----结束

## 14.31 集群修改域名后Hive 样例程序运行报错

问题背景与现象

Hive的二次开发代码样例运行报No rules applied to ****的错误：

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/696e06bb3ae14436e2ebd4ef0dc95592c99cee5d504f5cf47a4676c2c7fc52a2.jpg)

### 原因分析

1. Hive的二次开发样例代码会加载core-site.xml，此文件默认是通过classload加载，所以使用的时候要把此配置文件放到启动程序的classpath路径下面。

2. 如果修改了集群的域名，那么core-site.xml将发生变化，需要下载最新的core-site.xml并放入到打包hive二次开发样例代码进程的classpath路径下面。

解决办法

步骤1 下载集群Hive最新的客户端，获取最新的“core-site.xml”。

步骤2 将core-site.xml放入到打包Hive二次开发样例代码进程的classpath路径下面。

----结束

## 14.32 DBService 超过最大连接数后导致 Hive MetaStore异常

问题背景与现象

业务量较大导致DBService连接数超过了默认的最大值（可查看DBService的“dbservice.database.max.connections”参数获取），MetaStore出现异常，并报错“slots are reserved for non-replication superuser connections”：

2018-04-26 14:58:55,657 | ERROR | BoneCP-pool-watch-thread | Failed to acquire connection to
jdbc:postgresql://10.*.*.*:20051/hivemeta?socketTimeout=60. Sleeping for 1000 ms. Attempts left: 9 |
com.jolbox.bonecp.BoneCP.obtainInternalConnection(BoneCP.java:292)
org.postgresql.util.PSQLException: FATAL: remaining connection slots are reserved for non-replication
superuser connections at org.postgresql.core.v3.ConnectionFactoryImpl.readStartupMessages(ConnectionFactoryImpl.java:643) at org.postgresql.core.v3.ConnectionFactoryImpl.openConnectionImpl(ConnectionFactoryImpl.java:184) at org.postgresql.core.ConnectionFactory.openConnection(ConnectionFactory.java:64) at org.postgresql.jdbc2.AbstractJdbc2Connection.<init>(AbstractJdbc2Connection.java:124) at org.postgresql.jdbc3.AbstractJdbc3Connection.<init>(AbstractJdbc3Connection.java:28) at org.postgresql.jdbc3g.AbstractJdbc3gConnection.<init>(AbstractJdbc3gConnection.java:20) at org.postgresql.jdbc4.AbstractJdbc4Connection.<init>(AbstractJdbc4Connection.java:30) at org.postgresql.jdbc4.Jdbc4Connection.<init>(Jdbc4Connection.java:22) at org.postgresql.Driver.makeConnection(Driver.java:392) at org.postgresql.Driver.connect(Driver.java:266) at java.sql.DriverManager.getConnection(DriverManager.java:664) at java.sql.DriverManager.getConnection(DriverManager.java:208) at com.jolbox.bonecp.BoneCP.obtainRawInternalConnection(BoneCP.java:361) at com.jolbox.bonecp.BoneCP.obtainInternalConnection(BoneCP.java:269) at com.jolbox.bonecp.ConnectionHandle.<init>(ConnectionHandle.java:242) at com.jolbox.bonecp.PoolWatchThread.fillConnections(PoolWatchThread.java:115) at com.jolbox.bonecp.PoolWatchThread.run(PoolWatchThread.java:82) at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1142) at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:617) at java.lang.Thread.run(Thread.java:745)

### 原因分析

业务量大导致DBService的连接数超过了最大值，需要修改DBService的最大连接数。

### 解决办法

步骤1 进入DBService服务配置页面：

MRS 3.x之前版本，单击集群名称，登录集群详情页面，选择“组件管理 >DBService > 服务配置”，单击“基础配置”下拉菜单，选择“全部配置”。

说明

如果集群详情页面没有“组件管理”页签，请先完成IAM用户同步（在集群详情页的“概览”页签，单击“IAM用户同步”右侧的“同步”进行IAM用户同步）。

MRS 3.x及后续版本，登录FusionInsight Manager，然后选择“集群 > 服务 >DBService > 配置 > 全部配置”。

步骤2 搜索“dbservice.database.max.connections”配置项，并根据实际情况适当调大“dbservice.database.max.connections”配置的值。

该参数是数据库服务中用于配置数据库最大并发连接数的核心参数，用于限制同时连接到DBService的客户端数量上限。

配置该参数需结合实际业务场景，不能盲目设置过大或过小，主要从以下几点进行考虑：

● 节点资源配置：内存越大、CPU核心数越多，可支持的最大连接数通常越高。

业务并发量：高峰时段的客户端并发请求数是核心关注指标，需确保参数值略高于实际高峰并发量，避免正常业务被拒绝。

单连接的资源消耗：如果每个数据库连接对应的业务操作（如复杂查询、大事务）消耗资源较多，需适当降低最大连接数，反之可适当提高。

步骤3 保存配置，并重启受影响的服务或者实例。

步骤4 如果调整完还报超过最大连接数，需要排查业务代码，是否有连接泄露。

----结束

## 14.33 beeline 客户端报错“Failed to execute sessionhooks: over max connections”

问题背景与现象

HiveServer连接的最大连接数默认为200，当超过200时，beeline会报Failed toexecute session hooks: over max connections：

beeline> [root@172-27-16-38 c70client]# beeline

jdbc:hive2://129.188.82.38:24002,129.188.82.36:24002,129.188.82.35:24002/;serviceDiscoveryMode=zooKeepe r;zooKeeperNamespace=hiveserver2;sasl.qop=auth-conf;auth=KERBEROS;principal=hive/ hadoop.hadoop.com@HADOOP.COM

Debug is true storeKey false useTicketCache true useKeyTab false doNotPrompt false ticketCache is null isInitiator true KeyTab is null refreshKrb5Config is false principal is null tryFirstPass is false useFirstPass is false storePass is false clearPass is false

Acquire TGT from Cache

Principal is xxx@HADOOP.COM

Commit Succeeded

Error: Failed to execute session hooks: over max connections. (state=,code=0)

Beeline version 1.2.1 by Apache Hive

查看HiveServer日志（/var/log/Bigdata/hive/hiveserver/hive.log）报over maxconnections错误：

2018-05-03 04:31:56,728 | WARN | HiveServer2-Handler-Pool: Thread-137 | Error opening session: |
org.apache.hive.service.cli.thrift.ThriftCLIService.OpenSession(ThriftCLIService.java:542)
org.apache.hive.service.cli.HiveSQLException: Failed to execute session hooks: over max connections. at org.apache.hive.service.cli.session.SessionManager.openSession(SessionManager.java:322) at org.apache.hive.service.cli.CLIService.openSessionWithImpersonation(CLIService.java:189) at org.apache.hive.service.cli.thrift.ThriftCLIService.getSessionHandle(ThriftCLIService.java:663) at org.apache.hive.service.cli.thrift.ThriftCLIService.OpenSession(ThriftCLIService.java:527) at org.apache.hive.service.cli.thrift.TCLIService$Processor$OpenSession.getResult(TCLIService.java:1257) at org.apache.hive.service.cli.thrift.TCLIService$Processor$OpenSession.getResult(TCLIService.java:1242) at org.apache.thrift.ProcessFunction.process(ProcessFunction.java:39) at org.apache.thrift.TBaseProcessor.process(TBaseProcessor.java:39) at org.apache.hadoop.hive.thrift.HadoopThriftAuthBridge$Server
$TUGIAssumingProcessor.process(HadoopThriftAuthBridge.java:710)

at org.apache.thrift.server.TThreadPoolServer$WorkerProcess.run(TThreadPoolServer.java:286)
at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1142)
at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:617)
at java.lang.Thread.run(Thread.java:745)
Caused by: org.apache.hive.service.cli.HiveSQLException: over max connections.
at
org.apache.hadoop.hive.transporthook.SessionControllerTsaslTransportHook.checkTotalSessionNumber(Sessi
onControllerTsaslTransportHook.java:208)
at
org.apache.hadoop.hive.transporthook.SessionControllerTsaslTransportHook.postOpen(SessionControllerTsasl
TransportHook.java:163)
at
org.apache.hadoop.hive.transporthook.SessionControllerTsaslTransportHook.run(SessionControllerTsaslTransp
ortHook.java:134)
at org.apache.hive.service.cli.session.SessionManager.executeSessionHooks(SessionManager.java:432)
at org.apache.hive.service.cli.session.SessionManager.openSession(SessionManager.java:314)
. 12 more

### 原因分析

业务量大导致连接HiveServer单个节点最大连接数超过了200，需要调大连接HiveServer实例的最大连接数。

### 解决办法

步骤1 进入Hive服务配置页面：

MRS 3.x之前版本，单击集群名称，登录集群详情页面，选择“组件管理 > Hive> 服务配置”，单击“基础配置”下拉菜单，选择“全部配置”。

说明

如果集群详情页面没有“组件管理”页签，请先完成IAM用户同步（在集群详情页的“概览”页签，单击“IAM用户同步”右侧的“同步”进行IAM用户同步）。

MRS 3.x及后续版本，登录FusionInsight Manager，然后选择“集群 > 服务 >Hive > 配置 > 全部配置”。

步骤2 搜索hive.server.session.control.maxconnections配置项，并修改hive.server.session.control.maxconnections配置的值到合适值，不能超过1000。

步骤3 保存配置并重启受影响的服务或者实例。

----结束

## 14.34 beeline 客户端报错“OutOfMemoryError”

问题背景与现象

beeline客户端查询大量数据时，报OutOfMemoryError：Java heap space，具体报错信息如下：

org.apache.thrift.TException: Error in calling method FetchResults at org.apache.hive.jdbc.HiveConnection$SynchronizedHandler.invoke(HiveConnection.java:1514) at com.sun.proxy.$Proxy4.FetchResults(Unknown Source) at org.apache.hive.jdbc.HiveQueryResultSet.next(HiveQueryResultSet.java:358) at org.apache.hive.beeline.BuferedRows.<init>(BuferedRows.java:42) at org.apache.hive.beeline.BeeLine.print(BeeLine.java:1856) at org.apache.hive.beeline.Commands.execute(Commands.java:873) at org.apache.hive.beeline.Commands.sql(Commands.java:714) at org.apache.hive.beeline.BeeLine.dispatch(BeeLine.java:1035) at org.apache.hive.beeline.BeeLine.execute(BeeLine.java:821)

<table><tr><td>at org.apache.hive.beeline.BeeLine.begin(BeeLine.java:778) at org.apache.hive.beeline.BeeLine.mainWithInputRedirection(BeeLine.java:486) at org.apache.hive.beeline.BeeLine.main(BeeLine.java:469) Caused by: java.lang.OutOfMemoryError: Java heap space at com.sun.crypto.provider.CipherCore.doFinal(CipherCore.java:959) at com.sun.crypto.provider.CipherCore.doFinal(CipherCore.java:824) at com.sun.crypto.provider.AESCipher.engineDoFinal(AESCipher.java:436) at javax.crypto.Cipher.doFinal(Cipher.java:2223) at sun.security.krb5.internal.crypto.dk.AesDkCrypto.decryptCTS(AesDkCrypto.java:414) at sun.security.krb5.internal.crypto.dk.AesDkCrypto.decryptRaw(AesDkCrypto.java:291) at sun.security.krb5.internal.crypto.Aes256.decryptRaw(Aes256.java:86) at sun.security.jgss.krb5.CipherHelper.aes256Decrypt(CipherHelper.java:1397) at sun.security.jgss.krb5.CipherHelper.decryptData(CipherHelper.java:576) at sun.security.jgss.krb5.WrapToken_v2.getData(WrapToken_v2.java:130) at sun.security.jgss.krb5.WrapToken_v2.getData(WrapToken_v2.java:105) at sun.security.jgss.krb5.Krb5Context.unwrap(Krb5Context.java:1058) at sun.security.jgss.GSSContextImpl.unwrap(GSSContextImpl.java:403) at com.sun.security.sasl.gsskerb.GssKrb5Base.unwrap(GssKrb5Base.java:77) at org.apache.thrift.transport.TSaslTransport$SaslParticipant.unwrap(TSaslTransport.java:559) at org.apache.thrift.transport.TSaslTransport.readFrame(TSaslTransport.java:462) at org.apache.thrift.transport.TSaslTransport.read(TSaslTransport.java:435) at org.apache.thrift.transport.TSaslClientTransport.read(TSaslClientTransport.java:37) at org.apache.thrift.transport.TTransport.xxx(TTransport.java:86) at org.apache.hadoop.hive.thrift.TFilterTransport.xxx(TFilterTransport.java:62) at org.apache.thrift.protocol.TBinaryProtocol.xxx(TBinaryProtocol.java:429) at org.apache.thrift.protocol.TBinaryProtocol.readI32(TBinaryProtocol.java:318) at org.apache.thrift.protocol.TBinaryProtocol.readMessageBegin(TBinaryProtocol.java:219) at org.apache.thrift.TServiceClient.receiveBase(TServiceClient.java:77)</td></tr></table>

### 原因分析

● 客户查询大量数据，数据量过大。

客户在检索数据时使用select * from table_name;，进行全表查询，表内数据过多。

beeline默认启动内存128M，查询时返回结果集过大，导致beeline无法承载导致。

### 解决办法

步骤1 执行select count(*) from table_name;前确认需要查询的数据量大小，确认是否需要在beeline中显示如此数量级的数据。

步骤2 如数量在一定范围内需要显示，请调整hive客户端的jvm参数， 在hive客户端目录/Hive下的component_env中添加export HIVE_OPTS=-Xmx1024M（具体数值请根据业务调整），并重新执行source 客户端目录/bigdata_env配置环境变量。

----结束

## 14.35 输入文件数超出设置限制导致任务执行失败

问题背景与现象

Hive执行查询操作时报Job Submission failed with exception'java.lang.RuntimeException(input file number exceeded the limits in theconf;input file num is: 2380435,max heap memory is: 16892035072,the limit confis: 500000/4)'，此报错中具体数值根据实际情况会发生变化，具体报错信息如下：

ERROR : Job Submission failed with exception 'java.lang.RuntimeException(input file numbers exceeded the
limits in the conf;
input file num is: 2380435 ,
max heap memory is: 16892035072 ,
the limit conf is: 500000/4)'
java.lang.RuntimeException: input file numbers exceeded the limits in the conf;
input file num is: 2380435 ,
max heap memory is: 16892035072 ,
the limit conf is: 500000/4 at org.apache.hadoop.hive.ql.exec.mr.ExecDriver.checkFileNum(ExecDriver.java:545) at org.apache.hadoop.hive.ql.exec.mr.ExecDriver.execute(ExecDriver.java:430) at org.apache.hadoop.hive.ql.exec.mr.MapRedTask.execute(MapRedTask.java:137) at org.apache.hadoop.hive.ql.exec.Task.executeTask(Task.java:158) at org.apache.hadoop.hive.ql.exec.TaskRunner.runSequential(TaskRunner.java:101) at org.apache.hadoop.hive.ql.Driver.launchTask(Driver.java:1965) at org.apache.hadoop.hive.ql.Driver.execute(Driver.java:1723) at org.apache.hadoop.hive.ql.Driver.runInternal(Driver.java:1475) at org.apache.hadoop.hive.ql.Driver.run(Driver.java:1283) at org.apache.hadoop.hive.ql.Driver.run(Driver.java:1278) at org.apache.hive.service.cli.operation.SQLOperation.runQuery(SQLOperation.java:167) at org.apache.hive.service.cli.operation.SQLOperation.access$200(SQLOperation.java:75) at org.apache.hive.service.cli.operation.SQLOperation$1$1.run(SQLOperation.java:245) at java.security.AccessController.doPrivileged(Native Method) at javax.security.auth.Subject.doAs(Subject.java:422) at org.apache.hadoop.security.UserGroupInformation.doAs(UserGroupInformation.java:1710) at org.apache.hive.service.cli.operation.SQLOperation$1.run(SQLOperation.java:258) at java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:511) at java.util.concurrent.FutureTask.run(FutureTask.java:266) at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1142) at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:617) at java.lang.Thread.run(Thread.java:745)

Error: Error while processing statement: FAILED: Execution Error, return code 1 from org.apache.hadoop.hive.ql.exec.mr.MapRedTask (state=08S01,code=1)

### 原因分析

MapReduce任务提交前对输入文件数的检查策略：在提交的MapReduce任务中，允许的最大输入文件数和HiveServer最大堆内存的比值，例如500000/4（默认值），表示每4GB堆内存最大允许500000个输入文件。在输入的文件数超出此限制时则会发生此错误。

### 解决办法

步骤1 进入Hive服务配置页面：

MRS 3.x之前版本，单击集群名称，登录集群详情页面，选择“组件管理 > Hive> 服务配置”，单击“基础配置”下拉菜单，选择“全部配置”。

说明

如果集群详情页面没有“组件管理”页签，请先完成IAM用户同步（在集群详情页的“概览”页签，单击“IAM用户同步”右侧的“同步”进行IAM用户同步）。

MRS 3.x及后续版本，登录FusionInsight Manager，然后选择“集群 > 服务 >Hive > 配置 > 全部配置”。

步骤2 搜索hive.mapreduce.input.files2memory配置项，并修改hive.mapreduce.input.files2memory配置的值到合适值，根据实际内存和任务情况对此值进行调整。

步骤3 保存配置并重启受影响的服务或者实例。

步骤4 如调整后问题仍未解决，请根据业务情况调整HiveServer的GC参数至合理的值。

----结束

## 14.36 Hive任务执行中报栈内存溢出导致任务执行失败

问题背景与现象

Hive执行查询操作时报错Error running child : java.lang.StackOverflowError，具体报错信息如下：

FATAL [main] org.apache.hadoop.mapred.YarnChild: Error running child : java.lang.StackOverflowError at org.apache.hive.come.esotericsoftware.kryo.io.Input.readVarInt(Input.java:355) at

org.apache.hive.come.esotericsoftware.kryo.util.DefautClassResolver.readName(DefautClassResolver.java:127) at

org.apache.hive.come.esotericsoftware.kryo.util.DefautClassResolver.readClass(DefautClassResolver.java:115) at org.apache.hive.come.esotericsoftware.kryo.Kryo.readClass(Kryo.java.656)

at org.apache.hive.come.esotericsoftware.kryo.kryo.readClassAndObject(Kryo.java:767) at

org.apache.hive.come.esotericsoftware.kryo.serializers.collectionSerializer.read(CollectionSerializer.java:112)

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/baf01472b1c0537ae6b5891fce2031f5084460f5a9c22a984eb67671f1cf16af.jpg)

### 原因分析

java.lang.StackOverflowError这是内存溢出错误的一种，即线程栈的溢出，方法调用层次过多（比如存在无限递归调用）或线程栈太小都会导致此报错。

### 解决办法

通过调整mapreduce阶段的map和reduce子进程JVM参数中的栈内存解决此问题，主要涉及参数为mapreduce.map.java.opts（调整map的栈内存）和mapreduce.reduce.java.opts（调整reduce的栈内存），调整方法如下（以mapreduce.map.java.opts参数为例）。

● 临时增加map内存（只针对此次beeline生效）：

在beeline中执行如下命令set mapreduce.map.java.opts=-Xss8G;（具体数值请结合实际业务情况进行调整）。

永久增加map内存mapreduce.map.memory.mb和mapreduce.map.java.opts的值：

a. 进入Hive服务配置页面：

MRS 3.x之前版本，单击集群名称，登录集群详情页面，选择“组件管理> Hive > 服务配置”，单击“基础配置”下拉菜单，选择“全部配置”。

说明

如果集群详情页面没有“组件管理”页签，请先完成IAM用户同步（在集群详情页的“概览”页签，单击“IAM用户同步”右侧的“同步”进行IAM用户同步）。

MRS 3.x及后续版本，登录FusionInsight Manager，然后选择“集群 >称 > 服务 > Hive > 配置 > 全部配置”。

b. 在hiveserver自定义参数界面添加自定义参数mapreduce.map.java.opts及相应的值。

c. 保存配置并重启受影响的服务或者实例。

修改配置后需要保存，请注意参数在HiveServer自定义参数处修改，保存重启后生效（重启期间Hive服务不可用），请注意执行时间窗口。
----结束

## 14.37 对同一张表或分区并发覆写数据导致任务失败

问题背景与现象

Hive执行插入语句时，报错HDFS上文件或目录已存在或被清除，具体报错如下：

2019-03-1814:34:23,016|WAN|HiveServer2-Background-Pool:Thread-79606Failedtomovetotrash:hdfs:/hacluster/user/hive/warehouse/frpdb.db/w ixed costxn tmp5 f0000;Forcetodeletet.org.apache.hadoop.hie.common.FlUtils.moveToTrashFleUtils.java:651) 2019-03-1814:34:23,017INFO |HiveServer2-Background-Pol:Thread-179604Movedtotrash: hdfs://hacluster/user/hie/warehouse/fpdb.db/dw fixed cost xn temp6 f/000000 |org.apache.hadop.hie.common.FileUtils.moveToTrashFleUtils.java:644) 2019-03-1814:34:23,017EROR|HiveServer2-Background-Pool:Thread-1179606Failedtodeltehdfs:/hacluster/user/hive/warehouse/frpdb.db/dw fixed cost xn temp5 f000000org.apachehadoop.ive.common.FileUtils.moveToTrash(FleUtils.java:660) 2019-03-18 14:34:23.017 IERROR | HiveServer2-Backeround-Pool: Thread-1179606 | Failed with exception Destination directory hdfs:/hacluster/user/hive/warehouse/frpdb.db/dw fixed cost xn temp5 f has not be cleaned up.
org.apache.hadoop.hive.ql.metadata.HiveException: Destination directory hdfs://hacluster/user/hive/warehouse/frpdb.db/dw_fixed cost_xn_temp5_fhas not becleaned up
at org,apache.hadoop,hive,alL.metadata,Hive,replaceFiles(Hive.java:2974)
at org.apache.hadoop.hive.ql.metadata.Hive.loadTable(Hive.java:1664)
at org.apache.hadoop.hive.ql.exec.MoveTask.execute(MoveTask.java:374
at org.apache.hadoop.hive.gl.exec.Task.executeTask(Task.java:158)
at org anache hadoon hive al exec TaskRunner runSequential/TaskRunner java:101

### 原因分析

1. 根据HiveServer的审计日志，确认该任务的开始时间和结束时间。

2. 在上述时间区间内，查找是否有对同一张表或分区进行插入数据的操作。

3. Hive不支持对同一张表或分区进行并发覆写插入数据，这样会导致多个任务操作同一个数据临时目录，一个任务将另一个任务的数据移走，导致任务失败。

### 解决办法

修改业务逻辑，单线程插入数据到同一张表或分区。
----结束

## 14.38 Hive 任务失败，报没有 HDFS 目录的权限

问题背景与现象

Hive任务报错，提示执行用户没有HDFS目录权限：

2019-04-09 17:49:19,845 | ERROR | HiveServer2-Background-Pool: Thread-3160445 | Job Submission failed with exception 'org.apache.hadoop.security.AccessControlException(Permission denied: user=hive_quanxian, access=READ_EXECUTE, inode="/user/hive/warehouse/bigdata.db/
gd_ga_wa_swryswjl":zhongao:hive:dr

org.apache.hadoop.hdfs.server.namenode.FSPermissionChecker.checkAccessAcl(FSPermissionChecker.java:426 at org.apache.hadoop.hdfs.server.namenode.FSPermissionChecker.check(FSPermissionChecker.java:329) at

org.apache.hadoop.hdfs.server.namenode.FSPermissionChecker.checkSubAccess(FSPermissionChecker.java:30
0)
at

org.apache.hadoop.hdfs.server.namenode.FSPermissionChecker.checkPermission(FSPermissionChecker.java:24 1)at

com.xxx.hadoop.adapter.hdfs.plugin.HWAccessControlEnforce.checkPermission(HWAccessControlEnforce.java: 69)

org.apache.hadoop.hdfs.server.namenode.FSPermissionChecker.checkPermission(FSPermissionChecker.java:19 0)

org.apache.hadoop.hdfs.server.namenode.FSDirStatAndListingOp.getContentSummary(FSDirStatAndListingO p.java:135)

org.apache.hadoop.hdfs.server.namenode.NameNodeRpcServer.getContentSummary(NameNodeRpcServer.ja va:1342)

org.apache.hadoop.hdfs.protocolPB.ClientNamenodeProtocolServerSideTranslatorPB.getContentSummary(Cli
entNamenodeProtocolServerSideTranslatorPB.java:925)
at org.apache.hadoop.hdfs.protocol.proto.ClientNamenodeProtocolProtos$ClientNamenodeProtocol
$2.callBlockingMethod(ClientNamenodeProtocolProtos.java)
at org.apache.hadoop.ipc.ProtobufRpcEngine$Server$ProtoBufRpcInvoker.call(ProtobufRpcEngine.java:616)
at org.apache.hadoop.ipc.RPC$Server.call(RPC.java:973)
at org.apache.hadoop.ipc.Server$Handler$1.run(Server.java:2260)
at org.apache.hadoop.ipc.Server$Handler$1.run(Server.java:2256)
at java.security.AccessController.doPrivileged(Native Method)
at javax.security.auth.Subject.doAs(Subject.java:422)
at org.apache.hadoop.security.UserGroupInformation.doAs(UserGroupInformation.java:1781)
at org.apache.hadoop.ipc.Server$Handler.run(Server.java:2254)
)'

### 原因分析

1. 根据堆栈信息，可以看出在检查子目录的权限时失败。org.apache.hadoop.hdfs.server.namenode.FSPermissionChecker.checkSubAccess(FSPermissionChecker.java:300)

2. 检查HDFS上表目录下所有文件目录的权限，发现有一个目录权限为700（只有文件属主能够访问），确认存在异常目录。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/7c3be83a0067c453d2249d591b5eb9734c0472c105badc7552c65b8813da08ca.jpg)

### 解决办法

1. 确认该文件是否为手动异常导入，如不是数据文件或目录，删除该文件或目录。

2. 当无法删除时，建议修改文件或目录权限为770。
----结束

## 14.39 Load 数据到 Hive 表失败

问题背景与现象

用户在建表成功后，通过Load命令往此表导入数据，但导入操作中遇到如下问题：

> LOAD DATA INPATH '/user/tester1/hive-data/data.txt' INTO TABLE employees_info;
Error: Error while compiling statement: FAILED: SemanticException Unable to load data to destination table.
Error: The file that you are trying to load does not match the file format of the destination table.
(state=42000,code=40000)
.....

### 原因分析

1. 经分析，发现在建表时没有指定存储格式，所以采用了缺省存储格式RCFile。

2. 在导入数据时，被导入数据格式是TEXTFILE格式，最终导致此问题。

### 解决办法

属于应用侧问题，解决办法有多种。只要保证表所指定存储格式和被导入数据格式是一致的，可以根据实际情况采用合适方法。

● 方法1：

可以使用具有Hive表操作权限的用户在建表时指定存储格式，例如：

CREATE TABLE IF NOT EXISTS employees_info(name STRING,age INT) ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' STORED AS TEXTFILE;

指定被导入数据格式为TEXTFILE。

● 方法2：

被导入数据存储格式不能为TEXTFILE，而应为RCFile。
----结束

## 14.40 参考 Hive JDBC 代码用例开发的业务应用运行失败

问题背景与现象

用户参考Hive组件的“jdbc-examples”样例工程，完成其自身业务应用开发后，运行此应用失败。应用侧报如下异常：

2017-05-11 14:33:52.174 ERROR --- [ main] o.a.thrift.transport.TSaslTransport : SASL
negotiation failure
javax.security.sasl.SaslException: GSS initiate failed
at com.sun.security.sasl.gsskerb.GssKrb5Client.evaluateChallenge(Unknown Source)
at org.apache.thrift.transport.TSaslClientTransport.handleSaslStartMessage(TSaslClientTransport.java:94)
at org.apache.thrift.transport.TSaslTransport.open(TSaslTransport.java:271)
at org.apache.thrift.transport.TSaslClientTransport.open(TSaslClientTransport.java:37)

conf = new Configuration();

at org.apache.hadoop.hive.thrift.client.TUGIAssumingTransport$1.run(TUGIAssumingTransport.java:52)
at org.apache.hadoop.hive.thrift.client.TUGIAssumingTransport$1.run(TUGIAssumingTransport.java:49)
at java.security.AccessController.doPrivileged(Native Method)
at javax.security.auth.Subject.doAs(Unknown Source)
at org.apache.hadoop.security.UserGroupInformation.doAs(UserGroupInformation.java:1711)
at org.apache.hadoop.hive.thrift.client.TUGIAssumingTransport.open(TUGIAssumingTransport.java:49)
at org.apache.hive.jdbc.HiveConnection.openTransport(HiveConnection.java:260)
at org.apache.hive.jdbc.HiveConnection.createClient(HiveConnection.java:213)
at org.apache.hive.jdbc.HiveConnection.<init>(HiveConnection.java:178)
at org.apache.hive.jdbc.HiveDriver.connect(HiveDriver.java:105)
at java.sql.DriverManager.getConnection(Unknown Source)
at java.sql.DriverManager.getConnection(Unknown Source)
at com.xxx.bigdata.hive.example.JDBCExample.main(JDBCExample.java:107)
Caused by: org.ietf.jgss.GSSException: No valid credentials provided (Mechanism level: Failed to find any
Kerberos tgt)
at sun.security.jgss.krb5.Krb5InitCredential.getInstance(Unknown Source)
at sun.security.jgss.krb5.Krb5MechFactory.getCredentialElement(Unknown Source)
at sun.security.jgss.krb5.Krb5MechFactory.getMechanismContext(Unknown Source)
at sun.security.jgss.GSSManagerImpl.getMechanismContext(Unknown Source)
at sun.security.jgss.GSSContextImpl.initSecContext(Unknown Source)
at sun.security.jgss.GSSContextImpl.initSecContext(Unknown Source)
... 17 common frames omitted
…

### 原因分析

1. 初步分析怀疑是没有完成kerberos认证就去进行业务交互。

2. 深入分析日志发现日志上虽然有打印“com.xxx.bigdata.security.LoginUtil -Login success!!!!!!!!!!!!!!”，但没打印“org.apache.hadoop.security.UserGroupInformation : Login successful...”。分析代码，发现：

```java
*/@InterfaceAudience.Public
*/@InterfaceStability.Evolving
*/public static synchronized void loginUserFromKeytab(String user, String path)
*/throws IOException
/**/{
/*958 */if (!isSecurityEnabled()) {
/* 959 */return;
/**/ }
```

3. 分析“isSecurityEnabled()”，发现是否要发起认证，还需要判断configuration中是否有配置“hadoop.security.authentication”为“kerberos”。

本Hive业务应用确实没有正确设置此配置，所以被认为不需要做kerberos认证。分析Hive组件的“jdbc-examples”样例工程，不存在类似问题，是因为该工程的classpath路径下，存在core-site.xml配置文件，此配置文件上设置“hadoop.security.authentication”为“kerberos”。

### 解决办法

属于用户使用不当。对于本业务应用来说，若要解决此问题，可以参考如下几种办法：

- 方法1：

直接参考Hive组件的“jdbc-examples”样例工程，将core-site.xml配置文件放在classpath路径下。

● 方法2：

在代码中，显式加载配置文件core-site.xml，例如：

String userdir = System.getProperty("user.dir") + File.separator + "conf" + File.separator;
conf.addResource(new Path(userdir + "core-site.xml"));

- 方法3：

在代码中，设置“hadoop.security.authentication”为“kerberos”，例如：

......
CONF = new Configuration();
CONF.set("hadoop.security.authentication", "kerberos");
----结束

## 14.41 HiveServer 和 HiveHCat 进程故障

### 用户问题

客户集群HiveServer和WebHCat进程状态均为故障。

### 问题现象

客户MRS集群Master2节点上的HiveServer和WebHCat进程状态显示为故障，重启之后仍为故障状态。

### 原因分析

在Manager界面单独启动故障的HiveServer进程，登录后台查找hiveserver.out日志中对应时间点的报错，报错信息为：error parsing conf mapred-site.xml和Prematureend of file。然后重启WebHCat也发现同样报错，原因即为解析mapred-site.xml文件错误。

### 处理步骤

1. 以root用户登录Master2节点。

2. 执行find / -name 'mapred-site.xml'命令获取mapred-site.xml文件所在位置。HiveServer对应路径为“/opt/Bigdata/集群版本/1_13_HiveServer/etc/mapred-site.xml”。

WebHCat对应路径为“/opt/Bigdata/集群版本/1_13_WebHCat/etc/mapred-site.xml”。

3. 确认mapred-site.xml文件是否有异常，该案例中该配置文件内容为空导致解析失败。

4. 修复mapred-site.xml文件，将Master1节点上对应目录下的配置文件用scp命令拷贝到Master2节点对应目录替换原文件。

5. 执行chown omm:wheel mapred-site.xml命令更改所属组和用户。

6. 在Manager界面重启故障的HiveServer和WebHCat进程，恢复正常。
----结束

## 14.42 MRS Hive 连接 ZooKeeper 时报错“ConnectionLoss for hiveserver2”

### 问题现象

使用MRS 1.8集群的Hive 1.2.1通过Hive的JDBC接口连接MRS集群成功，但是使用MRS1.9.0集群的Hive 2.3.2，通过Hive的JDBC接口连接MRS集群进行计算任务报错。

报错信息如下：

Caused by: org.apache.zookeeper.KeeperException$ConnectionLossException: KeeperErrorCode = ConnectionLoss for /hiveserver2

### 原因分析

MRS 1.8版本和开源版本认证方式一样，在Hive的URL中直接将Kerberos认证的文件传进去进行认证。而在MRS 1.9版本中，此方法行不通，需要先进行Kerberos认证，并且需要获取一些别的配置信息，然后再进行URL拼接。

### 处理步骤

请参考官方MRS 1.9样例工程中hive-examples的认证连接，样例地址请参考开发指南。

### 建议与总结

在官方MRS 1.9的样例基础进行代码开发。
----结束

## 14.43 Hive 执行 insert into 语句报错

### 问题现象

使用MRS Hive执行一条SQL，有如下报错：

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/1d7a50b6d7f3330ad40c8a96329309b1658add54fed7729905b8c4cb23f8a912.jpg)

图 14-1 使用 MRS Hive 执行 SQL 报错

### 原因分析

1. 查看HiveServer日志，在对应时间点，有如下的报错信息。

图 14-2 HiveServer 日志

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/7806730a9971c3b049398dea2a99adbe6ea72882ea0a0f140e77099540b2ad79.jpg)

2. 在如上报错信息中未发现重要信息，但从堆栈中发现metadata字样，怀疑报错是和MetaStore有关。

图 14-3 堆栈中 metadata 字样

2020-06-02 16:11:03,771 | ERROR | HiveServer2-Background-Pool: Thread-2440344 | Failed to run column stats task | org.apache.hadoop.hive.ql.exec.ColumnStatsTask.execute(ColumnStatsTask.java:433)
org.apache.hadoop.hive.gl.metadata.HiveException: org.apache.thrift.transport.TTransportException at org.apache.hadoop.hive.gl.metadata.Hive.setPartitionColumnStatistics(Hive.java:3783) \~[hive-exec-2.3.3-mrs-1.9.0.jar:2.3.3-mrs-1.9.0]

3. 查看MetaStore日志，发现如下报错。

图 14-4 MetaStore 日志

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/e61dfb0be9be1ff107b7bf6a0c85b9aa994d92173cf508e3a519d372d0e4269e.jpg)

查看如上错误的上下文，确定是本次执行SQL的报错，在报错信息里面发现如下内容：

Caused by: org.postgresql.util.PSQLException: ERROR: value too long for type character varying(4000)确认是该条SQL对表的操作，所有列的字节长度超过4000的限制，导致SQL执行失败，需要修改该限制。

### 处理步骤

步骤1 以root用户登录集群任意一个Master节点，并执行su - omm命令切换到omm用户。

步骤2 执行如下命令登录数据库。命令中如果携带认证密码信息可能存在安全风险，在执行命令前建议关闭系统的history命令记录功能，避免信息泄露。gsql -p 20051 -d hivemeta -U username -W password

步骤3 执行如下命令修改限制。

alter table PARTITION_PARAMS alter column PARAM_VALUE type varchar(6000);

----结束

## 14.44 增加 Hive 表字段超时

### 用户问题

增加Hive表字段报错。

### 问题现象

Hive对包含10000+分区的表执行ALTER TABLE table_name ADDCOLUMNS(column_name string) CASCADE;，报错如下：

Timeout when executing method: alter_table_with_environment_context; 600525 ms exceeds 600000 ms

### 原因分析

1. MetaStore客户端连接超时，MRS默认MetaStore客户端和服务端连接的超时时间是600s，在Manager页面调大“hive.metastore.client.socket.timeout”为“3600s”。

2. 出现另一个报错：Error: org.apache.hive.service.cli.HiveSQLException: Error while processing statement: FAILED:Execution Error, return code 1 from org.apache.hadoop.hive.ql.exec.DDLTask. Unable to alter table.java.net.SocketTimeoutException: Read timed outMetastore元数据JDBC连接超时，默认60ms。

3. 调大javax.jdo.option.ConnectionURL中socketTimeout=60000，仍然产生最初的报错：Timeout when executing method: alter_table_with_environment_context;3600556 ms exceeds3600000 ms

4. 尝试调大hive.metastore.batch.retrieve.max、hive.metastore.batch.retrieve.table.partition.max、dbservice.database.max.connections等参数均未能解决。

5. 怀疑是GaussDB的问题，因为增加字段会遍历每个分区执行getPartitionColumnStatistics和alterPartition。

6. 使用omm用户执行gsql -p 20051 -U omm -W password -d hivemeta登录Hive元数据库。命令中如果携带认证密码信息可能存在安全风险，在执行命令前建议关闭系统的history命令记录功能，避免信息泄露。

7. 执行select * from pg_locks;没有发现锁等待。

8. 执行select * from pg_stat_activity;发现进程执行时间较长。

SELECT 'org.apache.hadoop.hive.metastore.model.MPartitionColumnStatistics'AS NUCLEUS_TYPE,A0.AVG_COL_LEN,A0."COLUMN_NAME",A0.COLUMN_TYPE,A0.DB_NAME,A0.BIG_DECI MAL_HIGH_VALUE,A0.BIG_DECIMAL_LOW_VALUE,A0.DOUBLE_HIGH_VALUE,A0.DOUBLE_LOW_VALUE, A0.LAST_ANALYZED,A0.LONG_HIGH_VALUE,A0.LONG_LOW_VALUE,A0.MAX_COL_LEN,A0.NUM_DISTIN CTS,A0.NUM_FALSES,A0.NUM_NULLS,A0.NUM_TRUES,A0.PARTITION_NAME,A0."TABLE_NAME",A0.CS_ ID,A0.PARTITION_NAMEAS NUCORDER0 FROM PART_COL_STATS A0 WHERE A0."TABLE_NAME" = '$1' ANDA0.DB_NAME = '$2' AND A0.PARTITION_NAME = '$3' AND((((((A0."COLUMN_NAME" = '$4') OR (A0."COLUMN_NAME" ='$5')) OR (A0."COLUMN_NAME" = '$6')) OR (A0."COLUMN_NAME" ='$7')) OR (A0."COLUMN_NAME" = '$8')) OR (A0."COLUMN_NAME" ='$9')) ORDER BY NUCORDER0;

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/99690df224ac7308c9424263c4c657d43a5337fda0ee68f72be36b01008180c5.jpg)

9. 执行gs_guc reload -c log_min_duration_statement=100 -D /srv/BigData/dbdata_service/data/开启SQL录制，发现8中语句执行时长700ms，而且因为有10000+分区，会触发执行10000+次命令。

10. 在SQL前加explain (analyze,verbose,timing,costs,bufers)分析执行计划，发现执行时需要全表扫描。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/261df3b0e2a4bd98cffb7fae9b8a140da22420bedf75dad25d8bfc903e17f931.jpg)

11. 查看索引，发现不满足最左匹配原则。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/002b14ea8f75d852d8da2357316f38f82e22adf27fe36777f6e58377d2ad0aa1.jpg)

### 处理步骤

1. 重建索引。su - ommgsql -p 20051 -U omm -W password -d hivemetaDROP INDEX PCS_STATS_IDX;CREATE INDEX PCS_STATS_IDX ON PART_COL_STATS(DB_NAME,TABLE_NAME, COLUMN_NAME, PARTITION_NAME);CREATE INDEX SDS_N50 ON SDS(CD_ID);

2. 重新查看执行计划，发现语句已经可以索引查询，且5ms执行完成（原来是700ms）。重新执行hive表字段增加，已经可以添加成功。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/33bbd53747b3d3d10badb4f699c33864b7276ed482d1a1f6e52199b58100e031.jpg)
----结束

## 14.45 重启 Hive 服务失败

### 用户问题

修改Hive服务配置后，保存配置失败，Manager页面Hive服务的配置状态为配置失败。

### 问题现象

用户A在MRS节点后台上打开了Hive相关配置文件且未关闭，此时用户B在MRSManager页面的“服务管理”中修改Hive配置项，保存配置并重启Hive服务，此时保存配置失败，并且Hive服务启动失败。

### 原因分析

由于用户B在MRS Manager页面修改配置时，配置文件被用户A在MRS节点后台打开，导致该配置文件不能被替换，最终导致Hive服务启动失败。

### 处理步骤

步骤1 用户需要首先手动关闭集群节点后台打开的Hive配置文件。

步骤2 在MRS Manager页面重新修改Hive的配置并保存配置。

步骤3 重启Hive服务。

----结束

## 14.46 Hive分区数过多导致删除表失败

### 问题现象

Hive创建的二级分区表有两万多个分区，导致用户在执行truncate table ${TableName},drop table ${TableName}时失败。

### 原因分析

删除文件操作是单线程串行执行的，Hive分区数过多导致在元数据数据库会保存大量元数据信息，在执行删除表语句时删除元数据就要用很长时间，最终在超时时间内删除不完，就会导致操作失败。

### 说明

超时时间可通过登录FusionInsight Manager，选择“集群 > 服务 > Hive > 配置 >全部配置 >MetaStore（角色） > 服务初始化”查看，“hive.metastore.client.socket.timeout”对应的值即为超时时间时长，在“描述”列可查看默认值。

### 处理步骤

步骤1 如果是内部表可以先通过alter table ${TableName} setTBLPROPERTIES('EXTERNAL'='true')来将内部表转成外部表，这样Hive删除的时候只删除元数据省去了删除HDFS数据的时间。

步骤2 如果要用相同的表名可以先将表结构用show create table ${TableName}来导出表结构，再用ALTER TABLE ${TableName} RENAME TO ${new_table_name};来将表重命名。这样就可以新建一个和原来一样表。

步骤3 执行hdfs dfs -rm -r -f ${hdfs_path}在HDFS上删除表数据。

步骤4 在Hive中用alter table ${Table_Name} drop partition (${PartitionName}<XXXX’, ${PartitionName}>’XXXX’);删除分区(具体删除条件可灵活处理)，减少Temporary文件数。

步骤5 删除分区少于一千个后，直接用drop table ${TableName}删掉表即可。

### 建议与总结

Hive分区虽然可以提高查询效率，但要避免分区不合理导致出现大量小文件的问题，要提前规划好分区策略。
----结束

## 14.47 Hive 执行 msck repair table 命令时报错

现象描述

Hive执行msck repair table table name命令报错：

FAILED: Execution Error, return code 1 from org.apache.hadoop.hive.ql.exec.DDLTask (state=08S01,code=1)。

### 可能原因

查看HiveServer日志“/var/log/Bigdata/hive/hiveserver/hive.log”，发现目录名不符合分区格式。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/79612e1065b72f105c8ff2117be6648cb3496d63b0f0df96f4a15e6bc58c8161.jpg)

### 处理步骤

● 方法一：删除错误的文件或目录。

● 方法二：执行set hive.msck.path.validation=skip;，跳过无效的目录。
----结束

## 14.48 Hive 执行 insert into 命令报用户权限不足

### 用户问题

用户在Beeline命令行执行insert into命令报错：

INFO : Concurrency mode is disabled, not creating a lock manager
Error: Error while processing statement: FAILED: Execution Error, return code 1 from
org.apache.hadoop.hive.ql.exec.mr.MapRedTask. org.apache.hadoop.yarn.exceptions.YarnException: Failed to submit application_xxx to YARN : User xxx cannot submit application application_xxx to queue root.default. ACL check failed. (state=08S01,code=1)

### 原因分析

当前提交任务的用户不具备Yarn对应队列的权限。

### 处理步骤

步骤1 为当前用户配置Yarn队列的权限。

在Manager界面为当前用户绑定对应权限的角色，例如：default，详细操作请参考修改用户信息章节。

若Hive启用了Ranger鉴权，也可以参考添加Yarn的Ranger访问权限策略章节设置当前用户在指定Yarn队列提交任务的权限。

步骤2 权限配置生效后，重新执行命令。

----结束

## 14.49 在 Hive 中 drop 表后如何完全释放磁盘空间

### 用户问题

在Hive命令行执行drop表的操作后，通过命令hdfs dfsadmin -report查看磁盘空间，发现表没有删除。

### 原因分析

在Hive命令行执行drop表只删除了外部表的表结构，并没有删除该表存储在HDFS上的表数据。

### 处理步骤

步骤1 使用root用户登录安装客户端的节点，并认证用户。cd 客户端安装目录source bigdata_envkinit 组件业务用户（未开启Kerberos认证的集群跳过此操作）

步骤2 执行以下命令删除存储在HDFS上的表。hadoop fs -rm hdfs://hacluster/表所在的具体路径----结束
----结束

## 14.50 JSON 表中有破损数据导致 Hive 查询异常

### 用户问题

在Hive客户端查询JSON数据，JSON表中有破损数据导致查询异常：

1. 在Hive客户端上使用默认开源的JSON序列化建表语句创建表：create external table if not exists test (name string)row format serde 'org.apache.hive.hcatalog.data.JsonSerDestored as textfilelocation 'hdfs://hacluster/user/hive/warehouse/database/table/jsondata';

2. 查询表出现异常。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/05c1178c4a482adb3f4c13eeca6a3a18fe93797c804e9b9284afda058c121a09.jpg)

### 说明

该章节内容适用于MRS 1.9.2之后版本。

### 原因分析

使用默认开源的JSON序列化语句创建Hive表无法将表中JSON破损数据过滤掉，导致查询异常。

### 处理步骤

步骤1 下载json-serde-1.3.8-jar-with-dependencies.jar到本地，并将该Jar上传到所有的HiveServer所在节点。

步骤2 以客户端安装用户，登录步骤1上传了Jar包并且安装了Hive和HDFS客户端的节点。

步骤3 执行以下命令认证用户。cd客户端安装目录source bigdata_envkinit 具有Hive管理员权限的用户（未开启Kerberos认证的集群跳过此操作）

步骤4 执行以下命令在HDFS上创建Jar包存放目录。hdfs dfs -mkdir Jar包存放在hdfs中的路径

步骤5 执行以下命令将步骤2的Jar上传至HDFS中。hdfs dfs -put Jar包存放路径Jar包存放在hdfs中的路径

步骤6 执行以下命令让Hive在执行命令行任务时加载指定Jar包。beelineset role admin;（未开启Kerberos认证的集群跳过此操作）add jar Jar包存放在hdfs中的路径;

步骤7 执行以下命令重新创建表：create external table if not exists test (name string)row format serde 'org.openx.data.jsonserde.JsonSerDe'stored as textfilelocation 'hdfs://hacluster/user/hive/warehouse/database/table/jsondata';

步骤8 执行以下命令修改表属性忽略破损的JSON数据：ALTER TABLE test SET SERDEPROPERTIES( "ignore.malformed.json" = "true");设置该属性后，查询表时若表中有破损的JSON数据默认显示为“NULL”。

步骤9 执行以下命令查询表数据：select * from test;数据查询成功则表示已忽略破损的JSON数据，其中，破损的JSON数据显示为“NULL”：

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/d7e957ac48ed313b49da9993dff60248bf54b744f5a9870c9e099312d4942a02.jpg)

----结束

## 14.51 Hive 客户端执行 SQL 报错连接超时

现象描述

Hive客户端执行SQL失败，报错：Timed out waiting for a free availableconnection。

### 可能原因

DBService连接较多，获取连接超时。

### 操作步骤

步骤1 客户端是否使用Spark-SQL客户端执行SQL。

● 是，检查连接的URL中超时参数，将其修改为600，执行步骤7。

● 否，执行步骤2。

步骤2 登录Manager页面，选择“集群 > 服务 > Hive > 配置 > 全部配置”，搜索“javax.jdo.option.ConnectionURL”，检查超时参数是否小于600。

Hive

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/de3d628cf977898d286e284f2f577e5e5830f4fedebef1415b3d22da7676b725.jpg)

### 说明

Hive、HiveServer、MetaStore、WebHCat中均有该参数，请确保它们的参数值一致。

● 是，执行步骤3。

● 否，执行步骤7。

步骤3 检查参数“javax.jdo.option.ConnectionURL”的值是否为“$

{javax.jdo.option.ConnectionURL.default}”。

● 是，执行步骤4。

● 否，修改URL中超时参数为600，单击“保存”，执行步骤7。

步骤4 单击“实例”，选择任意HiveServer实例，并使用root用户登录实例节点。

步骤5 打开配置文件“${BIGDATA_HOME}/FusionInsight_Current/*HiveServer/etc/hivemetastore-site.xml”，查找配置项“javax.jdo.option.ConnectionURL”，复制配置项值。

<property>
<name>avax.jdo.option.ConnectionURL</name>
<value>jdbc:postgresql://100.120.146.72:20051/hivemeta?socketTimeout=60</value>
</property>
<property>

步骤6 登录Manager页面，选择“集群 > 服务 > Hive > 配置 > 全部配置”，搜索“javax.jdo.option.ConnectionURL”，修改配置为步骤5中复制的URL，并修改超时参数为600，单击“保存”。

说明

Hive、HiveServer、MetaStore、WebHCat中均有该参数，请确保它们的参数值一致。

步骤7 选择“集群 > 服务 > Hive > 配置 > 全部配置”，搜索

“maxConnectionsPerPartition”，检查是否小于100。

● 是，修改参数为100，单击“保存”，执行步骤8。

● 否，执行步骤8。

步骤8 若以上步骤有修改参数，选择“集群 > 服务 > Hive > 概览”，选择“更多 > 滚动重启服务”，未修改则无需执行此步骤。

----结束

## 14.52 WebHCat 健康状态异常导致启动失败

### 用户问题

WebHCat实例启动失败。

### 问题现象

在Manager页面上查看到WebHCat实例的健康状态为“故障”，并上报“ALM-12007进程故障”告警，该告警的服务名称为“Hive”，实例名称为“WebHCat”。且重启Hive服务报错。

查看WebHCat实例的日志“/var/log/Bigdata/hive/webhcat/webhcat.log”报错“Service not found in Kerberos database”和“Address already in use”

### 处理步骤

步骤1 依次登录WebHCat实例所在节点检查“/etc/hosts”文件中的IP及主机名称映射关系是否正确。且“/etc/hostname”和“/etc/HOSTNAME”文件的WebHCat配置需与“/etc/hosts”保持一致，若不一致则需手动修改。

说明

WebHCat实例的IP地址及主机名称映射关系可登录FusionInsight Manager界面，选择“集群 >服务 > Hive > 实例”查看。

步骤2 登录WebHCat实例所在节的任一节点，执行以下命令切换到omm用户。su - omm

步骤3 执行以下命令查看是否存在WebHCat进程。ps -ef|grep webhcat|grep -v grep若存在，则需执行以下命令结束WebHCat进程：kill -9 ${webhcat_pid}

步骤4 登录FusionInsight Manager，选择“集群 > 服务 > Hive > 实例”，勾选所有WebHCat实例，选择“更多 > 重启实例”，等待WebHCat重启成功即可。
----结束

## 14.53 mapred-default.xml 文件解析异常导致 WebHCat启动失败

### 用户问题

MRS的Hive服务故障，重新启动后，Master2节点上的HiveServer和WebHCat进程启动失败，Master1节点进程正常。

### 原因分析

登录Master2节点，查看“/var/log/Bigdata/hive/hiveserver/hive.log”日志，发现HiveServer一直加载“/opt/Bigdata/*/*_HiveServer/etc/hive-site.xml”；查看HiveServer退出时的“/var/log/Bigdata/hive/hiveserver/hiveserver.out”日志，发现解析“mapred-default.xml”文件异常。

### 处理步骤

步骤1 登录Master2节点，使用以下命令查找“mapred-default.xml”所在路径：find /opt/ -name 'mapred-default.xml'查询到该配置文件在“/opt/Bigdata/*/*_WebHCat/etc/”目录下面，且该文件内容为空。

步骤2 登录到Master1节点，将“/opt/Bigdata/*/*_WebHCat/etc/mapred-default.xml”文件拷贝到Master2节点，并修改文件的属组为“omm:wheel”。

步骤3 登录Manager，重启异常的HiveServer和WebHCat实例。

----结束

## 14.54 Hive 元数据使用 RDS 时创建视图表中文乱码

### 用户问题

MRS 3.1.0版本集群，Hive元数据配置为RDS数据库中存储。创建视图时，使用casewhen语句中文显示乱码。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/d4d41c3a2d6ef4bc572f3f514deffc08a4fc6678586916041e979fd9bb7e3ca0.jpg)

例如建表语句如下：

查看视图内容中，中文乱码：

$$
\begin{array} { r l } { \sqrt { 2 } \equiv \lVert \widetilde { \mathbf { g } } \rVert \equiv \langle \mathbf { g } \rVert [ \mathbf { g } ( \mathbf { z } ) \mathbf { I } \rVert ( \mathbf { z } ( \mathbf { z } ) \mathbf { I } \mathbf { H } ( \mathbf { z } ) ) - \mathbf { V } \mathbf { e } ] \otimes \mathbf { I } \mathbf { e } [ \mathbf { z } ]  } & { [ \mathbf { g } ( \mathbf { z } ) \mathbf { A } ( \mathbf { a } ) \mathbf { S } \mathbf { I } \mathbf { z } ]  \mathbf { I } [ \mathbf { a } ] \ : \ : \lVert \mathbf { z } \rVert \ : \ : \Gamma [ \mathbf { g } ( \mathbf { z } ) \mathbf { I } \mathbf { z } ] } \\ { \mathrm { ~ } } & { \ : \ : \ : \ : \langle \mathbf { g } \rVert [ \mathbf { z } \rVert [ \mathbf { \overline { { g } } } \mathbf { a } ] [ \mathbf { \overline { { g } } } \mathbf { I } ] [ \mathbf { \overline { { g } } } \mathbf { I } \mathbf { I } ] [ \mathbf { \overline { { g } } } \mathbf { I } \mathbf { I } ] [ \mathbf { \overline { { g } } } \mathbf { I } \mathbf { I } ] [ \mathbf { \overline { { g } } } \mathbf { I } \mathbf { I } ] [ \mathbf { \overline { { g } } } \mathbf { I } \mathbf { I } ] [ \mathbf { \overline { { g } } } \mathbf { I } \mathbf { I } ] [ \mathbf { \overline { { g } } } \mathbf { I } \mathbf { I } ] } \\ { \mathrm { ~ } } & { \ : \ : \ : \ : \ : \langle \mathbf { I } \mathbf { I } \mathbf { I } \mathbf { I } \mathbf { I } \mathbf { I } \rangle [ \mathbf { \overline { { g } } } \mathbf { I } \mathbf { I } \mathbf { I } ] [ \mathbf { \overline { { g } } } \mathbf { I } \mathbf { I } ] [ \mathbf { \overline { { g } } } \mathbf { I } \mathbf { I } ] [ \mathbf { \overline { { g } } } \mathbf { I } \mathbf { I } ] } \\ { \mathrm { ~ } } &  \ : \ : \ : \ : \mathrm { I m ~ i s t ~ } \ : \ : \mathrm  \end{array}
$$

### 原因分析

该问题是由于元数据表相关字段编码不是UTF 8，导致中文显示异常。

### 处理步骤

$$
\begin{array} { r l }  \frac { 1 } { 2 5 } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { E } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { E } \mathbb { V } \mathbb { V } \mathbb { E } \mathbb { V } \mathbb { E } \mathbb { V } \mathbb { E } \mathbb { V } \mathbb { E } \mathbb { V } \mathbb { E } \mathbb { V } \mathbb { E } \mathbb { V } \mathbb { E } \mathbb { V } \mathbb { E } \mathbb { V } \mathbb { E } \mathbb { V } \mathbb { E } \mathbb { V } \mathbb { E } \mathbb { V } \mathbb { E } \mathbb { V } \mathbb { E } \mathbb { V } \mathbb { V } \mathbb { E } \mathbb { V } \mathbb { V } \mathbb { E } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { E } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { E } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { E } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { E } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { E } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V } \mathbb { V }  \end{array}
$$

ALTER TABLE TBLS modify COLUMN VIEW_EXPANDED_TEXT mediumtext CHARACTER SET utf8;

ALTER TABLE TBLS modify COLUMN VIEW_ORIGINAL_TEXT mediumtext CHARACTER SET utf8;

步骤3 重新创建视图后不存在中文乱码情况。

----结束

## 14.55 MetaStore 动态分区数超出阈值导致 SQL 报错

现象描述

执行SparkSQL或HiveSQL命令时，系统报错如下：

Number of dynamic partitions created is 2001, which is more than 2000. To solve this try to set hive.exec.max.dynamic.partitions to at least 2001

### 原因分析

Hive中会默认限制最大动态分区数，由“hive.exec.max.dynamic.partitions”参数控制（默认值为1000）。 如果超过此限制，Hive将不会创建新的动态分区。

### 处理步骤

调整上层业务，将动态分区数控制在“hive.exec.max.dynamic.partitions”参数值范围内。

执行set hive.exec.max.dynamic.partitions = XXX;命令调大“hive.exec.max.dynamic.partitions”参数值。

SparkSQL中需要设置“spark.hadoop.hive.exec.max.dynamic.partitions”参数。
----结束

## 14.56 如何对 insert overwrite 自读自写场景进行优化

场景说明

对于需要使用动态分区插入（使用历史分区更新）数据到目的表中，且和数据源表是同一张表时，由于直接在原表上执行insert overwrite可能会导致数据丢失或数据不一致的风险，建议先使用一个临时表来处理数据，再执行insert overwrite操作。

### 操作步骤

假设存在如下一张表：

user_data(user_group int, user_name string, update_time timestamp);

其中user_group是分区列，需要根据已有数据，按更新时间进行排序，刷新用户组信息。操作步骤如下：

步骤1 在Hive Beeline命令行执行以下命令开启Hive动态分区：set hive.exec.dynamic.partition=true;set hive.exec.dynamic.partition.mode=nonstrict;

```sql
步骤2 执行以下命令创建一个临时表，用于存储去重后的数据：
CREATE TABLE temp_user_data AS
SELECT * FROM (
SELECT *,
ROW_NUMBER() OVER(PARTITION BY user_group ORDER BY update_time
DESC) as rank
FROM user_data
) tmp
WHERE rank = 1;
步骤3 执行以下命令使用临时数据作为数据源，并插入到目的表中：
INSERT OVERWRITE TABLE user_data
SELECT user_group, user_name, update_time
FROM temp_user_data;
步骤4 执行以下命令清理临时表：
DROP TABLE IF EXISTS temp_user_data;
----结束
```
----结束

## 14.57 Hive 大 SQL 任务异常如何定位

现象描述

MRS 3.5.0-LTS及之后版本，Hive执行的大SQL导致HiveServer或MetaStore内存快速增长，频繁Full GC使得业务无法正常运行，甚至导致实例异常重启。

### 原因分析

● 查询大字段表导致HiveServer内存异常。

● 执行的SQL涉及的文件数过多，导致HiveServer内存异常。

● 执行的SQL涉及的分区数过多，导致HiveServer或MetaStore内存异常。

● MRS 3.6.0-LTS及之后版本，配置的堆内存不合理，导致HiveServer内存异常。

● MRS 3.6.0-LTS及之后版本，大量连接使用完未关闭，导致HiveServer内存异常。

### 处理步骤

- 查询大字段表导致HiveServer内存异常场景

HiveServer查询结果分批次返回客户端，默认一批次返回1000条数据，大字段将大量占用实例内存，严重时将导致HiveServer OOM自动重启，当前实例正在运行的任务全部失败。

大字段表查询异常时，客户端异常如图14-5所示，调用FetchResults时无法处理大字段，HiveServer异常重启，连接中断。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/2c2eabe4fb30d0da3a60ef2f7e5c9be4645960e2083f541f6a21ce2f8e686844.jpg)

图 14-5 大字段表查询异常

参考如下操作进行处理：

a. 登录Manager页面，选择“运维 > 事件”，在事件列表中查看Hive对象“进程重新启动”事件的详细信息，在“定位信息”中记录上报该事件的HiveServer主机名；并记录该事件的“产生时间”，即为HiveServer重启时间。

单击“主机”，在主机列表中查看上报事件的主机名对应的节点的IP地址。

b. 登录a查看到的重启的HiveServer节点，执行以下命令查看重启时是否生成JVM错误日志“hs_err_pid_*log”：

ll /var/log/Bigdata/hive/hiveserver/hs_err_pid_*log

▪ 是，执行c。

▪ 否，执行d。

c. 使用关键字“HiveSessionImpl.fetchResults”在“hs_err_pid_*log”日志中查找正在获取返回结果的线程名称，执行e。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/cf766294a26264f15fea64161c13e58c0cad1aacd80f73a5f990b3b2247bfb5d.jpg)

图14-6 查找线程名称

d. 在HiveServer运行日志“/var/log/Bigdata/hive/hiveserver”目录下的HiveServer重启前一段时间内的运行日志文件中，查找OOM重启日志“Stopping HiveServer2 due to OOM”，并记录线程名称，执行e。

e. 在HiveServer审计日志“/var/log/Bigdata/audit/hive/hiveserver/hive-audit.log”中使用编译线程名称查找HiveServer重启时间之前执行的查询SQL，并联系相关业务排查相关表是否包含大字段，停止对应的任务或修改相关表。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/98154a690f05d461cf9cbb42567389f4a18c3814c9e91f73419cc5c43179e78a.jpg)

图 14-7 查找 SQL 语句

- SQL涉及的文件数过多，导致HiveServer内存异常

HiveServer使用MapReduce引擎执行SQL时，提交任务前在HiveServer内存中读取文件进行切片，每个文件约占用2k内存，文件数过多将导致HiveServer内存异常。

a. 登录Manager页面，选择“集群 > 服务 > Hive > 配置 > 全部配置”，查看是否配置如下参数：

hive-ext.combine.input.file.limit.enable：用于设置是否开启读取文件数限制，默认值为“false”。开启该功能后，提交Hive任务前会统计读取的文件数并判断是否拦截该SQL，将增大对应任务执行的时间。

hive-ext.combine.input.file.limit.threshold：若开启读取文件数限制参数，文件数超过该参数值的SQL将失败，默认值为1000000。

▪ 是，执行b。

▪ 否，执行c。

b. 在HiveServer运行日志“/var/log/Bigdata/hive/hiveserver”目录下的HiveServer重启前一段时间内的运行日志文件中，使用关键字“The numberof files exceeds”过滤超过限制值50%的线程名称，排查对应的SQL并联系业务人员进行处理。

c. 联系业务人员确认是否需要开启相关参数限制大任务运行，文件数达到配置的限制值50%将打印提示日志“The number of files exceeds ***”，文件数达到限制值的SQL将失败。

▪ 是，在HiveServer自定义配置中添加以上两个参数，并重启HiveServer实例。

▪ 否，执行d。

d. MRS 3.6.0-LTS之前版本，任务正常执行打印日志如图14-8所示，过滤异常时间段打印目录日志“Total number of paths”，但无扫描文件结束日志“Total input files to process”的线程，以及打印文件数“Total input filesto process”超过10万的线程，并联系运维人员排查对应的SQL进行处理。

![image](https://cdn-mineru.openxlab.org.cn/result/2026-10-05/5074c877-6ef1-4a89-8d92-199d2917a672/aa4b6ee0c80c781bd0d05a62179fb65a64daaf0c76769706889d12918b2764a8.jpg)

图 14-8 任务运行日志

MRS 3.6.0-LTS及之后版本，任务正常执行会打印扫描的文件数，

MapReduce引擎搜索关键字“Number of all splits”，Tez和Spark引擎搜索关键字“Total input files”，找到关键字日志内容中“files”的值超过10万对应的线程，并联系运维人员排查对应的SQL进行处理。

- SQL涉及的分区数过多，导致HiveServer或MetaStore内存异常

分区表查询或msck、analyze、alter删除大量分区等SQL执行不带分区过滤条件时，HiveServer将会查询所有分区名，再根据分区名分批查询分区对象，将占用大量HiveServer内存；带分区过滤条件时，HiveServer将条件下推到MetaStore，若满足条件的分区过多，MetaStore内存也会被大量占用。

a. 确认异常的节点是HiveServer还是MetaStore。

▪ HiveServer节点异常，执行b。

▪ MetaStore节点异常，执行c。

b. 在HiveServer运行日志“/var/log/Bigdata/hive/hiveserver”目录下的HiveServer异常的前一段时间内的运行日志文件中，使用关键字“Thenumber of part size”过滤异常时间段扫描分区数大于10000的表，根据线程名排查相关SQL，联系运维人员进行处理。

c. 登录Manager页面，选择“集群 > 服务 > Hive > 配置 > 全部配置”，查看是否配置以下参数：

metastore.limit.partition.request：默认值为-1，配置该参数值大于0时，MetaStore会使用过滤条件提前count查询的分区数量，结果值超过此参数的分区过滤查询将失败。

▪ 是，执行d。

▪ 否，执行e。

d. 在MetaStore运行日志“/var/log/Bigdata/hive/metastore”目录下的MetaStore异常的前一段时间内的运行日志文件中，使用关键字“Thenumber of part size”过滤异常时间段扫描分区数大于10000的表，根据表名排查相关SQL，联系运维人员进行处理。

e. 联系业务确认是否需要开启相关参数，限制大任务运行，配置后分区过滤将增加count操作，将增加查询耗时。

▪ 是，在MetaStore自定义配置中添加相关参数并重启MetaStore实例。

▪ 否，执行f。

f. MRS 3.6.0-LTS之前版本，在MetaStore审计日志“/var/log/Bigdata/audit/hive/metastore”目录下的MetaStore异常的前一段时间内的日志文件中，使用关键字“get_partitions_by_expr”、“get_partitions”“get_partitions_with_auth”和“get_partitions_by_filter”过滤异常时间段查询的表，排查相关SQL并联系运维人员进行处理。

MRS 3.6.0-LTS及之后版本，在MetaStore运行日志“/var/log/Bigdata/hive/metastore”目录下的MetaStore异常的前一段时间内的日志文件中，使用关键字“The number of scanned partitions in”过滤异常时间段查询的表，排查相关SQL并联系运维人员进行处理。

MRS 3.6.0-LTS及之后版本，配置的堆内存不合理，导致HiveServer内存异常场景由于业务需要运行过多的SQL任务使得HiveServer或Metastore实例内存使用率很大，但系统内存仍使用的默认值，或者配置过小不能满足实际的需要，从而会导致进程频繁GC。方法如下：

a. 在Manager首页，选择“运维 告警 告警”，“Hive服务进程堆内存使用超出阈值”告警展开详情页面，在定位信息中确认内存使用异常的节点是HiveServer还是MetaStore。

▪ HiveServer节点异常，执行b。

▪ MetaStore节点异常，执行c。

b. 在Manager首页，选择“集群 > 服务 > Hive > 实例”，单击告警上报的HiveServer，进入实例“概览”页面，单击图表区域右上角的下拉菜单，选择“定制 > CPU和内存”，勾选“HiveServer内存使用率统计”，单击“确定”，查看HiveServer进程使用的堆内存是否长期达到或接近HiveServer进程设定的最大堆内存的阈值（默认95%）。

▪ 是，执行d。

▪ 否，操作结束。

c. 在Manager首页，选择“集群 > 服务 > Hive > 实例”，单击告警上报的MetaStore，进入实例“概览”页面，单击图表区域右上角的下拉菜单，选择“定制 > CPU和内存”，勾选“MetaStore内存使用率统计”，单击“确定”，查看MetaStore进程使用的堆内存是否长期达到或接近MetaStore进程设定的最大堆内存的阈值（默认95%）。

▪ 是，执行d。

▪ 否，操作结束。

d. 在Manager首页，选择“集群 > 服务 > Hive > 配置”，选择“全部配置”，在左侧导航栏选择“HiveServer（角色）/MetaStore（角色） > JVM”，将“HIVE_GC_OPTS/METASTORE_GC_OPTS”参数中“-Xmx”的值根据如下建议进行调整，单击“保存”保存配置，并重启Hive使配置生效。

GC参数配置建议：

▪ 将“-Xmx”值调整为默认值的2倍，例如“-Xmx”默认设置为2G时，调整“-Xmx”的值为4G。

调整“-Xms”的值，使“-Xms”和“-Xmx”比值为1:2，这样可以避免JVM动态调整堆内存大小时影响性能。

▪ 调小“-XX:CMSInitiatingOccupancyFraction”参数的值，加快GC频率，避免一次GC时间过长，例如修改值为60。

▪ 将“-XX:NewSize”和“-XX:MaxNewSize”参数值大小设置为“-Xmx”参数值的四分之一。

如果现有集群的JVM配置里没有相关参数，但需要调整参数值，可在现有参数里加上需要调整的参数。

MRS 3.6.0-LTS及之后版本，大量连接使用完未关闭导致HiveServer内存异常场景创建Hive连接时，JDBC驱动对象、结果集对象ResultSet、语句对象Statement、内部缓冲区等都会存储在堆内存中，如果大量的连接未正常关闭，会持续占用堆内存空间，导致老年代对象堆积并触发回收需求，触发Full GC报错。

a. 确认异常的节点是HiveServer还是MetaStore。

▪ HiveServer节点异常，执行b。

▪ MetaStore节点异常，执行c。

b. 登录Manager页面，选择“集群 > 服务 > Hive > 图表”，在“图表分类”中选择“Session”，在图表区域查看“HiveServer的session数统计”图表，确认HiveServer的session数是否出现持续增高的现象。

▪ 是，执行d。

▪ 否，操作结束。

c. 登录Manager页面，选择“集群 > 服务 > Hive > 实例 > MetaStore > 图表”，在“图表分类”中选择“连接数”，在图表区域查看“MetaStore连接数统计”图表，确认MetaStore的session数是否出现持续增高的现象。

▪ 是，执行e。

▪ 否，操作结束。

d. 登录异常的HiveServer节点，执行以下命令：

grep 'OpenSession' /var/log/Bigdata/audit/hive/hiveserver/hiveaudit.log | awk '{print $9}' | sort | uniq -c | sort
grep 'CloseSession' /var/log/Bigdata/audit/hive/hiveserver/hiveaudit.log | awk '{print $9}' | sort | uniq -c | sort

分析以上命令执行后的统计结果，根据审计日志中打开session和关闭session的日志记录信息排查session是否正常关闭，如果关闭session的日志信息少于打开session的日志，且相差的数量远大于正在运行的任务数量，则说明存在大量连接数未关闭的情况，需要业务侧检查是否有未正常关闭的连接、连接池配置的是否合理，如果存在需及时处理。

e. 联系业务侧开发人员排查连接MetaStore的代码，检查是否有未正常关闭的连接、连接池配置的是否合理，如果存在需及时处理。
----结束
