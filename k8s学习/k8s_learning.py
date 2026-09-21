import sys
import logging
from logging.handlers import RotatingFileHandler
from kubernetes import client, config
from pathlib import Path

# 日志
log = logging.getLogger(__name__)
def set_up_log():
    log.level = logging.DEBUG

    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setLevel(logging.INFO)
    screen_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    date_handler = logging.handlers.TimedRotatingFileHandler( Path(__file__).parent / "k8s.log",when="midnight",backupCount=2, encoding="utf-8")
    date_handler.setLevel(logging.DEBUG)
    date_handler.setFormatter(logging.Formatter('%(asctime)s  - %(levelname)s - %(message)s'))

    log.addHandler(screen_handler)
    log.addHandler(date_handler)


# 获取配置文件
config.load_kube_config()

# 创建API对象
core = client.CoreV1Api()
apps = client.AppsV1Api()

# 获取pod运行状态
def pods_status():
    pods = core.list_namespaced_pod(namespace='k8s-check-test')
    for pod in pods.items:
        print(f"{pod.metadata.name:<50} -- {pod.status.phase}")

# 获取容器重启状态
def containers_status():
    pods = core.list_namespaced_pod(namespace='k8s-check-test')
    for pod in pods.items:
        pod_name = pod.metadata.name
        for container in pod.status.container_statuses or []:
            print(f"{pod_name:<50} -- {container.name:<15}  -- {container.restart_count}")

# 获取副本数
def replica_deployment_status():
    deployments = apps.list_namespaced_deployment(namespace='k8s-check-test')
    for deployment in deployments.items:
        ready_num = deployment.status.ready_replicas or 0
        print(f"{deployment.metadata.name:<50} -- now:{ready_num:<12} -- spec:{deployment.spec.replicas}")



def main():
    print("\n---------------------- 获取pod运行状态 ----------------------\n")
    pods_status()
    print("\n---------------------- 获取容器重启状态 ----------------------\n")
    containers_status()
    print("\n----------------------    获取副本数   ----------------------\n")
    replica_deployment_status()

if __name__ == "__main__":
    main()

# kubectl api-resources