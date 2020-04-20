# -*- coding: utf-8 -*-

app_name = "ossftp"
max_send_retry_times = 3
send_data_buff_size = 10 * 1024 * 1024
oss_trans_protocol = 'https'

def set_data_buff_size(capacity):
    global send_data_buff_size
    send_data_buff_size = capacity

def get_data_buff_size():
    return send_data_buff_size

def set_oss_trans_protocol(protocol):
    global oss_trans_protocol
    oss_trans_protocol = protocol

def get_oss_trans_protocol():
    return oss_trans_protocol


