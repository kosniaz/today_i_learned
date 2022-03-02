# Kubernetes learn sheet

## Questions

#### How to expose k8s cluster? 

Make sure metalLB is installed (kubespray) and define an ingress service that is configured to route traffic to the app's entrypoint service.

First we need to make sure current host has privkey,certifacte files (ask your admin for that, or make your own [here](https://certbot.eff.org/)). Then we need to make a tls secret using said files:
```
kubectl create secret tls my-tls-secret \
  --cert=path/to/cert/file \
  --key=path/to/key/file
```

Create an ingress file named `my-ingress.yml`:
```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/rewrite-target: /$1 # https://www.codegravity.com/blog/kubernetes-ingress-nginx-path-forwarding-does-not-work
spec:
  tls:
  - hosts:
      - my-hostname
    secretName: my-tls-secret
  rules:
  - host: my-hostname
    http:
      paths:
      - path: /(.*)
        pathType: Prefix
        backend:
          service:
            name: my-backend
            port:
              number: 4321                             
```

and then 
```
kubectl apply -f my-ingress.yml
```

and finally wait until the ingress gets an ip.
```
$ kubectl get ing
NAME             CLASS    HOSTS             ADDRESS      PORTS     AGE
my-ingress       <none>   my-hostname       10.0.10.4   80, 443   10d
```

10.0.10.4 is the address you can use to access the service now. You can now proceed to make NAT rules (IPtables) to forward incoming traffic from the host machine to the ingress service.

## Glossary

1. Provisioning (prepare the environment of deployment)
2. Workloads https://kubernetes.io/docs/concepts/workloads/
3. Controllers: ReplicaSet, DaemonSet, StatefulSet, Deployment
4. Resource types, Resource, Object.
Definitions [here](https://kubernetes.io/docs/reference/using-api/api-concepts/#standard-api-terminology)
Commands [here](https://www.studytonight.com/post/how-to-list-all-resources-in-a-kubernetes-namespace)
```
# see all resource types
kubectl api-resources
```
See all the resource of a resource type:
```
kubectl get <resource-type>
```

5. kubelet
6. storageClass
7. pv
8. pvc
9. manifest: the yaml I use to instantiate a deployment, pv, service, ingress etc


## To read

* The kubernetes API (server): https://cloud.redhat.com/blog/kubernetes-deep-dive-api-server-part-1
