import os
import textwrap

BASE_DIR = "/Users/swibit/Documents/Swibit/Intern/shiftmaster-py/infrastructure/k8s/base"

os.makedirs(BASE_DIR, exist_ok=True)

manifests = {
    "namespace.yaml": """\
apiVersion: v1
kind: Namespace
metadata:
  name: shiftmaster
""",
    "postgres-statefulset.yaml": """\
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: shiftmaster
spec:
  serviceName: "postgres"
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: "shift_master_py_db"
        - name: POSTGRES_USER
          value: "shift_py"
        - name: POSTGRES_PASSWORD
          value: "supersecretpassword"
        ports:
        - containerPort: 5432
          name: postgres
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 5Gi
""",
    "postgres-service.yaml": """\
apiVersion: v1
kind: Service
metadata:
  name: db
  namespace: shiftmaster
spec:
  ports:
  - port: 5432
    targetPort: 5432
  selector:
    app: postgres
""",
    "redis-deployment.yaml": """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: shiftmaster
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command: ["redis-server", "--maxmemory", "128mb", "--maxmemory-policy", "allkeys-lru"]
        ports:
        - containerPort: 6379
""",
    "redis-service.yaml": """\
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: shiftmaster
spec:
  ports:
  - port: 6379
    targetPort: 6379
  selector:
    app: redis
""",
    "rabbitmq-statefulset.yaml": """\
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: rabbitmq
  namespace: shiftmaster
spec:
  serviceName: "rabbitmq"
  replicas: 1
  selector:
    matchLabels:
      app: rabbitmq
  template:
    metadata:
      labels:
        app: rabbitmq
    spec:
      containers:
      - name: rabbitmq
        image: rabbitmq:3-management-alpine
        env:
        - name: RABBITMQ_DEFAULT_USER
          value: "guest"
        - name: RABBITMQ_DEFAULT_PASS
          value: "guest"
        ports:
        - containerPort: 5672
          name: amqp
        - containerPort: 15672
          name: management
""",
    "rabbitmq-service.yaml": """\
apiVersion: v1
kind: Service
metadata:
  name: rabbitmq
  namespace: shiftmaster
spec:
  ports:
  - port: 5672
    name: amqp
    targetPort: 5672
  - port: 15672
    name: management
    targetPort: 15672
  selector:
    app: rabbitmq
"""
}

# Add microservices
services = ["gateway", "auth", "schedule", "notifications", "monolith"]
for svc in services:
    manifests[f"{svc}-deployment.yaml"] = f"""\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {svc}
  namespace: shiftmaster
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {svc}
  template:
    metadata:
      labels:
        app: {svc}
    spec:
      containers:
      - name: {svc}
        image: ghcr.io/haiderbassem/shiftmaster-py-{svc}:latest
        imagePullPolicy: Always
        env:
        - name: DB_HOST
          value: "prod-db"
        - name: REDIS_URL
          value: "redis://prod-redis:6379/0"
        - name: RABBITMQ_URL
          value: "amqp://guest:guest@prod-rabbitmq:5672/"
        - name: DB_PASSWORD
          value: "supersecretpassword"
        - name: DB_USER
          value: "shift_py"
        - name: DB_NAME
          value: "shift_master_py_db"
        - name: JWT_SECRET
          value: "supersecretjwtkeythatislongenough32chars"
        - name: AUTH_SERVICE_URL
          value: "http://prod-auth:8000"
        - name: SCHEDULE_SERVICE_URL
          value: "http://prod-schedule:8000"
        - name: NOTIFICATION_SERVICE_URL
          value: "http://prod-notifications:8000"
        - name: MONOLITH_URL
          value: "http://prod-monolith:8000"
        ports:
        - containerPort: 8000
"""
    manifests[f"{svc}-service.yaml"] = f"""\
apiVersion: v1
kind: Service
metadata:
  name: {svc}
  namespace: shiftmaster
spec:
  {"type: LoadBalancer\n  " if svc == "gateway" else ""}ports:
  - port: 8000
    targetPort: 8000
  selector:
    app: {svc}
"""

kustomization = """\
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: shiftmaster

resources:
"""
for filename in manifests.keys():
    kustomization += f"- {filename}\n"

manifests["kustomization.yaml"] = kustomization

for filename, content in manifests.items():
    with open(os.path.join(BASE_DIR, filename), "w") as f:
        f.write(content)

print(f"Generated {len(manifests)} manifests in {BASE_DIR}")
