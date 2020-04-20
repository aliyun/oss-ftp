# OSS-FTP

[![GitHub Version](https://badge.fury.io/gh/aliyun%2Foss-ftp.svg)](https://badge.fury.io/gh/aliyun%2Foss-ftp)
[![Software License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)

### [README of English](https://github.com/aliyun/oss-ftp/blob/master/README.md)

## 介绍
OSS-FTP是一款基于阿里云OSS的FTP与SFTP server工具, 通过将FTP,SFTP请求转换为OSS请求，使得用户可以用FTP或SFTP的方式来使用OSS.

### 主要特性

- **跨平台:** 无论是windows、Linux还是Mac， 无论是32位还是64位操作系统，无论是图形界面还是命令行都可以运行
- **免安装:** 解压后可直接运行
- **免设置:** 无需设置即可运行
- **透明化:** 工具是python写的，您可以看到完整的源码，我们稍后也会开源到Github

### 主要功能

- 支持文件／文件夹的上传／下载／删除等操作
- 通过Multipart方式，分片上传大文件
- 支持大部分FTP指令，可以满足日常FTP的使用需求

### *注意*
- 目前在1.0版本中，考虑到安装部署的简便, OSS FTP工具没有支持TLS加密。由于FTP协议是明文传输的，**为了防止您的密码泄漏，建议将FTP server和client运行在同一台机器上**，通过127.0.0.1:port的方式来访问
- 不支持rename, move操作
- 安装包解压后的路径不要含有中文
- OSS-FTP server的管理控制页面在低版本的IE中可能打不开
- OSS-FTP server支持的Python版本: python2.6, python2.7, python3.6, python3.7


## 启动FTP/SFTP server
分为便捷式启动与轻量级启动两种方式。

### 1. 便捷式启动FTP, SFTP server以及一个简单web server
启动FTP与SFTP server的同时，会启动一个简单的web server，方便进行FTP/SFTP服务器的配置和状态监控。
可以在配置界面配置FTP server与SFTP server的开启与否。

在OSS-FTP工具的根目录，直接运行相应的start脚本

- Windows:
双击运行start.vbs即可

- Linux:
```bash
$ bash start.sh
```

- Mac:
```bash
$ bash start.command
```

这种方法会读取OSS-FTP工具根目录下的**config.json**文件, 然后默认在本地的127.0.0.1:2048端口监听FTP请求，在127.0.0.1:50000监听SFTP请求，同时会在127.0.0.1:8192端口开启一个web服务器，方便对FTP/SFTP server进行管理。

config.json中的配置参数介绍见后文。

### 2. 轻量级启动FTP server
进入到ossftp目录

```bash
$ python ftpserver.py
```
这会在127.0.0.1:2048端口启动一个FTP 服务器

启动时也可以通过参数指定监听地址和端口等信息
```bash
python ftpserver.py --listen_address=<ip address> --port=<your local port> --passive_ports=<your passive_ports like 51000~52000>--internal=<True/False> --loglevel=<DEBUG/INFO>
```
passive_ports 为FTP 被动模式的数据端口

如果 internal为"True", FTP server将通过内网域名访问OSS.
如果 internal为"False", FTP server通过公网域名访问OSS.
当不指定internal字段时，FTP server就会自动探测网络状态, 优先选择从内网域名访问OSS

> 关于OSS的访问域名的更多信息，请参考https://help.aliyun.com/document_detail/oss/user_guide/endpoint_region.html

loglevel决定了ftpserver的日志级别, DEBUG级别输出的日志信息会更详细

### 3. 轻量级启动SFTP server
进入到osssftp目录

```bash
$ python sftpserver.py
```
这会在127.0.0.1:50000端口启动一个SFTP 服务器

启动时也可以通过参数指定监听地址和端口等信息
```bash
python sftpserver.py --listen_address=<ip address> --port=<your local port> --internal=<True/False> --loglevel=<DEBUG/INFO>
```
如果 internal为"True", SFTP server将通过内网域名访问OSS.
如果 internal为"False", SFTP server通过公网域名访问OSS.
当不指定internal字段时，SFTP server就会自动探测网络状态, 优先选择从内网域名访问OSS

> 关于OSS的访问域名的更多信息，请参考https://help.aliyun.com/document_detail/oss/user_guide/endpoint_region.html

loglevel决定了sftpserver的日志级别, DEBUG级别输出的日志信息会更详细

## 连接到FTP/SFTP Server
推荐使用[FileZilla客户端](https://filezilla-project.org/)去连接FTP/SFTP server。下载安装后，按如下方式连接即可:

- 主机：FTP：127.0.0.1，SFTP：sftp://127.0.0.1
- 登录类型： 正常
- 用户：access_key_id/bucket_name (注意： 这里的/是必须的，不是‘或’的意思，如用户名'tSxyiUM3NKswPMEp/test-hz-jh-002')
- 密码：access_key_secret
- 端口：FTP server默认监听端口：2048， SFTP server默认监听端口50000

## 配置文件config.json介绍
如果使用便捷式启动FTP/SFTP server, 程序将从config.json中获取配置信息，以下是各参数介绍。

### 启动参数
- auto_start: 是否开机自启，默认值0表示不自启。
- control_port: web配置端口，默认8192。
- oss_protocol: OSS传输协议，默认为"https"。
- popup_webui:1, 是否自动弹出web界面。默认值1表示弹出。
- show_systray: 是否显示系统托盘，默认值1表示显示。

### FTP server配置参数
- enable: 是否开启FTP server，默认值1表示开启。
- address: FTP server绑定地址，默认值"127.0.0.1"。
- port": FTP server监听端口，默认值2048。
- passive_ports: FTP server 被动模式数据传输端口，默认值"51000~52000"。
- bucket_endpoints: Bucket的访问域名，格式为bucket_name.enpoint，多个域名以英文逗号(",")隔开。默认为空字符串""。
- buff_size: 上传数据缓冲区大小，单位为MB，缓冲区满或者上传完毕，FTP server才会从缓冲区提取数据上传至OSS，默认值为10。
- log_level: 日志等级（DEBUG，INFO，WARNING，ERROR，CRITICAL），默认值"DEBUG"。

### SFTP server配置参数
- enable: 是否开启SFTP server，默认值1表示开启。
- address: SFTP server绑定地址，默认值"127.0.0.1"。
- port": SFTP server监听端口，默认值50000。
- bucket_endpoints: Bucket的访问域名，格式为bucket_name.enpoint，多个域名以英文逗号(",")隔开。默认为空字符串""。
- buff_size: 上传数据缓冲区大小，单位为MB，缓冲区满或者上传完毕，SFTP server才会从缓冲区提取数据上传至OSS，默认值为10。
- log_level: 日志等级（DEBUG，INFO，WARNING，ERROR，CRITICAL），默认值"DEBUG"。

## 可能遇到的问题

**1. 如果连接FTP server时，遇到以下错误：**

```bash
$ 530 Can't list buckets, check your access_key. 
```

有两种可能:

a. 输入的 access_key_id 和 access_key_secret有误.
解决：请输入正确的信息后再重试

b. 所用的access_key信息为ram 子账户的access_key，而子账户不具有List buckets权限。
解决: 给ram子账户赋予足够的权限才能使用FTP工具. 关于用使用ram访问oss时的访问控制，请参考文档[访问控制](https://www.aliyun.com/product/ram/)

> - **只读访问** OSS FTP工具需要的权限列表为
 ['ListBuckets', 'GetBucketAcl', 'ListObjects', 'GetObject', 'HeadObject'].
>  关于如何创建一个具有**只读访问**的ram子账户，请参考图文教程[如何结合ram实现文件共享](https://help.aliyun.com/document_detail/oss/utilities/ossftp/build-file-share-by-ram.html)

> - 如果允许ram子账户**上传文件**，还需要['PutObject']

> - 如果允许ram子账户**删除文件**，还需要['DeleteObject']

**2. 如果你在Linux下运行FTP server，然后用FileZilla连接时遇到如下错误:**

> - 501 can't decode path (server filesystem encoding is ANSI_X3.4-1968)

一般是因为本地的中文编码有问题。
在将要运行start.sh的终端中输入下面的命令，然后再重新启动即可
```bash
$ export LC_ALL=en_US.UTF-8; export LANG="en_US.UTF-8"; locale
```

**3. 如果FTP server已经成功启动，但是文件列出失败:**
- 首先测试服务是否启动成功，可以使用telnet命令进行测试。
```bash
telnet 127.0.0.1 2048
```
- 如果确保服务已成功启动，但是文件列出失败，首先考虑FTP server的被动端口是否添加到了防火墙白名单。

**4. 如果连接服务器失败:**
- 同上，首先确保程序已经成功启动。尝试在config.json中服务地址配置为真实地址或者“0.0.0.0”代替“127.0.0.1”.

## Run tests
进入 *test* 目录运行run_test.sh脚本
```bash
bash run_test.sh
```

## 更多文档
[oss ftp官网主页](https://help.aliyun.com/document_detail/oss/utilities/ossftp/install.html)
