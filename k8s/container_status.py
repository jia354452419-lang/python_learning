import sys
import logging
from logging.handlers import RotatingFileHandler
from kubernetes import client, config
from pathlib import Path
from datetime import datetime

# 引入db模块
from container_status_db import insert_pods_status


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

def get_k8s_config():
    config.load_kube_config()

config.load_kube_config()
# 创建API对象
core = client.CoreV1Api()
apps = client.AppsV1Api()



# 获取pod运行状态
def pods_status() -> list:
    """
    获取k8s集群的pod运行状态
    :return: list
    """
    result = []
    group_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pods = core.list_pod_for_all_namespaces(_request_timeout=6)
    for pod in pods.items:
        if pod.status.phase == "Running" or pod.status.phase == "Succeeded":
            summarize = "OK"
            detail = f"{pod.metadata.name}运行正常"
            log.info(f"{pod.metadata.name:<50} -- {pod.status.phase}")
        else:
            summarize = "ERROR"
            detail = f"ERROR, 请注意pod {pod.metadata.name} 状态"
            log.error(f"{pod.metadata.name:<50} -- {pod.status.phase}")

        result_pod = {
            "group_id": group_id,
            "name":pod.metadata.name,
            "container_name": "N/A",
            "spec":"Running",
            "status":pod.status.phase,
            "summarize": summarize,
            "detail": detail,
            "check_type": "pods_status"
        }
        # 数据插入数据库
        insert_to_db(result_pod)
        # 数据归档
        result.append(result_pod)
    return result


# 获取容器重启状态
def containers_status() -> list:
    """
    获取k8s集群容器重启状态
    :return: list
    """
    result = []
    group_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pods = core.list_pod_for_all_namespaces(_request_timeout=6)
    for pod in pods.items:
        pod_name = pod.metadata.name
        for container in pod.status.container_statuses or []:
            if container.restart_count == 0:
                summarize = "OK"
                detail = "运行正常"
                log.info(f"{pod_name:<50} -- {container.name:<15}  -- {container.restart_count}")
            else:
                summarize = 'ERROR'
                detail = f"ERROR, 容器 {container.name} 有重启记录，请尽快排查"
                log.error(f"{pod_name:<50} -- {container.name:<15}  -- {container.restart_count}")

            result_container = {
                "group_id": group_id,
                "name":pod_name,
                "container_name":container.name,
                "spec":0,
                "status":container.restart_count,
                "summarize": summarize,
                "detail": detail,
                "check_type": "containers_restart"
            }
            # 数据插入数据库
            insert_to_db(result_container)
            # 数据归档
            result.append(result_container)
    return result


# 获取副本数
def replica_deployment_status():
    """
    获取k8s集群deployment副本数当前状态与期望状态
    """
    result = []
    group_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    deployments = apps.list_deployment_for_all_namespaces(_request_timeout=6)
    for deployment in deployments.items:
        ready_num = deployment.status.ready_replicas or 0
        if ready_num == deployment.spec.replicas:
            summarize = "OK"
            detail = "运行正常"
            log.info(f"{deployment.metadata.name:<50} -- now:{ready_num:<12} -- spec:{deployment.spec.replicas}")
        else:
            summarize = "ERROR"
            detail = f"ERROR，副本 {deployment.metadata.name} 数不一致，请尽快排查"
            log.error(f"{deployment.metadata.name:<50} -- now:{ready_num:<12} -- spec:{deployment.spec.replicas}")
        result_deployment = {
            "group_id":group_id,
            "name":deployment.metadata.name,
            "container_name": "N/A",
            "spec":deployment.spec.replicas,
            "status":ready_num,
            "summarize": summarize,
            "detail": detail,
            "check_type": "replica_deployment"
        }
        # 数据插入数据库
        insert_to_db(result_deployment)
        # 数据归档
        result.append(result_deployment)
    return result


# 数据处理
def insert_to_db(result: dict):

    insert_pods_status(result["group_id"],result["name"],result["container_name"],result["spec"],result["status"],result["summarize"],result["detail"],result["check_type"])






def main():

    # 开启日志
    set_up_log()

    #
    get_k8s_config()


    # 主进程
    print("\n---------------------- 获取pod运行状态 ----------------------\n")
    a = pods_status()
    print("\n---------------------- 获取容器重启状态 ----------------------\n")
    b = containers_status()
    print("\n----------------------    获取副本数   ----------------------\n")
    c = replica_deployment_status()

if __name__ == "__main__":
    main()

# kubectl api-resources