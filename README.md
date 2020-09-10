# OSS-FTP

[![GitHub Version](https://badge.fury.io/gh/aliyun%2Foss-ftp.svg)](https://badge.fury.io/gh/aliyun%2Foss-ftp)
[![Software License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)

### [README of Chinese](https://github.com/aliyun/oss-ftp/blob/master/README.md)

## Introduction
OSS-FTP is an FTP server tool based on Alibaba Cloud OSS. It converts FTP requests into OSS requests for users to use the OSS in an FTP-like approach.

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
- Currently, the OSS FTP V1.0 does not support TLS encryption for the ease of installation and deployment. Because the FTP protocol implements plaintext transmission, **we recommend you run the FTP server and client on the same server to prevent password leaks** and access using 127.0.0.1:port.
- Rename and move operations are not supported. 
- Do not include Chinese characters in the path to which the installer package is unzipped.
- The FTP server's management control page may fail to be opened in older versions of Internet Explorer.
- Python versions supported by the FTP server:  Python2.6 and Python2.7.

## Start FTP server

Two methods are available:

1. Start a simple web server when starting the FTP server for the convenience of monitoring the FTP server configuration and status. 

Run the corresponding start script directly in the root directory of the FTP tool.

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

In this method, the system will read the **config.json** file in the root directory of the FTP tool, and listens for FTP requests at the local 127.0.0.1:2048 port by default. At the same time, a web server will be activated at the 127.0.0.1:8192 port for the convenience of managing the FTP server.


2. A lightweight startup mode where only one FTP server is initiated.
Enter the ossftp directory.

```bash
$ python ftpserver.py
```
This will start an FTP server at the 127.0.0.1:2048 port. 

You can also specify the listening address and port among other information in parameters at the startup.
```bash
python ftpserver.py --listen_address=<ip address> --port=<your local port> --passive_ports_start=<your passive ports start> --passive_ports_end=<your passive ports end> --internal=<True/False> --loglevel=<DEBUG/INFO>
```
If the internal value is "True", the FTP server will access the OSS through the intranet domain name.
If the internal value is "False", the FTP server will access the OSS through the internet domain name.
When the internal field is not specified, the FTP server will automatically probe the network status and prioritize intranet access to the OSS.

> For more information on domain names for OSS access, refer tohttps://help.aliyun.com/document_detail/oss/user_guide/endpoint_region.html。

The loglevel decides the level of the ftpserver log. The DEBUG-level output log provides more detailed information.

## Connect to the FTP server
We recommend you use [FileZilla Client]((https://filezilla-project.org/)) to connect to the FTP server. After downloading and installing the tool, you can connect it to the FTP server following the instructions below: 

- Host:  127.0.0.1.
- Logon type:  Normal. 
- User: access_key_id/bucket_name (Note: Here the "/" is necessary. It does not mean "or". For example, the user name 'tSxyiUM3NKswPMEp/test-hz-jh-002'). 
- Password: access_key_secret. 

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
**3. If the FTP server has already started, but ftp client cannot connect it.

> - First, ensure the FTP server is start success, you can use Telnet command to test it.
```bash
telnet 127.0.0.1 2048
```
> - If the FTP server has started successfully, but ftp client cannot connect it yet, first considering the passive ports is forbidden by the firewall, maybe you need add it to the whitelist.


## Run test
Enter the *test* directory and configure test.cfg. Then run {login.py, file.py, dir.py} with Python to run the OSS FTP-related tests.

## More documentation
[OSS FTP official homepage](https://help.aliyun.com/document_detail/oss/utilities/ossftp/install.html).
