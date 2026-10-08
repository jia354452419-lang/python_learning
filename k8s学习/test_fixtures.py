"""
3.7 测试数据构造脚本：给巡检服务造靶子（kubectl 的 Python 等价物，同一 kubeconfig 同一 apiserver）
每个对象对应一个巡检项的触发路径，含两个"不该被报"的阴性对照

用法：
    python test_fixtures.py            # 创建全部靶子
    python test_fixtures.py --status   # 查看各对象状态与等待原因（比 k8s_demo 多一层 Why）
    python test_fixtures.py --cleanup  # 删除整个命名空间，级联清理
"""
import sys
from kubernetes import client, config
from kubernetes.client.rest import ApiException

config.load_kube_config()
v1 = client.CoreV1Api()
apps = client.AppsV1Api()

NS = "k8s-check-test"
T = 15


def make_pod(name, image, command=None, restart_policy="Always", cpu_request=None):
    resources = client.V1ResourceRequirements(requests={"cpu": cpu_request}) if cpu_request else None
    container = client.V1Container(name="main", image=image, command=command, resources=resources)
    return client.V1Pod(
        metadata=client.V1ObjectMeta(name=name, labels={"test-case": name}),
        spec=client.V1PodSpec(containers=[container], restart_policy=restart_policy),
    )


def make_pod_containers(name, containers, restart_policy="Always"):
    container_objs = [
        client.V1Container(name=cname, image=image, command=cmd)
        for cname, image, cmd in containers
    ]
    return client.V1Pod(
        metadata=client.V1ObjectMeta(name=name, labels={"test-case": name}),
        spec=client.V1PodSpec(containers=container_objs, restart_policy=restart_policy),
    )


def make_deploy(name, image, replicas):
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": name}),
        spec=client.V1PodSpec(containers=[client.V1Container(name="main", image=image)]),
    )
    return client.V1Deployment(
        metadata=client.V1ObjectMeta(name=name),
        spec=client.V1DeploymentSpec(
            replicas=replicas,
            selector=client.V1LabelSelector(match_labels={"app": name}),
            template=template,
        ),
    )


# (名字, 镜像, 命令, 重启策略, CPU请求)
PODS = [
    ("pending-unschedulable", "busybox:1.36", ["sh", "-c", "sleep 3600"], "Never", "100"),
    ("pending-imagepull", "nginx:1.999.999-notexist", None, "Never", None),
    ("crashloop-counter", "busybox:1.36", ["sh", "-c", "exit 1"], "Always", None),
    ("succeeded-job", "busybox:1.36", ["sh", "-c", "echo done"], "Never", None),
    ("failed-job", "busybox:1.36", ["sh", "-c", "exit 2"], "Never", None),
]

# 多容器 Pod（sidecar 模式 + 故意一个坏的）：一栋房子三个住户，验证巡检发现粒度是容器级
# 注意 restartPolicy 是 Pod 级的，三个容器共享——K8s 不支持按容器单独设重启策略
MULTI_POD = ("multi-container-demo", [
    ("app", "nginx:1.27", None),
    ("log-shipper", "busybox:1.36", ["sh", "-c", "while true; do date; sleep 30; done"]),
    ("broken-sidecar", "busybox:1.36", ["sh", "-c", "exit 1"]),
], "Always")

# (名字, 镜像, 副本数)
DEPLOYS = [
    ("deploy-replica-mismatch", "nginx:1.888.888-notexist", 3),
    ("deploy-healthy", "nginx:1.27", 2),
]


def create_or_skip(title, fn, *args):
    try:
        fn(*args, _request_timeout=T)
        print(f"[+] {title}")
    except ApiException as e:
        if e.status == 409:
            print(f"[=] {title} 已存在，跳过")
        else:
            print(f"[!] {title} 失败: {e.status} {e.reason}")


def create():
    create_or_skip(f"Namespace/{NS}", v1.create_namespace,
                   client.V1Namespace(metadata=client.V1ObjectMeta(name=NS)))
    for name, image, cmd, rp, cpu in PODS:
        create_or_skip(f"Pod/{name}", v1.create_namespaced_pod, NS, make_pod(name, image, cmd, rp, cpu))
    mname, mcontainers, mrp = MULTI_POD
    create_or_skip(f"Pod/{mname}", v1.create_namespaced_pod, NS, make_pod_containers(mname, mcontainers, mrp))
    for name, image, replicas in DEPLOYS:
        create_or_skip(f"Deployment/{name}", apps.create_namespaced_deployment, NS,
                       make_deploy(name, image, replicas))


def status():
    pods = v1.list_namespaced_pod(NS, _request_timeout=T)
    print(f"{'POD':<26} {'PHASE':<10} CONTAINERS(restarts)  REASON")
    for p in pods.items:
        cs_list = p.status.container_statuses or []
        restarts = " ".join(f"{cs.name}={cs.restart_count}" for cs in cs_list) or "-"
        reason = ""
        for cs in cs_list:
            if cs.state and cs.state.waiting:
                reason = cs.state.waiting.reason or ""
        if not reason and p.status.phase == "Pending":
            for cond in (p.status.conditions or []):
                if cond.type == "PodScheduled" and cond.status == "False":
                    reason = cond.reason or ""
        print(f"{p.metadata.name:<26} {p.status.phase:<10} {restarts}  {reason}")
    print()
    for d in apps.list_namespaced_deployment(NS, _request_timeout=T).items:
        print(f"Deployment/{d.metadata.name}: ready={d.status.ready_replicas or 0} desired={d.spec.replicas}")


def cleanup():
    try:
        v1.delete_namespace(NS, _request_timeout=T)
        print(f"[-] Namespace/{NS} 删除已提交（级联清理全部对象）")
    except ApiException as e:
        if e.status == 404:
            print(f"[=] Namespace/{NS} 不存在")
        else:
            print(f"[!] 删除失败: {e.status} {e.reason}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "--cleanup":
        cleanup()
    elif mode == "--status":
        status()
    else:
        create()
