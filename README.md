# OSS FTP Server (试用版)

## what's this?
It's a FTP Server, you can access this FTP Server by general FTP Client, and read/write file directly to OSS.

## how it works?
It has a abstract file system over OSS, all incoming FTP Requests will operate on that file system, finally read/write files on OSS.

## how to install?

* install such dependence:

```bash      
$ apt-get install libffi-dev
$ apt-get install libssl-dev
``` 
or:

```bash
$ yum install libffi
$ yum install openssl-devel
```

* download the package, and execute the following commd:

```bash
$ python setup.py install
```

## how to use?
      
* start ftpserver:

```bash
$ python ftpserver_ssl.py
```     
the ftpserver will choose domain(internal domain or public domain), and internal domain is preferred.

or

```bash
python ftpserver_ssl.py --port=<your local port> --internal=<True/False>
```        

if --internal="True", the ftpserver will access oss from the internal domain.
if --internal="False", the ftpserver will access oss from the public domain.
 
> internal domain is like "oss-cn-hangzhou-internal.aliyuncs.com"
  for more info, please refer https://help.aliyun.com/document_detail/oss/user_guide/endpoint_region.html
    
* connect to ftpserver:
      
you can use general ftp client to access this FTP Server, FileZilla is recommended
about FTP Account:

        username:  ACCESS_ID/BUCKET
        password: ACCESS_KEY
        port:     990

for example:

        username: qwertyasdfg/this-is-bucket-name
        password: zxcvbgfdsa
