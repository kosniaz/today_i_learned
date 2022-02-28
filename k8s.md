# Kubernetes learn sheet

## Questions

* how to expose k8s cluster? 

Make sure metalLB is installed (kubespray) and define an ingress service that is configured to route traffic to the app's entrypoint service.
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
my-ingress       <none>   my-hostname       10.0.20.50   80, 443   10d
```
