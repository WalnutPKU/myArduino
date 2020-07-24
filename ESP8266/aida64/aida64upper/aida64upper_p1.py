# -*- coding: utf-8 -*-
"""
Created on 2020-07-23 23:36:03

@author: Walnut

"""

import mmap
import xml.dom.minidom
import serial
import time

while True:
    # 读取AIDA64共享内存数据，参见文档https://www.aida64.co.uk/user-manual/external-applications
    # 10000是读取的长度值，并不知道实际数据的长度，如果实际数据超出此区域需要增加长度.
    # 请求的长度多于实际长度时自动填0. 实际数据中\x00后面还有一些内容，原因不明，需在\x00出现时提前截断.
    # consider using multiprocessing.shared_memory for python 3.8+
    mm = mmap.mmap(-1, 10000, "AIDA64_SensorValues", mmap.ACCESS_READ)
    # 原生数据只有"一行"，直接readline获得b""二进制串，转码为普通ascii字符串，x00空白字符截止
    raw = ""
    for i in range(mm.size()):
        c = mm.read(1)
        if c == b'\x00':
            break
        raw = raw + c.decode('ascii')
    mm.close()
    # 原生数据没有根元素，其实不符合XML格式规范，套上根元素方便解析
    xmlstr = "<AIDA64>" + raw + "</AIDA64>"
    # XML转DOM树，参考资料https://www.runoob.com/python/python-xml.html
    DOMTree = xml.dom.minidom.parseString(xmlstr)
    root = DOMTree.documentElement
    # 共6类数据，生成相应的list，拼接到aidalist
    groups = ["sys", "fan", "temp", "duty", "volt", "pwr"]
    aidalist = []
    for g in groups:
        aidalist.extend(root.getElementsByTagName(g))   
    # 将在elist中的参数拷贝到scomdict中
    scomdict = {}
    elist = ["SCPUCLK", "SCPUUTI", "VCPU", "TCPU"]
    for element in aidalist:
        eid = element.getElementsByTagName('id')[0].childNodes[0].data
        edata = element.getElementsByTagName('value')[0].childNodes[0].data
        if eid == "SCPUCLK":
            edata = "%s"%(float(edata) / 1000)
        if eid in elist:
            scomdict[eid] = edata
    # ESP8266使用的波特率为1500000
    scom = serial.Serial("COM4", 1500000)
    for key in scomdict:
        msg = "?" + key + "=" + scomdict[key] + "!"
        print(msg)
        scom.write(msg.encode("utf-8"))
    scom.close()
    time.sleep(1)
