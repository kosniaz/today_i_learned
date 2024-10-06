# Kubernetes TIL

## Provisioning AKS cluster with azure-cli

### Make the resource group (be consistent with a naming convention)
``` 
azure rg create --name rg-<appname>-eEU-<number> --location easteurope
```
### Provision the cluster (better use low cost solutions for testing devops)
```
az aks create \
  --resource-group <your-resource-group>  \
  --name <your-aks-name> \
  --node-count 2 \
  --node-vm-size Standard_B2s \
  --generate-ssh-keys
```

((by the way, tmux has internal copy and paste.)[https://www.baeldung.com/linux/tmux-copy-paste-keyboard-mouse])


### Install kubectl (if not there already)

```
az aks install-cli
```

### Get AKS cluster credentials
```
az aks get-credentials --resource-group aksResourceGroup --name myAKSCluster
```

This will store the credentials in `~/.kube/config`

### Check for storage

Check what storage classes are available. 
```
kubectl get storageclass
```

With Azure, you get a variety of storage classes. 

## blue/green method in deploying

https://codefresh.io/learn/software-deployment/what-is-blue-green-deployment/

## tracking down bugs on k8s logs

1. Use --timestamp in docker logs command
2. export to file [you can even do this with tmux's buffer](https://getridbug.com/unix-linux/write-all-tmux-scrollback-to-a-file/)
3. search for the timestamps where the (possibly recurring) bug emerged with grep: `grep <Weird_error_message> <log_file>`
4. isolate the log lines that happened in the exact second(s) of every incident using vim and adding a delimiter (eg  bug start)
5. separate the log incident using the delimiter with awk as in [here](https://stackoverflow.com/questions/1825745/split-file-based-on-string-delimiter-in-bash-how) 

## Rasa X on kuberenetes

#### Installation

It's easy to install via Helm, as explained in [the docs](https://rasa.com/docs/rasa-x/). All the configuration is inside `values.yaml`. Steps are:
```
helm repo add rasa-x https://rasahq.github.io/rasa-x-helm
helm repo update
helm install --values values.yaml rasa-x rasa-x/rasa-x \
    --namespace <your-namespace>
```

```
kosniaz@stonehedge ➜  rasax git: kubectl get svc -n my-namespace
NAME                                   TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)                                 AGE
rasa-x-app                             ClusterIP      10.132.52.190   <none>        5055/TCP,80/TCP                         2m28s
rasa-x-db-migration-service-headless   ClusterIP      None            <none>        8000/TCP                                2m28s
rasa-x-duckling                        ClusterIP      10.132.34.210   <none>        8000/TCP                                2m28s
rasa-x-nginx                           LoadBalancer   10.132.99.22    10.90.24.20   8000:31628/TCP                          2m28s
rasa-x-postgresql                      ClusterIP      10.132.42.12    <none>        5432/TCP                                2m28s
rasa-x-postgresql-headless             ClusterIP      None            <none>        5432/TCP                                2m28s
rasa-x-rabbit                          ClusterIP      10.132.42.21    <none>        5672/TCP,4369/TCP,25672/TCP,15672/TCP   2m28s
rasa-x-rabbit-headless                 ClusterIP      None            <none>        4369/TCP,5672/TCP,25672/TCP,15672/TCP   2m28s
rasa-x-rasa-worker                     ClusterIP      10.132.91.210   <none>        5005/TCP                                2m28s
rasa-x-rasa-x                          ClusterIP      10.132.21.231   <none>        5002/TCP                                2m28s
rasa-x-redis-headless                  ClusterIP      None            <none>        6379/TCP                                2m28s
rasa-x-redis-master                    ClusterIP      10.132.42.230   <none>        6379/TCP                                2m28s
```
#### How to expose

    1. port forwarding with k8s: 
    ```
    kubectl port-forward -n <your-namespace> service/rasa-x-nginx --address 0.0.0.0 <your-port>:8080
    ```
    or 
    2. use a local nginx installation, by adding the following in the nginx.conf (and then `sudo systemctl reload nginx`)
    
    ```
    http {
    
    server {
        listen <your-port> ssl;
        server_name <your-hostname>;

        ssl_certificate /etc/letsencrypt/<path-to-your-keyfile>;
        ssl_certificate_key /etc/letsencrypt/<path-to-your-certfile>;

        location / {
            proxy_pass http://<external-ip-of-svc>:8000;
        }
     }
     }
    ```
    
    
#### How to use the rabbit mq inside:

Just change `values.yml` to include the following in the rabbitmq section:
```
    # service specifies settings for exposing rabbit to other services
    service:
        # port on which rabbitmq is exposed to Rasa
        port: 5672
```

and expose with port forwarding, as shown in the previous section. It can't be accessed directly, because it is not a `LoadBalancer` type service.

#### Upgrade with Helm (and a common error encountered)

```
helm upgrade rasa-x rasa-x/rasa-x -n <your-namespace> --values values.yaml
```

Possible error with the default values:

```
kubaras@chomsky ➜ helm-deployment helm upgrade rasa-x rasa-x/rasa-x -n <your-namespace> --values values.yaml                                           [6/1974]
Error: UPGRADE FAILED: execution error at (rasa-x/charts/rabbitmq/templates/NOTES.txt:170:4):                                                                          
PASSWORDS ERROR: You must provide your current passwords when upgrading the release.                                                                                   
                 Note that even after reinstallation, old credentials may be needed as they may be kept in persistent volume claims.                                   
                 Further information can be obtained at https://docs.bitnami.com/general/how-to/troubleshoot-helm-chart-issues/#credential-errors-while-upgrading-chart
-releases                                                                                                                                                              
                                                                                                                                                                       
    'auth.erlangCookie' must not be empty, please add '--set auth.erlangCookie=$RABBITMQ_ERLANG_COOKIE' to the command. To get the current value:

        export RABBITMQ_ERLANG_COOKIE=$(kubectl get secret --namespace "nbg-contributors" rasa-x-rabbit -o jsonpath="{.data.rabbitmq-erlang-cookie}" | base64 --decode$

```

Solution: Make sure this is inside the `values.yaml`
```
rabbitmq:
  enabled: true
  install: true
  auth:
    password: <specify>
    erlangCookie: <specify>
```

[source](https://forum.rasa.com/t/cannot-upgrade-deployment-in-kubernates/50748/3)



## How to expose k8s cluster? 

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

## How I set up a static file server for deployment in our cluster 

### Static fs deployment


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


### Your app's context

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

### Create the PVC that will be used by our app's deployment to claim storage in the PV

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

### Create the service and test locally with port-forwarding

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


### Glossary

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
