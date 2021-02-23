# -*- coding: utf-8 -*-

from util import *
import unittest
import paramiko
from paramiko import AuthenticationException
import socket
import time

class SftpTest2(unittest.TestCase):
    def setUp(self):
        self.host = get_value_from_config("sftpconfig", "host")
        self.sftp_port = int(get_value_from_config("sftpconfig", "sftp_port"))
        self.bucket_name = get_value_from_config("sftpconfig", "normal_bucket")
        self.aliyun_id = get_value_from_config("sftpconfig", "normal_id")
        self.aliyun_secret = get_value_from_config("sftpconfig", "normal_key")
        self.aliyun_login_username = self.aliyun_id + '/' + self.bucket_name

        self.username = get_value_from_config("sftpconfig", "account_name")
        self.password =get_value_from_config("sftpconfig", "account_password")

    def test_sftp_login_with_user_id(self):
        s = socket.socket()
        s.settimeout(10)
        s.connect((self.host, self.sftp_port))

        tran = paramiko.Transport(s)

        try:
            tran.connect(username=self.username, password=self.password)
        except Exception as e:
            raise (e, 'sftp login error.')
        finally:
            tran.close()

    def test_sftp_login_with_user_id_error(self):
        s = socket.socket()
        s.settimeout(10)
        s.connect((self.host, self.sftp_port))

        tran = paramiko.Transport(s)

        try:
            tran.connect(username=self.username, password=self.password + 'error')
        except AuthenticationException as e:
            pass
        finally:
            tran.close()

    def test_sftp_login_with_aliyun_id(self):
        s = socket.socket()
        s.settimeout(10)
        s.connect((self.host, self.sftp_port))

        tran = paramiko.Transport(s)

        try:
            tran.connect(username=self.aliyun_login_username, password=self.aliyun_secret)
        except Exception as e:
            raise (e, 'sftp login error.')
        finally:
            tran.close()

    def test_sftp_login_with_aliyun_id_error(self):
        s = socket.socket()
        s.settimeout(10)
        s.connect((self.host, self.sftp_port))
        tran = paramiko.Transport(s)

        try:
            tran.connect(username=self.aliyun_login_username+'-error', password=self.aliyun_secret)
        except AuthenticationException as e:
            pass
        finally:
            tran.close()

        s = socket.socket()
        s.settimeout(10)
        s.connect((self.host, self.sftp_port))
        tran = paramiko.Transport(s)
        try:
            tran.connect(username=self.aliyun_login_username, password=self.aliyun_secret + '-error')
        except AuthenticationException as e:
            pass
        finally:
            tran.close()

        s = socket.socket()
        s.settimeout(10)
        s.connect((self.host, self.sftp_port))
        tran = paramiko.Transport(s)
        try:
            tran.connect(username=self.aliyun_id+'-error' + '/' + self.bucket_name, password=self.aliyun_secret + '-error')
        except AuthenticationException as e:
            pass
        finally:
            tran.close()

    def test_sftp_login_error(self):
        s = socket.socket()
        s.settimeout(10)
        s.connect((self.host, self.sftp_port))
        tran = paramiko.Transport(s)

        try:
            tran.connect(username=self.username+'-error', password=self.password)
        except AuthenticationException as e:
            pass
        finally:
            tran.close()

        s = socket.socket()
        s.settimeout(10)
        s.connect((self.host, self.sftp_port))
        tran = paramiko.Transport(s)
        try:
            tran.connect(username=self.username, password=self.password + '-error')
        except AuthenticationException as e:
            pass
        finally:
            tran.close()

        s = socket.socket()
        s.settimeout(10)
        s.connect((self.host, self.sftp_port))
        tran = paramiko.Transport(s)
        try:
            tran.connect(username=self.aliyun_id+'-error' + '/' + self.bucket_name, password=self.password + '-error')
        except AuthenticationException as e:
            pass
        finally:
            tran.close()

    def test_login_with_private_key(self):
        s = socket.socket()
        s.settimeout(10)
        s.connect((self.host, self.sftp_port))

        tran = paramiko.Transport(s)

        key_file = 'test-sftp-private-key'
        rsa_key = paramiko.RSAKey.generate(bits=2048)
        rsa_key.write_private_key_file(key_file)

        try:
            private_key = paramiko.RSAKey.from_private_key_file(key_file)
            tran.connect(username='test', pkey=private_key)
            self.fail("should be failed here.")
        except:
            pass

        tran.close()
        safe_remove_file(key_file)

    def gen_transport_and_client(self):
        s = socket.socket()
        s.settimeout(10)
        s.connect((self.host, self.sftp_port))

        transport = paramiko.Transport(s)
        transport.connect(username=self.username, password=self.password)

        sftp_client = paramiko.SFTPClient.from_transport(transport)

        return transport, sftp_client

    def test_put_get_small_file(self):
        transport, sftp_client = self.gen_transport_and_client()
        local_file_name = "test_sftp_put_small.txt"
        remote_file_name = local_file_name
        download_file_name = local_file_name + '-download'
        gen_file(local_file_name, 512)

        try:
            sftp_client.put(local_file_name, remote_file_name)
            sftp_client.get(remote_file_name, download_file_name)

            file_md5 = get_file_md5(local_file_name)
            down_file_md5 = get_file_md5(download_file_name)

            self.assertEqual(file_md5, down_file_md5)
        finally:
            sftp_client.remove(remote_file_name)
            transport.close()
            safe_remove_file(local_file_name)
            safe_remove_file(download_file_name)

    def test_put_get_big_file(self):
        transport, sftp_client = self.gen_transport_and_client()
        local_file_name = "test_sftp_put_big.txt"
        remote_file_name = local_file_name
        download_file_name = local_file_name + '-download'
        gen_file(local_file_name, 2 * 1024 * 1024)

        try:
            sftp_client.put(local_file_name, remote_file_name)
            sftp_client.get(remote_file_name, download_file_name)

            file_md5 = get_file_md5(local_file_name)
            down_file_md5 = get_file_md5(download_file_name)

            self.assertEqual(file_md5, down_file_md5)
        finally:
            sftp_client.remove(remote_file_name)
            transport.close()
            safe_remove_file(local_file_name)
            safe_remove_file(download_file_name)

    def test_delete_file(self):
        transport, sftp_client = self.gen_transport_and_client()
        local_file_name = "test_sftp_delete_file.txt"
        remote_file_name = local_file_name
        gen_file(local_file_name, 2 * 1024 * 1024)

        try:
            sftp_client.put(local_file_name, remote_file_name)
            sftp_client.remove(remote_file_name)
        finally:
            transport.close()
            safe_remove_file(local_file_name)

    def test_remove_dir(self):
        transport, sftp_client = self.gen_transport_and_client()

        local_file_name = "test_remove_dir_file.txt"
        remote_dir = 'test-sftp-rm-dir'
        remote_file_name = remote_dir + '/' +local_file_name
        download_file_name = local_file_name + '-download'

        gen_file(local_file_name, 512)

        try:
            sftp_client.put(local_file_name, remote_file_name)
            sftp_client.get(remote_file_name, download_file_name)
            sftp_client.rmdir(remote_dir)
        except Exception as e:
            safe_remove_file(local_file_name)
            safe_remove_file(download_file_name)
            transport.close()
            raise e

        try:
            sftp_client.get(remote_file_name, download_file_name)
        except:
            pass

        transport.close()
        safe_remove_file(local_file_name)
        safe_remove_file(download_file_name)

    def test_list_dir(self):
        transport, sftp_client = self.gen_transport_and_client()

        remote_dir = 'test-sftp-list-dir'
        sftp_client.rmdir(remote_dir)

        local_file_name = "test_list_dir_file.txt"
        remote_sumb_dir = 'sub'
        remote_file_name1 = remote_dir + '/' + remote_sumb_dir + '/' + local_file_name
        remote_file_name2 = remote_dir + '/' + local_file_name

        gen_file(local_file_name, 512)

        try:
            sftp_client.put(local_file_name, remote_file_name1)
            sftp_client.put(local_file_name, remote_file_name2)
            list_result = sftp_client.listdir(remote_dir)
            self.assertEqual(2, len(list_result))
            self.assertTrue('sub' in list_result)
            self.assertTrue(local_file_name in list_result)
        finally:
            safe_remove_file(local_file_name)
            sftp_client.rmdir(remote_dir)
            transport.close()

    def test_mkdir(self):
        transport, sftp_client = self.gen_transport_and_client()
        remote_dir = 'test-sftp-mkdir'
        sftp_client.rmdir(remote_dir)
        download_file_name = remote_dir + '-download'

        try:
            sftp_client.mkdir(remote_dir)
            sftp_client.get(remote_dir+'/', download_file_name)
            file_size = os.path.getsize(download_file_name)
            self.assertEqual(0, file_size)
        finally:
            sftp_client.rmdir(remote_dir)
            transport.close()
            safe_remove_file(download_file_name)

    def test_unsupport_rename(self):
        transport, sftp_client = self.gen_transport_and_client()

        local_file_name = "test_sftp_rename_file.txt"
        remote_file_name = local_file_name
        gen_file(local_file_name, 3)

        try:
            sftp_client.put(local_file_name, remote_file_name)
            sftp_client.rename(remote_file_name, remote_file_name + '-rename.txt')
        except IOError:
            pass
        finally:
            sftp_client.remove(remote_file_name)
            transport.close()
            safe_remove_file(local_file_name)

    def test_unsupport_symlink(self):
        transport, sftp_client = self.gen_transport_and_client()

        local_file_name = "test_sftp_symlink_file.txt"
        remote_file_name = local_file_name
        gen_file(local_file_name, 3)

        try:
            sftp_client.put(local_file_name, remote_file_name)
            sftp_client.symlink(remote_file_name, remote_file_name + '-symlinktxt')
        except IOError:
            pass
        finally:
            sftp_client.remove(remote_file_name)
            transport.close()
            safe_remove_file(local_file_name)

    def test_unsupport_readlink(self):
        transport, sftp_client = self.gen_transport_and_client()

        local_file_name = "test_sftp_readlink_file.txt"
        remote_file_name = local_file_name
        gen_file(local_file_name, 3)

        try:
            sftp_client.put(local_file_name, remote_file_name)
            sftp_client.readlink(remote_file_name)
        except IOError:
            pass
        finally:
            sftp_client.remove(remote_file_name)
            transport.close()
            safe_remove_file(local_file_name)


if __name__ == '__main__':
    print('\n\nstart test %s' % __file__)
    t = TestSftpThread("sftp-thread", bucket_endpoints="test-wrong-bucket.oss-cn-shenzhen.aliyuncs.com")
    t.daemon = True
    t.start()
    time.sleep(2)
    unittest.main()

