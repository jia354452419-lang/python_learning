"""
3.7 K8s API 教学版：ACK 集群健康巡检（只读）
知识点：kubeconfig 认证、CoreV1Api/AppsV1Api、Pod 状态/重启计数、Deployment 副本、None 兜底

前置：本机 ~/.kube/config 存在（与 kubectl 共用凭证）
运行：python k8s_demo.py
"""
from kubernetes import client, config

# 认证：加载本机 kubeconfig（kubectl 用的同一个文件）
# 集群内部署时改用 config.load_incluster_config()（读 ServiceAccount token，3.3 提过的平台身份）
config.load_kube_config()

# 两个常用 API 组（对应 kubectl api-resources 里的分组）
v1 = client.CoreV1Api()    # Pod / Node / Event / Service / Namespace
apps = client.AppsV1Api()  # Deployment / StatefulSet / DaemonSet


def check_pod_phase():
    """巡检项 1：非 Running 的 Pod（Succeeded 是 Job 正常完成，不算异常）"""
    issues = []
    pods = v1.list_pod_for_all_namespaces()
    for pod in pods.items:
        phase = pod.status.phase
        if phase not in ("Running", "Succeeded"):
            issues.append({
                "namespace": pod.metadata.namespace,
                "pod": pod.metadata.name,
                "phase": phase,
            })
    return issues


def check_pod_restarts(min_restarts=1):
    """巡检项 2：容器重启计数（"Pod 异常重启怎么监控"的代码级答案）

    坑位：Pending Pod 的 container_statuses 是 None，直接迭代炸 TypeError，必须 or [] 兜底
    """
    issues = []
    pods = v1.list_pod_for_all_namespaces()
    for pod in pods.items:
        for cs in pod.status.container_statuses or []:
            if cs.restart_count >= min_restarts:
                issues.append({
                    "namespace": pod.metadata.namespace,
                    "pod": pod.metadata.name,
                    "container": cs.name,
                    "restarts": cs.restart_count,
                })
    return issues


def check_deployment_replicas():
    """巡检项 3：Deployment 就绪副本 != 期望副本

    坑位：ready_replicas 可能是 None（刚创建还没就绪），不能直接与 int 比较
    """
    issues = []
    deploys = apps.list_deployment_for_all_namespaces()
    for d in deploys.items:
        desired = d.spec.replicas or 0
        ready = d.status.ready_replicas or 0
        if ready != desired:
            issues.append({
                "namespace": d.metadata.namespace,
                "deployment": d.metadata.name,
                "ready": ready,
                "desired": desired,
            })
    return issues


def print_report(title, issues):
    print(f"\n=== {title}: {len(issues)} 项 ===")
    for item in issues:
        print(" ", item)


if __name__ == "__main__":
    print_report("非 Running Pod", check_pod_phase())
    print_report("容器重启计数 >= 1", check_pod_restarts())
    print_report("Deployment 副本不齐", check_deployment_replicas())
