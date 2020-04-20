# OSS-FTP

[![GitHub Version](https://badge.fury.io/gh/aliyun%2Foss-ftp.svg)](https://badge.fury.io/gh/aliyun%2Foss-ftp)
[![Software License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)

### [README of Chinese](https://github.com/aliyun/oss-ftp/blob/master/README-CN.md)

## Introduction
OSS-FTP is an FTP and SFTP server tool based on Alibaba Cloud OSS. It converts FTP and SFTP requests into OSS requests for users to use the OSS in an FTP-like or SFTP-like approach.

### Main features

- **Cross-platform:** This tool can run in a graphic interface or using command lines on 32-bit and 64-bit Windows, Linux and Mac operating systems.
- **Installation-free:** You can run this tool directly after extraction.
- **Configuration-free:** You can run the tool without making any configuration.
- **Transparent:** The FTP tool is written in Python and you can see the complete source code. We will soon make it open source on GitHub.

### Main functionality

- Support file/folder upload, download, delete and other operations.
- Support multipart upload of large files.
- Support most FTP commands and can satisfy daily FTP usage needs.

### *Note*
- Currently, does not support TLS encryption for the ease of installation and deployment. Because the FTP protocol implements plaintext transmission, **we recommend you run the FTP server and client on the same server to prevent password leaks** and access using 127.0.0.1:port.
- Rename and move operations are not supported. 
- Do not include Chinese characters in the path to which the installer package is unzipped.
- The OSS-FTP tool's management control page may fail to be opened in older versions of Internet Explorer.
- Python versions supported by the OSS-FTP tool:  Python2.6 , Python2.7, Python3.6, Python3.7 

## Start FTP And SFTP server

Two mode are available, easy startup mode and lightweight startup mode.

### 1. Easy starting a simple web server and FTP, SFTP server 
Start a simple web server when starting the FTP server for the convenience of monitoring the FTP server configuration and status. 

Run the corresponding start script directly in the root directory of the OSS-FTP tool.

- Windows
Double click start.vbs to run the tool.

- Linux
```bash
$ bash start.sh
```

- Mac
```bash
$ bash start.command
```

In this method, the system will read the **config.json** file in the root directory of the OSS-FTP tool, and listens for FTP requests at the local 127.0.0.1:2048, and listens for SFTP requests at local 127.0.0.1:50000 port by default. At the same time, a web server will be activated at the 127.0.0.1:8192 port for the convenience of managing the FTP and SFTP server.

For the information in config.json , see below.

### 2. Lightweight staring a FTP server
Enter the ossftp directory.

```bash
$ python ftpserver.py
```
This will start a FTP server at the 127.0.0.1:2048 port. 

You can also specify the listening address and port among other information in parameters at the startup.
```bash
python ftpserver.py --listen_address=<ip address> --port=<your local port> --passive_ports=<your passive_ports like 51000~52000>--internal=<True/False> --loglevel=<DEBUG/INFO>
```
passive_ports: The data ports of FTP PASV mode.

If the internal value is "True", the FTP server will access the OSS through the intranet domain name.
If the internal value is "False", the FTP server will access the OSS through the internet domain name.
When the internal field is not specified, the FTP server will automatically probe the network status and prioritize intranet access to the OSS.

> For more information on domain names for OSS access, refer to https://help.aliyun.com/document_detail/oss/user_guide/endpoint_region.html。

The loglevel decides the level of the ftpserver log. The DEBUG-level output log provides more detailed information.

### 3. Lightweight staring a SFTP server
Enter the osssftp directory.

```bash
$ python sftpserver.py
```
This will start a FTP server at the 127.0.0.1:2048 port. 

You can also specify the listening address and port among other information in parameters at the startup.
```bash
python sftpserver.py --listen_address=<ip address> --port=<your local port> --internal=<True/False> --loglevel=<DEBUG/INFO>
```

If the internal value is "True", the SFTP server will access the OSS through the intranet domain name.
If the internal value is "False", the SFTP server will access the OSS through the internet domain name.
When the internal field is not specified, the SFTP server will automatically probe the network status and prioritize intranet access to the OSS.

> For more information on domain names for OSS access, refer tohttps://help.aliyun.com/document_detail/oss/user_guide/endpoint_region.html。

The loglevel decides the level of the sftpserver log. The DEBUG-level output log provides more detailed information.

## Connect to the FTP or SFTP server
We recommend you use [FileZilla Client]((https://filezilla-project.org/)) to connect to the FTP server. After downloading and installing the tool, you can connect it to the FTP server following the instructions below: 

- Host:  the FTP default host is 127.0.0.1, the SFTP default host is sftp://127.0.0.1.
- Logon type:  Normal. 
- User: access_key_id/bucket_name (Note: Here the "/" is necessary. It does not mean "or". For example, the user name 'tSxyiUM3NKswPMEp/test-hz-jh-002'). 
- Password: access_key_secret. 
- port: the FTP default port is 2048, the SFTP default port is 50000.

## Introduction of config.json
If you start this tools in easy startup mode, it will get configurations from config.json.

### startup parameters
- auto_start: whether auto start this tools after the computer starting or not, default value is 0 means no.
- control_port: the port of the web server，default is 8192。
- oss_protocol: the transport protocol of OSS, default is "https"
- popup_webui:1, whether popup the web configuration ui after servers starting or not, default value is 1 means yes.
- show_systray: whether show the tray after servers starting or not, default value is 1 means yes.

### FTP server parameters
- enable: whether enable the FTP server or not, default value is 1 means yes.
- address: the FTP server bind address, default value is "127.0.0.1".
- port: the FTP server listening port，default value is 2048。
- passive_ports: the FTP server passive ports, default value is "51000~52000"。
- bucket_endpoints: the endpoints of buckets, it should be in format of bucket_name.endpoint, multi endpoints should be spilt by ",". default value is a empty string "".
- buff_size: the size of upload buffer, the FTP server will pop up data to send to OSS after the buffer is full or the file is upload over. 
- log_level: the logger level, it's value is in (DEBUG，INFO，WARNING，ERROR，CRITICAL), default value is "DEBUG".

### SFTP server parameters
- enable: whether enable the SFTP server or not, default value is 1 means yes.
- address: the SFTP server bind address, default value is "127.0.0.1".
- port: the SFTP server listening port，default value is 2048.
- bucket_endpoints: the endpoints of buckets, it should be in format of bucket_name.endpoint, multi endpoints should be spilt by ",". default value is a empty string "".
- buff_size: the size of upload buffer, the SFTP server will pop up data to send to OSS after the buffer is full or the file is upload over. 
- log_level: the logger level, it's value is in (DEBUG，INFO，WARNING，ERROR，CRITICAL), default value is "DEBUG".

## Possible problems

**1. If the following error occurs during connection to the FTP server:**

```bash
$ 530 Can't list buckets, check your access_key. 
```

There are two possible reasons: 

a. The input access_key_id and access_key_secret contain errors. 
Solution: Enter the correct information and try again. 

b. The access_key used belongs to the RAM sub-account which has no permission for listing buckets. 
Solution:  Grant required permission to the RAM sub-account to use the FTP tool. To control RAM access to the OSS, refer to the [Access Control](https://www.aliyun.com/product/ram/)documentation. 

> - **Read-only access** The permissions required by the OSS FTP tool are listed below. 
 ['ListBuckets', 'GetBucketAcl', 'ListObjects', 'GetObject', 'HeadObject'].
>  To learn how to create an RAM sub-account with **read-only access** permission, refer to the illustrations on [How to achieve file sharing using RAM](https://help.aliyun.com/document_detail/oss/utilities/ossftp/build-file-share-by-ram.html). 

> - If you want to allow the RAM sub-account to **upload files**, you also need ['PutObject'].

> - If you want to allow the RAM sub-account to **delete objects**, you also need ['DeleteObject']. 

**2. If you are running the FTP server on Linux and encounter the following error when using FileZilla to connect to the server:**

> - 501 can't decode path (server filesystem encoding is ANSI_X3.4-1968)。

this is usually because of issues in local Chinese encoding.
Enter the following command in the terminal where you want to run start.sh, and then restart the program.

```bash
$ export LC_ALL=en_US.UTF-8; export LANG="en_US.UTF-8"; locale
```

**3. If the FTP server is already start, but cannot connect it:**

- First, ensure the FTP server has started successfully, you can use Telnet command to test it.
```bash
telnet 127.0.0.1 2048
```
- If the FTP server has started successfully, but cannot connect it yet, first considering the passive ports is forbid by the firewall or not.

**4. If connect server failed:**
- Please refer to the last tip to ensure the server has started successfully, considering use your accurate address or "0.0.0.0" instead of "127.0.0.1" in config.json.

## Run tests
Enter the *test* directory and run tests.
```bash
bash run_test.sh
```

## More documentation
[OSS FTP official homepage](https://help.aliyun.com/document_detail/oss/utilities/ossftp/install.html).
