import os

# Dev Overlay
DEV_DIR = "/Users/swibit/Documents/Swibit/Intern/shiftmaster-py/infrastructure/k8s/overlays/dev"
os.makedirs(DEV_DIR, exist_ok=True)

dev_kustomization = """\
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- ../../base

namePrefix: dev-

# In dev, we might override resource limits or replicas, but base is fine for now
"""
with open(os.path.join(DEV_DIR, "kustomization.yaml"), "w") as f:
    f.write(dev_kustomization)

# Prod Overlay
PROD_DIR = "/Users/swibit/Documents/Swibit/Intern/shiftmaster-py/infrastructure/k8s/overlays/prod"
os.makedirs(PROD_DIR, exist_ok=True)

prod_kustomization = """\
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- ../../base

namePrefix: prod-

# Example patch to increase replicas for production
patches:
- target:
    kind: Deployment
    name: gateway
  patch: |-
    - op: replace
      path: /spec/replicas
      value: 3
- target:
    kind: Deployment
    name: auth
  patch: |-
    - op: replace
      path: /spec/replicas
      value: 2
- target:
    kind: Deployment
    name: monolith
  patch: |-
    - op: replace
      path: /spec/replicas
      value: 2
"""
with open(os.path.join(PROD_DIR, "kustomization.yaml"), "w") as f:
    f.write(prod_kustomization)

print("Overlays generated")
