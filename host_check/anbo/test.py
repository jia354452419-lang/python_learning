# import re
# a = "    最短 = 10ms，最长 = 12ms，平均 = 10ms "
#
# m = re.search(r'(\d+)ms\s$',a)
# print(m.group(1))



with open('hosts.txt', 'r', encoding='utf-8') as hosts:
    for i in hosts.readlines():
        print(i,end="")
    # a = hosts.readlines()
    # print(a)