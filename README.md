# OSS-FTP工具

## 介绍
OSS-FTP是一款基于阿里云OSS的FTP server工具, 通过将FTP请求转换为OSS请求，使得用户可以用FTP的方式来使用OSS.

## 支持系统
* windows

* Mac

* Linux

## 环境依赖

* python 2.6
* python 2.7

## 下载

下载链接： [ossftp.1.0.zip](http://gosspublic.alicdn.com/ossftp/ossftp.1.0.zip)

1. **注意解压后的路径不要含有中文**

2. **注意由于FTP 协议是明文传输的，所以建议您把FTP server和FTP client放在同一台机器，避免密码泄漏**

## 启动FTP server
有两种方法:

1. 启动FTP server的同时，启动一个简单的web server，方便进行FTP服务器的配置和状态监控

在FTP工具的根目录，直接运行对应的start脚本

    1) Windows:
    双击运行start.vbs即可

    2) Linux:
```bash
$ bash start.sh
```
    3) Mac:
```bash
$ bash start.command
```

这种方法会默认在本地的127.0.0.1:2048端口监听FTP请求，同时会在127.0.0.1:8192端口开启一个web服务器
这种方法会读取FTP工具根目录下的**config.json**文件

2. 轻量级的启动方式，即只启动一个FTP server
进入到ossftp目录

```bash
$ python ftpserver.py
```
这会在127.0.0.1:2048端口启动一个FTP 服务器

启动时也可以通过参数指定监听地址和端口等信息
```bash
python ftpserver.py --listen_address=<ip address> --port=<your local port> --internal=<True/False> --loglevel=<DEBUG/INFO>
```
如果 internal为"True", FTP server将通过内网域名访问OSS.
如果 internal为"False", FTP server通过公网域名访问OSS.
当不指定internal字段时，FTP server就会自动探测网络状态, 优先选择从内网域名访问OSS

> 关于OSS的访问域名的更多信息，请参考https://help.aliyun.com/document_detail/oss/user_guide/endpoint_region.html

loglevel决定了ftpserver的日志级别, DEBUG级别输出的日志信息会更详细

## 连接到FTP server

可以使用通用的FTP client连接到该FTP server, 推荐使用 [FilzeZilla](https://filezilla-project.org/)
关于FTP账号:

        username:  access_key_id/bucket_name
        password:  access_key_sercret

例如：
        username: qwertyasdfg/this-is-bucket-name
        password: zxcvbgfdsa

## 可能遇到的问题
如果你在Linux下运行FTP server，然后用FileZilla连接时遇到如下错误:

> 501 can't decode path (server filesystem encoding is ANSI_X3.4-1968)

一般是因为本地的中文编码有问题.
在将要运行start.sh的终端中输入下面的命令，然后再重新启动即可

```bash
$ export LC_ALL=en_US.UTF-8; export LANG="en_US.UTF-8"; locale
```

## 更多文档

[OSS FTP工具发布啦](http://bbs.aliyun.com/read/268724.html)

[如何基于OSS FTP工具实现远程附件上传到OSS](http://bbs.aliyun.com/read/268734.html)
