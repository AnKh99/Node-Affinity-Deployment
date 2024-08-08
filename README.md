# Task

Create configuration for k8s to run `ipp` pod and 3 instances of `mgen` pods. `mgen` should make curl request to `ipp` on the same node.

## Installation

### Create 3 nodes
```bash
minikube start --nodes 3 -p multinode
```

### Create YAML configuration
#### MGEN YAML
```yaml
# mgen-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mgen-deployment
spec:
  replicas: 9
  selector:
    matchLabels:
      app: mgen
  template:
    metadata:
      labels:
        app: mgen
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - mgen
              topologyKey: "kubernetes.io/hostname"
      containers:
      - name: mgen
        image: your_repo/mgen-app:latest
        command: ["python", "app.py"]
        args: ["$(NODE_IP)"]
        resources:
          limits:
            cpu: "1"
            memory: "512Mi"
        env:
        - name: NODE_IP
          valueFrom:
            fieldRef:
              fieldPath: status.hostIP
```

#### IPP YAML
```yaml
# ipp-daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: ipp-daemonset
spec:
  selector:
    matchLabels:
      app: ipp
  template:
    metadata:
      labels:
        app: ipp
    spec:
      hostNetwork: true
      containers:
      - name: ipp
        image: your_repo/ipp-server:latest
        ports:
        - containerPort: 5000
```

### Create applications
#### IPP SERVER
```py
# app.py
from flask import Flask
import socket

app = Flask(__name__)

@app.route('/')
def hello():
    return f"Hello from {socket.gethostname()}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

#### IPP SERVER Dockerfile

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && apt-get clean

COPY app.py .

RUN pip install flask

CMD ["python", "app.py"]
```


#### MGEN APP

```py
import sys
import time
import requests
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if len(sys.argv) != 2:
    logger.error("Usage: app.py <NODE_IP>")
    sys.exit(1)

node_ip = sys.argv[1]

logger.info(f"Starting application with NODE_IP: {node_ip}")

while True:
    try:
        logger.info(f"Request to {node_ip}")
        response = requests.get(f'http://{node_ip}:5000')
        logger.info(f"Response: {response.text}")
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
    time.sleep(5)
```

#### MGEN APP Dockerfile

```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN apt-get update && apt-get install -y curl && apt-get clean

# Install any needed packages
RUN pip install requests

# Run app.py when the container launches
CMD ["python", "app.py"]
```

### Build apps

#### IPP SERVER
```sh
docker build -t your_repo/ipp-server:latest .
docker push your_repo/ipp-server:latest
```

#### MGEN APP
```sh
docker build -t your_repo/mgen-app:latest
docker push your_repo/mgen-app:latest
```

### Apply k8s configurations

```sh
kubectl apply -f ipp-daemonset.yaml
kubectl apply -f mgen-deployment.yaml
```

#### Get pods in cluster
```sh
kubectl get pods -o wide
```

Output:
```sh
NAME                               READY   STATUS    RESTARTS   AGE     IP             NODE             NOMINATED NODE   READINESS GATES
ipp-daemonset-5jfld                1/1     Running   0          3h45m   192.168.58.3   multinode-m02   <none>           <none>
ipp-daemonset-fcmtt                1/1     Running   0          3h45m   192.168.58.4   multinode-m03   <none>           <none>
ipp-daemonset-tr9k2                1/1     Running   0          3h45m   192.168.58.2   multinode       <none>           <none>
mgen-deployment-7d98f489f4-5lpkh   1/1     Running   0          3h12m   10.244.0.33    multinode       <none>           <none>
mgen-deployment-7d98f489f4-7xqbb   1/1     Running   0          3h12m   10.244.0.31    multinode       <none>           <none>
mgen-deployment-7d98f489f4-ccwt2   1/1     Running   0          3h12m   10.244.2.32    multinode-m03   <none>           <none>
mgen-deployment-7d98f489f4-pgsj9   1/1     Running   0          3h12m   10.244.1.33    multinode-m02   <none>           <none>
mgen-deployment-7d98f489f4-q776s   1/1     Running   0          3h12m   10.244.0.32    multinode       <none>           <none>
mgen-deployment-7d98f489f4-rz85t   1/1     Running   0          3h12m   10.244.2.31    multinode-m03   <none>           <none>
mgen-deployment-7d98f489f4-swrlv   1/1     Running   0          3h12m   10.244.2.33    multinode-m03   <none>           <none>
mgen-deployment-7d98f489f4-vw2w6   1/1     Running   0          3h12m   10.244.1.32    multinode-m02   <none>           <none>
mgen-deployment-7d98f489f4-zwb74   1/1     Running   0          3h12m   10.244.1.31    multinode-m02   <none>           <none>
```

#### Get logs from IPP pod

```sh
kubectl logs -f ipp-daemonset-5jfld
```

Output:
```sh
10.244.1.33 - - [08/Aug/2024 13:01:38] "GET / HTTP/1.1" 200 -
10.244.1.31 - - [08/Aug/2024 13:01:41] "GET / HTTP/1.1" 200 -
```

#### Get logs from MGEN pod
```sh
kubectl logs -f ipp-daemonset-5jfld
```

Output:
```sh
2024-08-08 13:02:04,413 - INFO - Request to 192.168.58.2
2024-08-08 13:02:04,415 - INFO - Response: Hello from multinode
2024-08-08 13:02:09,420 - INFO - Request to 192.168.58.2
2024-08-08 13:02:09,423 - INFO - Response: Hello from multinode
```


## Bash script to run with dynamic nodes count

```bash
#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <number_of_pods_per_node>"
  exit 1
fi

PODS_PER_NODE=$1

NODE_COUNT=$(kubectl get nodes --no-headers | wc -l)

TOTAL_PODS=$((NODE_COUNT * PODS_PER_NODE))

kubectl scale deployment mgen-deployment --replicas=$TOTAL_PODS

echo "Scaled mgen-deployment to $TOTAL_PODS replicas. $PODS_PER_NODE pods per node."
```