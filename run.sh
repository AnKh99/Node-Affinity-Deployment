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