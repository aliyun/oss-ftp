# 如何使用OSS FTP工具实现网站的远程附件功能

------
### 前言：

网站远程附件功能是指将用户上传的附件直接存储到远端的存储服务器，一般是通过FTP的方式存储到远程的FTP服务器。带来的好处有以下几点：
> * 减少web服务器的流量 
> * 减轻web服务器负载
> * 节约web服务的存储空间

目前Discuz论坛、phpwind论坛、Wordpress个人网站等都支持远程附件功能。

----------

### 关于OSS:
对象存储（Object Storage Service，简称OSS），是阿里云提供的海量、安全和高可靠的云存储服务。详细信息请参考[oss官网主页](http://www.aliyun.com/product/oss/ "http://www.aliyun.com/product/oss/")

----------

### 关于OSS FTP工具:
OSS FTP是一个基于OSS存储提供FTP访问的工具。详情请参考


----------


### 准备工作：
申请OSS账号，并且创建一个**public-read**的bucket。这里需要权限为public-read是因为后面需要匿名访问。

----------

### Disquz用户如何使用OSS存储远程附件
作者所用Disquz版本为**Discuz! X3.1**，下面是作者的详细设置流程，亲测可行。


*  登录Discuz站点，进入管理界面后，先点击**全局**，再点击**上传设置**，如下图所示
   
![全局入口](http://test-hz-jh-002.oss-cn-hangzhou.aliyuncs.com/disquz-main.png)

*  选择**远程附件**，然后开始设置
![设置1](http://test-hz-jh-002.oss-cn-hangzhou.aliyuncs.com/disquz-setting-1.png)

如上图所示：

    1.  选择**启用远程附件**
    
    2.  启用SSL链接为 **否**
    
    3.  填写你的FTP服务器地址
    
    4.  FTP服务的端口号，默认为**2048**
    
    5.  FTP登录用户名，格式为“**AccessKeyID/BukcetName**”
    
    6.  FTP的登录密码，为**AceessKeySecrete**
    
    7.  被动模式连接，选择默认的“**是**“即可
    
![设置2](http://test-hz-jh-002.oss-cn-hangzhou.aliyuncs.com/disquz-setting-2.png)

    8.  远程附件目录，填 **.** 表示在Bucket的根目录下创建上传目录
    9.  远程访问URL, 填http://BucketName.Endpoint即可
        作者这里填的是 http://test-hz-jh-002.oss-cn-hangzhou.aliyuncs.com
        **注意BucketName要和Endpoint匹配**
    10. 设置好后，可以点击测试远程附件，如果成功则会出现如下画面

![test](http://test-hz-jh-002.oss-cn-hangzhou.aliyuncs.com/disquz-test.png)

*  发帖验证

好了，现在我们去论坛发帖试试。
随意找个板块，发贴时上传图片附件如下所示

![post](http://test-hz-jh-002.oss-cn-hangzhou.aliyuncs.com/disquz-post.png)

在图片上右键点击，选择在“新建标签页”中打开图片，如下所示

![post](http://test-hz-jh-002.oss-cn-hangzhou.aliyuncs.com/disquz-img-assert.png)

这里看到浏览器中图片的URL为 http://test-hz-jh-002.oss-cn-hangzhou.aliyuncs.com/forum/201512/18/171012mzvkku2z3na2w2wa.png, 这就表示图片已经上传到了OSS的test-hz-jh-002中。

----------


### Phpwind用户如何使用OSS存储远程附件
作者所用版本为phpwind8.7, 以下为详细设置流程，其实跟discuz的设置方式基本一致。

*  登录站点

进入管理界面，依次选择**全局**－**上传设置**－**远程附件**
![phpwind全局](http://test-hz-jh-002.oss-cn-hangzhou.aliyuncs.com/phpwind-main.png)

*  开始设置

![phpwind setting](http://test-hz-jh-002.oss-cn-hangzhou.aliyuncs.com/phpwind-setting.png)

这里的设置方法和disqus中的设置一样, 具体参数含义请参考上文

*  发帖验证

phpwind不能在设置好直接点击测试，我们这里发带图片的帖子来验证下

![phpwind post](http://test-hz-jh-002.oss-cn-hangzhou.aliyuncs.com/phpwind-post.png)

在图片点击右键，在新建标签页中打开图片，可以看到下图

![phpwind img assert](http://test-hz-jh-002.oss-cn-hangzhou.aliyuncs.com/phpwind-img-assert.png)

通过图中的URL，我们可以判断图片已经上传到了OSS的test-hz-jh-002 Bucket中。

----------


### Wordpress用户如何使用OSS存储远程附件
wordpress本身是不支持远程附件功能的，但是可以通过第三方的插件来做远程附件。作者所用wordpress版本为**4.3.1**, 所用插件为**Hacklog Remote Attachment**，以下为具体设置步骤

*  登录wordpress站点，选择安装插件，搜关键词FTP,选择**Hacklog Remote Attachment**安装

![wordpress plugin](http://test-hz-jh-002.oss-cn-hangzhou.aliyuncs.com/wordpress-plugin.png)

*  设置

>  *   FTP服务器填其ip地址或域名
>  *   FTP服务器端口填2048（默认）
>  *   FTP用户名为AccessKeyID/BucketName
>  *   FTP密码为AccessKeySecret
>  *   远程基本URL填 http://BucketName.Endpoint
>  *   FTP远程路径填wp(可自定义)，注意不要加/
>  *   HTTP远程路径填.即可

具体信息见下图的配置

![wordpress setting](http://test-hz-jh-002.oss-cn-hangzhou.aliyuncs.com/wordpress-setting.png)

*  验证

设置好之后，点击保存的同时，会做测试，测试结果会在页面上方显示，如下图所示表示测试成功

![wordpress test](http://test-hz-jh-002.oss-cn-hangzhou.aliyuncs.com/wordpress-save-and-test.png)

*  发布新文章， 并插入图片

现在开始写一篇新文章，并测试远程附件。创建好文章后，点击添加媒体来上传附件

![wordpress new post](http://test-hz-jh-002.oss-cn-hangzhou.aliyuncs.com/wordpress-new-post.png)

上传附件如下图所示

![wordpress upload img](http://test-hz-jh-002.oss-cn-hangzhou.aliyuncs.com/wordpress-upload-img.png)

*  上传完附件，点击发布，即可看到文章了。

![wordpress post](http://test-hz-jh-002.oss-cn-hangzhou.aliyuncs.com/wordpress-post.png)

仍然通过右键点击图片，通过新建链接来打开图片即可看到图片的URL如下图所示
![wordpress assert](http://test-hz-jh-002.oss-cn-hangzhou.aliyuncs.com/wordpress-img-assert.png)

通过图片的URL，我们可以判定图片已经成功上传到了OSS
