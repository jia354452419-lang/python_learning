import argparse



argparser = argparse.ArgumentParser(description='ssh巡检')
argparser.add_argument('-w','--workers',type=int, default=3, help='并发数')
argparser.add_argument('-host','--host',type=str,required=True,help='ip地址')
argparser.add_argument('-p','--port',type=int,default=22,help='端口号')
argparser.add_argument('-u','--user',type=str,default='root',help='用户名')
argparser.add_argument('--warning_percent',type=int,default=85,help='告警阈值')
args = argparser.parse_args()
print(type(argparser.parse_args()))

print(f"{args.user}@{args.host}:{args.port} 并发数：{args.workers}  告警阈值: {args.warning_percent}%")