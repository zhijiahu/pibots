Steps to run ghost blog in my K3s cluster

# Required components

## Cert manager
`arkade install cert-manager`

## Ingress nginx
`arkade install ingress-nginx`

## Metal LB
`kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.9.3/manifests/namespace.yaml
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.9.3/manifests/metallb.yaml
kubectl create secret generic -n metallb-system memberlist --from-literal=secretkey="$(openssl rand -base64 128)"`


# Create ghost namespace
`kubectl create namespace ghost`

# Secrets
kubectl apply -f config/secrets/mysql.yaml
kubectl -n ghost create secret generic ghost-s3-secret --from-literal=awsaccesskeyid=<change_here> --from-literal=awssecretaccesskey=<change_here>


# Network

## Proxy


## Ingress
kubectl apply -f network/ingress/ghost.yaml

## Services
kubectl apply -f network/services/ghost.yaml
kubectl apply -f network/services/mysql.yaml

# Storage
kubectl apply -f storage/mysql.yaml

# Deployment

### MySQL
kubectl apply -f deployments/mysql.yaml

kubectl run -it --rm --image=hypriot/rpi-mysql:5.5 --restart=Never -n ghost mysql-client -- mysql -h mysql -pabcd1234

### Ghost Blog
kubectl apply -f deployments/ghost.yaml


## HPA
`kubectl apply -f hpa/ghost.yaml`

### Generate some load to observe scaling
docker run --rm williamyeh/wrk -c 5 -d 120 -t 5 https://blog.zhijiahu.sg
