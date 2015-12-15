# OSS-FTP (试用版)

## 介绍
OSS-FTP是一款基于阿里云OSS的FTP Server工具, 通过将FTP请求转换为OSS请求，使得用户可以用FTP的方式来使用OSS.

## 支持系统
* 
*

## 环境依赖


## 安装

* 安装依赖：由于用到了pyOpenSSL库，而该python库是对系统的OpenSSL库的一种封装，所以需要安装以下系统库

如果是在Ubuntu/Debian上：
```bash      
$ apt-get install libffi-dev
$ apt-get install libssl-dev
``` 

如果是在CentOS上:
```bash
$ yum install libffi-devel
$ yum install openssl-devel
```

* 下载OSS-FTP代码，进入目录执行下面的命令进行安装:

```bash
$ python setup.py install
```

## 使用
      
* 启动FTP Server:

```bash
$ python ftpserver_ssl.py
```     
当不加任何参数启动Server时, FTP Server将会自动根据当前网络情况，选择是否通过内网域名访问OSS.


```bash
python ftpserver_ssl.py --port=<your local port> --internal=<True/False>
```        
也可以按上述方式显示指定Server的监听端口，以及访问OSS的方式。
如果 internal为"True", FTP Server将通过内网域名访问OSS.
如果 internal为"False", FTP Server通过公网域名访问OSS.
 
> 关于OSS的访问域名的更多信息，请参考https://help.aliyun.com/document_detail/oss/user_guide/endpoint_region.html
    
* 连接到FTP Server:

可以使用通用的FTP Client连接到该FTP Server, 推荐使用FilzeZilla      
关于FTP账号:

        username:  ACCESS_ID/BUCKET
        password: ACCESS_KEY
        port:     990

例如：
        username: qwertyasdfg/this-is-bucket-name
        password: zxcvbgfdsa
