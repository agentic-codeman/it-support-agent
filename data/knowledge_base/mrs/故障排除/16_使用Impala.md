## 16.1 连接 impala-shell 失败

### 用户问题

用户连接impala-shell失败。

### 问题现象

用户在“组件管理”页面修改任意组件的配置并重启服务后，连接impala-shell，会出现连接失败，报错no such file/directory。

```ini
[root@node-master1emdj etc]# pwd
/opt/Bigdata/MRS_2.1.0/1_7_KuduMaster/etc
[root@node-master1emdj etc]# impala-shell -i 192.168.0.73
shell-init: error retrieving current directory: getcwd: cannot access parent directories: No such file or directory
chdir: error retrieving current directory: getcwd: cannot access parent directories: No such file or directory

Traceback (most recent call last):
  File "/opt/client/Impala/impala/shell/impala_shell.py", line 38, in <module>
    from impala_client import (ImpalaClient, DisconnectedException, QueryStateException,
  File "/opt/client/Impala/impala/shell/lib/impala_client.py", line 20, in <module>
    import sasl
  File "build/bdist.linux-x86_64/egg/sasl/_init_.py", line 1, in <module>

  File "build/bdist.linux-x86_64/egg/sasl/wrapper.py", line 7, in <module>
  File "build/bdist.linux-x86_64/egg/_sasl/wrapper.py", line 7, in <module>
  File "build/bdist.linux-x86_64/egg/_sasl/wrapper.py", line 3, in __bootstrap__.
  File "/usr/lib/python2.7/site-packages/setuptools-0.6c11-py2.7.egg/pkg_resources.py", line 2594, in <module>
    for comparator, version in req.specs:
    File "/usr/lib/python2.7/site-packages/setuptools-0.6c11-py2.7.egg/pkg_resources.py", line 425, in __init__.

  File "/usr/lib/python2.7/site-packages/setuptools-0.6c11-py2.7.egg/pkg_resources.py", line 440, in add_entry
`req`. But, if there is an active distribution for the project and it
  File "/usr/lib/python2.7/site-packages/setuptools-0.6c11-py2.7.egg/pkg_resources.py", line 1688, in find_on_path
return ()
  File "/usr/lib/python2.7/site-packages/setuptools-0.6c11-py2.7.egg/pkg_resources.py", line 1835, in _normalize_cached
  File "/usr/lib/python2.7/site-packages/setuptools-0.6c11-py2.7.egg/pkg_resources.py", line 1829, in normalize_path
register_namespace_handler(object,null_ns_handler)
  File "/usr/lib64/python2.7/posixpath.py", line 368, in realpath
return abspath(path)
  File "/usr/lib64/python2.7/posixpath.py", line 356, in abspath
cwd = os.getcwd()
OSError: [Errno 2] No such file or directory 
```

### 原因分析

修改服务配置并重启服务后，部分服务的目录结构会删除并重新创建，如服务的etc目录等。如果重启服务前所在的目录为etc或者其子目录，由于重启后目录重建，仍在原来目录执行impala-shell时会产生某些系统变量或者参数无法找到的情况，所以连接impala-shell连接失败。

### 处理步骤

任意切换到存在的目录，重新连接impala-shell即可。

## 16.2 创建 Kudu 表报错

### 用户问题

创建Kudu表报错。

### 问题现象

新建了集群，在创建表时，报错如下：

[Cloudera]ImpalaJDBCDriver ERROR processing query/statement. Error Code: 0, SQL state: TStatus(statusCode:ERROR_STATUS, sqlState:HY000, errorMessage:AnalysisException: Table property 'kudu.master_addresses' is required when the impalad startup flag -kudu_master_hosts is not used.” 

### 原因分析

用户未在impala sql中指定kudu.master_addresses地址导致报错。

### 处理步骤

参考使用Impala操作Kudu文档在创建Kudu表时指定“kudu.master_addresses”地址。