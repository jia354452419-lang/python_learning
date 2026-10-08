"""
模型对象 vs 原生 dict：为什么 k8s 客户端能用 .xxx 取值
- 客户端把 API 返回的 JSON 反序列化成类实例（V1Pod 等），JSON 键变成属性
- print 出来的"字典"是 to_dict()/repr 渲染的视图，本体是对象
- 同一模式的还有：Pydantic（FastAPI 的 body.threshold）、SQLAlchemy ORM（3.8 会见）
"""
from kubernetes import client, config
from kubernetes.client.models import V1ContainerStatus

config.load_kube_config()
v1 = client.CoreV1Api()

pending = v1.read_namespaced_pod("pending-unschedulable", "k8s-check-test", _request_timeout=10)
print("1) API 返回的类型:", type(pending).__name__)
print("2) Pending Pod 的 container_statuses =", pending.status.container_statuses, "-> 教学版 or [] 兜的就是它")

ok_pod = v1.list_namespaced_pod("kube-system", _request_timeout=10).items[0]
print("3) 属性链:", ok_pod.metadata.name, "/ status 类型:", type(ok_pod.status).__name__)

d = ok_pod.to_dict()
print("4) 同一数据两种取法: 对象", ok_pod.metadata.name, "| 字典", d["metadata"]["name"])

print("5) 属性名 <-> 线上 JSON 的 camelCase 键 映射表:")
for attr, json_key in V1ContainerStatus.attribute_map.items():
    if attr in ("restart_count", "container_id", "image"):
        print(f"   {attr:<15} <-> {json_key}")

try:
    ok_pod.status["container_statuses"]
except TypeError as e:
    print("6) 拿字典姿势访问对象 ->", type(e).__name__, ":", e)
