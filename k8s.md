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

# How I set up a static file server for deployment in our cluster 

# Static fs deployment


This is an attempt to deploy a service on our cluster, from zero to deployment with storage to an nfs PV.

1. Build the image and push it to an accessible docker repo
2. Set another namespace (use contexts! https://kubernetes.io/docs/tasks/administer-cluster/namespaces-walkthrough/
3. create the pv:
   1. mkdir a folder inside the /storage/srv/nfs dir
   2. add it to /etc/exports, in order to add it to the nfs server dirs
   3. run `exportfs -r` to reload the exports file
   4. specify the folder you made in the pv manifest, as shown in our example

3. Write the deployment and pvc files

 failed in using fanout technique to expose service through theano ingress. Actually our ingress never got an IP, so I couldn't test. My method was:

 1. https://kubernetes.io/docs/concepts/services-networking/ingress/#simple-fanout
 2. https://stackoverflow.com/questions/51878195/kubernetes-cross-namespace-ingress-network/51899301#51899301
 3. https://stackoverflow.com/questions/59844622/ingress-configuration-for-k8s-in-different-namespaces


## Your app's context

1. Check the namespaces available:
```
get ns
```

2. Create your own namespace:
```
kubectl create namespace kosmas-ns
```

3. To create a context associated to this namespace, first we check the existing contexts, users, clusters

```
kubectl config view
```
Then, proceed to make your own context 
```
kubectl config set-context kosmas-context --namespace=kosmas-ns \
  --cluster=cluster.local \
  --user=kubernetes-admin-cluster.local
```

4. Switch to the context 
```
kubectl config use-context kosmas-context
```
5. Verify current context
```
kubectl config current-context
```

## Prepare a persistent volume of the NFS type, hosted on chomsky

1. Create a folder to be used by the application. 
```
mkdir /storage/srv/nfs/kosmas-static-fs-data
```
2. Configure the nfs server to serve this folder too, by editing the /etc/exports file. 
```
echo "/storage/srv/nfs/kosmas-static-fs-storage *(rw,sync,no_subtree_check)" >> /etc/exports
```
3. Refresh the nfs server, to read the new directories
```
exportfs -rv
```
4. write the pv file following the example of the theano-pv
```
apiVersion: v1
kind: PersistentVolume
metadata:
  name: theano-nfs-pv
spec:
  capacity:
    storage: 50Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  storageClassName: nfs
  mountOptions:
    - hard
  nfs:
    path: /storage/srv/nfs/theano_data_sources
    server: ${NFS_SERVER_HOST}
```
5. Apply the manifest to create the pv
```
kubectl apply -f kosmas-pv.yaml
```
6. Check the new pv
```
kubectl get pv
```

## Create the PVC that will be used by our app's deployment to claim storage in the PV

1. Simply edit this template, used by the rasa-actions service:
```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: rasa-actions-pvc
spec:
  storageClassName: nfs
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 5Gi
  volumeName: theano-nfs-pv

```
To ensure the right PV will be bound, we explicitly refernce the pv in the field `volumeName`

2. Apply the template as before
```
kubectl apply -f static-fs-pvc.yaml
```
3. It should be bound immediately
```
kubectl get pvc
```

### Create the deployment file and run it!

At this step, you need the name of the image to download, the port of your service, the mountpoint of the persistent volume as well as the 
environment variables needed.
In this file we also declare the pvc that will be used, the number of replicas in the beginning, the imagePullPolicy, some labels for this deployment.
And some more stuff

Sample file here
```
apiVersion: apps/v1
kind: Deployment 
metadata:
  annotations:
  labels:
    app: kosmas-static-fs  # a label for the deployment
  name: kosmas-static-fs  
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kosmas-static-fs
  strategy:
    type: Recreate
  template:    
    metadata:
      annotations:
      labels:
        app: kosmas-static-fs
    spec:
      volumes:              # a list of volumes made available to containers
      - name: static-fs-pv
        persistentVolumeClaim:
         claimName: static-fs-pvc
      containers:           # a list of the pod's containers
      - name: kosmas-static-fs
        image: kubaras/kosmas-static-fileserver
        env:                # a list of to-create environment variables
        - name: FOOVAR
          value: "foo"  
        imagePullPolicy: Always  # defines when to pull/check for a new image
        ports:                      # ports to be exposed by the container
          - containerPort: <port>
        volumeMounts:
          - mountPath: "/static-fs/data_folder" # where persisting data will be kept
            name: static-fs-pv # persistent volume
      restartPolicy: Always # behavior when the pod fails/exits
```
To launch the deployment, simply run
```
kubectl apply -f static-fs-deployment.yaml
```
and check it
```
kubectl get deployments.apps static-fs
```
check the pods too
```
kubectl get po
```
Finally, see the debug messages of the pods launching
```
kubectl describe pods
```

## Create the service and test locally with port-forwarding

Create a simple loadBalancer service that will expose your deployment.
Otherwise it cannot be accessed, except through the pods themselves (but we don't want to expose the pods themselves,
becuase they are not persistent)

create a service manifest and apply it

```
apiVersion: v1
kind: Service
metadata:
  annotations:
  labels:
    app: rasa-actions
  name: rasa-actions
spec:
  ports:
  - name: "5055"
    port: 5055
    targetPort: 5055
  selector:
    app: rasa-actions
status:
  loadBalancer: {}
```
Apply it
```
kubectl apply -f static-fs-service.yaml
```
use port forward to test it.
```
kubectl port-forward static-fs-service 1357:<PORT>
```
And test it!
```
curl localhost:1357/data_folder/index.html
```

## Make service accessible to the default ingress

Give the service an external name, that can be used by the ingress from the default namespace
```
apiVersion: v1
kind: Service
metadata:
  annotations:
  labels:
    app: kosmas-static-fileserver 
  name: kosmas-static-fileserver
  namespace: kosmas-ns
spec:
  type: ExternalName
  externalName: kosmas-static-fileserver.kosmas-static-fs.svc.cluster.local
  ports:
  - name: <port>
    port: <port>
    targetPort: <port>
  selector:
    app: kosmas-static-fileserver
status:
  loadBalancer: {}
```


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
