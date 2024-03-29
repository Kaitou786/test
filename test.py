#!/usr/bin/python
import commands as sp
import time
import sys
start_time_tests=time.time()

f=open("test.config","r")
var=f.read()
var=var.split("\n")
masterIP=var[0].split("=")[1]
nfsIP=var[1].split("=")[1]
nfsPATH=var[2].split("=")[1]
netmask=int(var[3].split("=")[1])
if "--debug" in sys.argv:
	debug=True
else:
	debug=False

print("=========verifying if all pods in kube-system are running or not=======")

pods=sp.getoutput("kubectl get pods -n kube-system")
pods=pods.split("\n")
flag=0
for i in range(1,len(pods)-1):
	if pods[i].split()[2] != 'Running':
		flag+=1
if flag == 0:
	if debug:
		print("all pods in kube-system are running")


print("=====================Initializing tests======================")
def single_pod_test():
	print("====================single container pods creation and deletion===========")
	start_time_test_case=time.time()

	docker_image="nginx"

	fh=open("pod_test.yaml","w")
	fh.write("""apiVersion: v1
kind: Pod
metadata:
     name: test-pod
     labels:
         app-lang: python
         type: back-end
spec:
     containers:
       - name: test-cont
         image: {}""".format(docker_image))
	fh.close()

	tup=sp.getstatusoutput("kubectl create -f pod_test.yaml")
	if tup[0]==0:
		if debug:
			print("====================Single container POD created===============")

	status=sp.getoutput("kubectl get pod test-pod")
	status=status.split()[-3]


	if debug:
		print("waiting for pod to be running......")
	while status != "Running":
	       status=sp.getoutput("kubectl get pods")
	       status=status.split()[-3]
	if debug:
		print("============================POD is running succesfully================")

	tup=sp.getstatusoutput("kubectl delete -f pod_test.yaml")
	if tup[0]==0:
		if debug:
			print("========================POD Deleted===================")
	print("=========================Test case complete=============")

	test_case_time= time.time()  - start_time_test_case
	tests_time=time.time() - start_time_tests

	print("Time Taken by test="+str(test_case_time))
	print("Total Time elapsed="+str(tests_time))


	print("==========================================================================================")



def multi_pod_test():
	start_time_test_case=time.time()
	print("=================Multi-Cont Pod test=================")
	fh=open("multi-cont_test.yaml","w")
	fh.write("""apiVersion: v1
kind: Pod
metadata:
  name: two-containers
spec:

  restartPolicy: Never

  volumes:
   - name: shared-data
     emptyDir: {}

  containers:
   - name: nginx-container
     image: nginx
     volumeMounts:
     - name: shared-data
       mountPath: /usr/share/nginx/html
     ports:
      - containerPort: 80
   - name: debian-container
     image: debian
     volumeMounts:
      - name: shared-data
        mountPath: /pod-data
     command: ["/bin/sh"]
     args: ["-c", "echo Hello from the debian container > /pod-data/index.html"]""")

	fh.close()

	tup=sp.getstatusoutput("kubectl create -f multi-cont_test.yaml")
	if tup[0]==0:
		if debug:
			print("====================POD is created=================")
	status = sp.getoutput("kubectl get pod  two-containers")
	status=status.split()[-3]


	if debug:
		print("waiting for pod to be running......")
	while status != "Running":
	       status=sp.getoutput("kubectl get pods")
	       status=status.split()[-3]
	if debug:
		print("===============POD is now running====================")

	data=sp.getoutput("kubectl exec -it two-containers   -c nginx-container   cat '/usr/share/nginx/html/index.html'")
	if data == "Hello from the debian container":
	    if debug:
	    	print("==============container inside pod can access shared resources==============")
	sp.getoutput("kubectl delete -f multi-cont_test.yaml")
	print("===============Test case complete=====================")

	test_case_time= time.time()  - start_time_test_case
	tests_time=time.time() - start_time_tests

	print("Time Taken by test="+str(test_case_time))
	print("Total Time elapsed="+str(tests_time))


def namespace():
	print("==============================================================")
	print("checking if multiple namespaces can be created or not")
	start_time_test_case=time.time()

	status=[]
	j=0
	status.append(sp.getstatusoutput("kubectl create namespace test1"))
	status.append(sp.getstatusoutput("kubectl create namespace test2"))
	status.append(sp.getstatusoutput("kubectl create namespace test3"))
	for i in range(len(status)):
	   if status[i][0] != 0:
	      j+=1
	      print(i)
	if j==0:
	    if debug:
	    	print("multiple namespaces can be created")
	else:
	   if debug:
	   	print("Please check if there are namespaces already present starting with test")

	sp.getoutput("kubectl delete ns test1")
	sp.getoutput("kubectl delete ns test2")
	sp.getoutput("kubectl delete ns test3")
	if debug:
		print("==============Namespaces are deleted===============")
	print("==============Test case complete===================")


	test_case_time= time.time()  - start_time_test_case
	tests_time=time.time() - start_time_tests

	print("Time Taken by test="+str(test_case_time))
	print("Total Time elapsed="+str(tests_time))

def rs_test():
	print("==========================================================")
	print("====================Deploying pods by creating Replica Set=================")
	start_time_test_case=time.time()


	fh=open("rs_test.yaml","w")
	fh.write("""apiVersion: apps/v1
kind: ReplicaSet
metadata:
   name: test-pod
   labels:
     app: rs-test
spec:
    template:
       metadata:
          name: test-pod
          labels:
             app: rs-test
       spec:
          containers:
            - name: test-cont
              image: nginx
              ports:
               - containerPort: 80
    replicas: 3
    selector:
      matchLabels:
        app: rs-test""")
	fh.close()

	tup=sp.getstatusoutput("kubectl create -f rs_test.yaml")
	if tup[0]==0:
		if debug:
			print("=================Replica set is created==================")
	else:
		print("error in creating replica set")
	pods=sp.getoutput("kubectl get pods")
	pods=pods.strip().split("\n")
	pods_status=[]
	for i in range(len(pods)-1):
		pods_status.append(pods[i+1].split()[2])
	if debug:
		print("waiting for all the pods to be in running state")
	while pods_status[0]!="Running" or pods_status[1]!="Running" or pods_status[2]!="Running":
	  pods=sp.getoutput("kubectl get pods")
	  pods=pods.strip().split("\n")
	  pods_status=[]
	  for i in range(len(pods)-1):
	    pods_status.append(pods[i+1].split()[2])
	if debug:
		print("All pods are running")

	pods=sp.getoutput("kubectl get pods")
	pod_to_be_deleted=pods.split("\n")[1].split()[0]
	if debug:
		print("deleting a pod to test self-healing")
	sp.getoutput("kubectl delete pod {}".format(pod_to_be_deleted))
	if debug:
		print("Pod deleted")
		print("waiting for all pods to be running")

	pods=pods.strip().split("\n")
	pods_status=['noset']
	while pods_status[0]!="Running":
	  pods=sp.getoutput("kubectl get pods")
	  pods=pods.strip().split("\n")
	  pods_status=[]
	  for i in range(len(pods)-1):
	    pods_status.append(pods[i+1].split()[2])
	  pods=sp.getoutput("kubectl get pods")
	if debug:
		print("================All the pods are running again==============")
		print("=================Scaling up the pod=========================")



	tup=sp.getstatusoutput("kubectl scale --replicas=5  rs/test-pod")
	if tup[0]==0:
		status=sp.getoutput("kubectl get pods")
		status=status.split("\n")
		while status[1].split()[2] != 'Running' or status[2].split()[2] != 'Running' or status[3].split()[2] != 'Running' or    status[4].split()[2] != 'Running'  or status[5].split()[2] != 'Running':

		      status=sp.getoutput("kubectl get pods")
		      status=status.split("\n")
		if debug:
			print("scaled up and running")

			print("================Scaling down the pod========================")


	tup=sp.getstatusoutput("kubectl scale --replicas=1  rs/test-pod")
	if tup[0]==0:
		status=sp.getoutput("kubectl get pods")
		status=status.split("\n")
		while len(status) != 2:
			status = sp.getoutput("kubectl get pods")
			status=status.split("\n")
		if debug:
			print("scaled down and running")
			print("=======exposing the replica set============")
	tup=sp.getstatusoutput("kubectl expose rs/test-pod  --type=NodePort")
	if tup[0]==0:
		if debug:
			print("pod has been exposed")
		port=sp.getoutput("kubectl get svc test-pod")
		port=port.split("\n")[1].split(":")[1].split("/")[0]
		tup=sp.getstatusoutput("curl {}:{}".format(masterIP,port))
		if tup[0]==0:
			if debug:
				print("application is accessible from outside the cluster")
		else:
			print("ERROR in accessing the application")
	sp.getoutput("kubectl delete svc test-pod")		
	sp.getoutput("kubectl delete -f rs_test.yaml")

	if debug:
		print("==================Replica set is deleted================")
	running_pods=""
	if debug:
		print("waiting for the pods to be terminated")
	while len(running_pods)!=19:
	     running_pods=sp.getoutput("kubectl get pods")
	if debug:
		print("=========All pods are terminated automatically============")
	test_case_time= time.time()  - start_time_test_case
	tests_time=time.time() - start_time_tests

	print("Time Taken by test="+str(test_case_time))
	print("Total Time elapsed="+str(tests_time))


def decToBin(num):
	num=bin(num)
	num=num[2:len(num)]
	length=len(num)
	rest=""
	while length < 8:
		rest=rest+"0"
		length+=1
	rq_num=rest+num
	return rq_num

def network_layer():
	print("========================================================")
	print("======Verifying if pods run on same network layer=======")
	start_time_test_case=time.time()
	fh=open("rs_test.yaml","w")
	fh.write("""apiVersion: apps/v1
kind: ReplicaSet
metadata:
   name: test-pod
   labels:
     app: rs-test
spec:
    template:
       metadata:
          name: test-pod
          labels:
             app: rs-test
       spec:
          containers:
            - name: test-cont
              image: nginx
              ports:
               - containerPort: 80
    replicas: 4
    selector:
      matchLabels:
        app: rs-test""")
	fh.close()

	tup=sp.getstatusoutput("kubectl create -f rs_test.yaml")
	if tup[0]==0:
		if debug:
			print("Pods on all nodes are created")
			print("Waiting for all pods to be in running status")
		pods=sp.getoutput("kubectl get pods")
		pods=pods.split("\n")
		pods_status=[]
		for i in range(len(pods)-1):
			pods_status.append(pods[i+1].split()[2])
		while pods_status[0]!="Running" or pods_status[1]!="Running" or pods_status[2]!="Running" or pods_status[3]!="Running":
		  pods=sp.getoutput("kubectl get pods")
		  pods=pods.strip().split("\n")
		  pods_status=[]
		  for i in range(len(pods)-1):
		    pods_status.append(pods[i+1].split()[2]) 
		if debug:
			print("all pods are running now")
	if debug:
		print("getting ips of all the pods")

	pods=sp.getoutput("kubectl get pods -o wide")
	pods=pods.split("\n")
	pod_ip1=pods[1].split()[5]
	pod_ip2=pods[2].split()[5]
	pod_ip3=pods[3].split()[5]
	pod_ip4=pods[4].split()[5]

	pod_ip1=pod_ip1.split(".")
	pod_ip2=pod_ip2.split(".")
	pod_ip3=pod_ip3.split(".")
	pod_ip4=pod_ip4.split(".")

	pod_ip1_oc1=pod_ip1[0]
	pod_ip1_oc2=pod_ip1[1]
	pod_ip1_oc3=pod_ip1[2]
	pod_ip1_oc4=pod_ip1[3]


	pod_ip2_oc1=pod_ip2[0]
	pod_ip2_oc2=pod_ip2[1]
	pod_ip2_oc3=pod_ip2[2]
	pod_ip2_oc4=pod_ip2[3]


	pod_ip3_oc1=pod_ip3[0]
	pod_ip3_oc2=pod_ip3[1]
	pod_ip3_oc3=pod_ip3[2]
	pod_ip3_oc4=pod_ip3[3]


	pod_ip4_oc1=pod_ip4[0]
	pod_ip4_oc2=pod_ip4[1]
	pod_ip4_oc3=pod_ip4[2]
	pod_ip4_oc4=pod_ip4[3]

	if debug:
		print("converting all ips in 32 bit addresses")
	pod_ip1_bin=str(decToBin(int(pod_ip1_oc1)))+str(decToBin(int(pod_ip1_oc2)))+str(decToBin(int(pod_ip1_oc3)))+str(decToBin(int(pod_ip1_oc4))) 
	pod_ip2_bin=str(decToBin(int(pod_ip2_oc1)))+str(decToBin(int(pod_ip2_oc2)))+str(decToBin(int(pod_ip2_oc3)))+str(decToBin(int(pod_ip2_oc4)))
	pod_ip3_bin=str(decToBin(int(pod_ip3_oc1)))+str(decToBin(int(pod_ip3_oc2)))+str(decToBin(int(pod_ip3_oc3)))+str(decToBin(int(pod_ip3_oc4)))
	pod_ip4_bin=str(decToBin(int(pod_ip4_oc1)))+str(decToBin(int(pod_ip4_oc2)))+str(decToBin(int(pod_ip4_oc3)))+str(decToBin(int(pod_ip4_oc4)))


	if pod_ip1_bin[0:netmask] == pod_ip2_bin[0:netmask] == pod_ip3_bin[0:netmask] == pod_ip4_bin[0:netmask]:
		print("===========All pods on different nodes are on same network layer==========")
	if debug:
		print("deleting pods")
	sp.getoutput("kubectl delete rs/test-pod")
	running_pods=""
	if debug:
		print("waiting for the pods to be terminated")
	while len(running_pods)!=19:
	     running_pods=sp.getoutput("kubectl get pods")
	if debug:
		print("=========All pods are terminated============")
	print("============Test case complete===================")
	test_case_time= time.time()  - start_time_test_case
	tests_time=time.time() - start_time_tests

	print("Time Taken by test="+str(test_case_time))
	print("Total Time elapsed="+str(tests_time))	

def metric_server():
	print("========================================================")
	print("=========Checking if metric server is running===========")
	start_time_test_case=time.time()
	metric=sp.getoutput("kubectl top nodes")
	metric_status=metric.split(" ")[0]

	metric_pod=sp.getoutput("kubectl get pods -n kube-system | grep metric")
	metric_pod_status=metric_pod.split()[2]
	if metric_pod_status == 'Running':
		if metric_status == 'NAME':
		        print("===========Metrics server is working=========")
	else:
		print("============Error in metrics server deployment======")

	test_case_time= time.time()  - start_time_test_case
	tests_time=time.time() - start_time_tests

	print("Time Taken by test="+str(test_case_time))
	print("Total Time elapsed="+str(tests_time))


def sc_pvc():
	print("================================================================")
	print("=========Creation and deletion of storage class=================")
	print("=========PVC to claim from storage class(dynamic provisioning)==")
	print("======pod to utilize that pvc and write something in it=========")
	start_time_test_case=time.time()
	fh=open("service.yaml","w")
	fh.write("""kind: ServiceAccount
apiVersion: v1
metadata:
  name: nfs-client-provisioner
---
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: nfs-client-provisioner-runner
rules:
  - apiGroups: [""]
    resources: ["persistentvolumes"]
    verbs: ["get", "list", "watch", "create", "delete"]
  - apiGroups: [""]
    resources: ["persistentvolumeclaims"]
    verbs: ["get", "list", "watch", "update"]
  - apiGroups: ["storage.k8s.io"]
    resources: ["storageclasses"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["events"]
    verbs: ["create", "update", "patch"]
---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: run-nfs-client-provisioner
subjects:
  - kind: ServiceAccount
    name: nfs-client-provisioner
    namespace: default
roleRef:
  kind: ClusterRole
  name: nfs-client-provisioner-runner
  apiGroup: rbac.authorization.k8s.io
---
kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: leader-locking-nfs-client-provisioner
rules:
  - apiGroups: [""]
    resources: ["endpoints"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
---
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: leader-locking-nfs-client-provisioner
subjects:
  - kind: ServiceAccount
    name: nfs-client-provisioner
    # replace with namespace where provisioner is deployed
    namespace: default
roleRef:
  kind: Role
  name: leader-locking-nfs-client-provisioner
  apiGroup: rbac.authorization.k8s.io""")
	fh.close()

	fh1=open("deployment.yaml","w")
	fh1.write("""kind: Deployment
apiVersion: extensions/v1beta1
metadata:
  name: nfs-client-provisioner
spec:
  replicas: 1
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        app: nfs-client-provisioner
    spec:
      serviceAccountName: nfs-client-provisioner
      containers:
        - name: nfs-client-provisioner
          image: quay.io/external_storage/nfs-client-provisioner:latest
          volumeMounts:
            - name: nfs-client-root
              mountPath: /persistentvolumes
          env:
            - name: PROVISIONER_NAME
              value: example.com/nfs
            - name: NFS_SERVER
              value: {0}
            - name: NFS_PATH
              value: {1}
      volumes:
        - name: nfs-client-root
          nfs:
            server: {0}
            path: {1}""".format(nfsIP,nfsPATH))
	fh1.close()
	fh2=open("class.yaml","w")
	fh2.write("""apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: managed-nfs-storage
provisioner: example.com/nfs
reclaimPolicy: Delete
parameters:
  archiveOnDelete: 'false'""")
	fh2.close()
	fh3=open("claim.yaml","w")
	fh3.write("""kind: PersistentVolumeClaim
apiVersion: v1
metadata:
   name: nfs
   annotations:
      volume.beta.kubernetes.io/storage-class: "managed-nfs-storage"
spec:
   accessModes:
     - ReadWriteMany
   resources:
     requests:
        storage: 1Gi""")
	fh3.close()

	fh4=open("pod_pvc.yaml","w")
	fh4.write("""apiVersion: v1
kind: Pod
metadata:
  name: pod-pvc
spec:

  restartPolicy: Never

  volumes:
   - name: mypvc
     persistentVolumeClaim:
        claimName: nfs

  containers:
   - name: nginx-container
     image: nginx
     volumeMounts:
     - name: mypvc
       mountPath: /etc/nginx/html
     ports:
      - containerPort: 80
   - name: debian-container
     image: debian
     volumeMounts:
      - name: mypvc
        mountPath: /pod-data
     command: ["/bin/sh"]
     args: ['-c', 'echo Hello from the debian container > /pod-data/index.html']""")
	fh4.close()
	tup=sp.getstatusoutput("kubectl create -f service.yaml")
	if tup[0]==0:
		if debug:
			print("Service account with required RBAC for nfs provisioner has been created")
			print(tup[1])
		tup=sp.getstatusoutput("kubectl create -f deployment.yaml")
		if tup[0]==0:
			if debug:
				print("deployment for provisioning the nfs is created")
				print("waiting for it to be in running state")
			pod=sp.getoutput("kubectl get pod")
			pod_status=pod.split("\n")[1].split()[2]
			while pod_status != 'Running':
				pod=sp.getoutput("kubectl get pod")
				pod_status=pod.split("\n")[1].split()[2]
			if debug:
				print("nfs-provisioner is in running state now")
				print("creating storage class")
			tup=sp.getstatusoutput("kubectl create -f class.yaml")
			if tup[0]==0:
				if debug:
					print("storage class sucessfully created")
					print("creating a persistent volume claim on the storage class")
				tup=sp.getstatusoutput("kubectl create -f claim.yaml")
				if tup[0]==0:
					if debug:
						print("claim has been created waiting for it to be bounded")
				pvc=sp.getoutput("kubectl get pvc nfs")
				pvc_status=pvc.split("\n")[1].split()[1]
				while pvc_status != 'Bound':
					pvc=sp.getoutput("kubectl get pvc nfs")
					pvc_status=pvc.split("\n")[1].split()[1]
				if debug:
					print("pvc sucessfully bounded")
			tup=sp.getstatusoutput("kubectl create -f pod_pvc.yaml")
			if tup[0]==0:
				if debug:
					print("pod with pvc is created")
					print("waiting for it to be in running state")
				pod=sp.getoutput("kubectl get pods pod-pvc")
				pod_status=pod.split("\n")[1].split()[2]
				while pod_status != 'Running':
					pod=sp.getoutput("kubectl get pods pod-pvc")
					pod_status=pod.split("\n")[1].split()[2]
				if debug:
					print("pod is created and attached to pvc")
					print("Checking if data is present in nfs server")
					print("creating directory locally and mounting to nfs to check file")
				tup=sp.getstatusoutput("mkdir /k8s-nfs")
				if tup[0]==0:
					tup=sp.getstatusoutput("mount {}:{}   /k8s-nfs".format(nfsIP,nfsPATH))
					if tup[0]==0:
						if debug:
							print("Successfully mounted on local directory")
						pv=sp.getoutput("kubectl get pv")
						pv_name=pv.split("\n")[1].split()[0]
						tup=sp.getstatusoutput("cat /k8s-nfs/default-nfs-{}/index.html".format(pv_name))
						if tup[0]==0:
							if debug:
								print("File is successfully created in nfs")
								print("unmounting local directory")
							sp.getoutput("umount /k8s-nfs")
							sp.getoutput("rmdir /k8s-nfs")
							if debug:
								print("directory deleted")
						else:
							if debug:
								print("Error...file not present in nfs")
					else:
						if debug:
							print("error in mounting")
				else:
					if debug:
						print("Error in creating the directory")

			sp.getoutput("kubectl delete -f pod_pvc.yaml")
			if debug:
				print("Pod has been deleted")
	tup=sp.getstatusoutput("kubectl delete pvc nfs")
	if tup[0]==0:
		if debug:
			print("pvc has been deleted")
	tup=sp.getstatusoutput("kubectl delete -f class.yaml")
	if tup[0]==0:	
		if debug:
			print("storage class has been deleted")

	tup=sp.getstatusoutput("kubectl delete -f deployment.yaml")
	if tup[0]==0:
		if debug:
			print("Deployment for nfs-provisioner is deleted")

	tup=sp.getstatusoutput("kubectl delete -f service.yaml")
	if tup[0]==0:
		if debug:
			print("Service account and other rbacs are deleted")
	print("================TEST case Completed==========")

	test_case_time= time.time()  - start_time_test_case
	tests_time=time.time() - start_time_tests

	print("Time Taken by test="+str(test_case_time))
	print("Total Time elapsed="+str(tests_time))


def deployment():
	start_time_test_case=time.time()
	print("====================================================")
	print("============Deployment test=========================")
	fh=open('test-deploy.yaml','w')
	fh.write("""apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.7.9
        ports:
        - containerPort: 80
""")
	fh.close()
	tup=sp.getstatusoutput("kubectl create -f test-deploy.yaml")
	if tup[0]==0:
		if debug:
			print("=================Depoyment created===============")
		status=sp.getoutput("kubectl get deploy/nginx-deployment")
		status=status.split("\n")	
		status=status[1].split()[1]
		while status != '3/3':
			status=sp.getoutput("kubectl get deploy/nginx-deployment")
			status=status.split("\n")	
			status=status[1].split()[1]
		if debug:
			print("Deployment up and running")
			print("deleting replica set to check it's self healing")
		rs=sp.getoutput("kubectl get rs")
		rs=rs.split("\n")[1].split()
		tup=sp.getstatusoutput("kubectl delete rs {}".format(rs[0]))
		if tup[0]==0:
			if debug:
				print("replica set deleted")
		while rs[3] =='3':
			rs=sp.getoutput("kubectl get rs")
			rs=rs.split("\n")[1].split()
		if debug:
			print("Replic set is now running again")
		pods=sp.getoutput("kubectl get pods")
		pods=pods.split("\n")
		if debug:
			print("Waiting for all pods to be running again")
		while len(pods) != 4:
			pods=sp.getoutput("kubectl get pods")
			pods=pods.split("\n")
		while pods[1].split()[2] != 'Running' or pods[2].split()[2] != 'Running' or pods[3].split()[2] != 'Running':
			pods=sp.getoutput("kubectl get pods")
			pods=pods.split("\n")
		if debug:
			print("All pods are running again")
		#print(pods[1].split()[2])
		if debug:
			print("scaling up the deployment")
		sp.getoutput("kubectl scale deploy/nginx-deployment --replicas=5")		
		deploy=sp.getoutput("kubectl get deploy")
		deploy=deploy.split("\n")[1].split()
		while deploy[3] != '5':
			deploy=sp.getoutput("kubectl get deploy")
			deploy=deploy.split("\n")[1].split()
		if debug:
			print("deployment scaled...")
			print("Scaling down the deployment")
		sp.getoutput("kubectl scale deploy/nginx-deployment --replicas=2")
		pods=sp.getoutput("kubectl get pods")
		pods=pods.split("\n")
		while len(pods) != 3:
			pods=sp.getoutput("kubectl get pods")
			pods=pods.split("\n")
		if debug:
			print("deployment has been scaled down")
			print("Exposing the deployment to NodePort")
		sp.getoutput("kubectl expose deploy/nginx-deployment --type=NodePort")
		port=sp.getoutput("kubectl get svc/nginx-deployment")
		port=port.split("\n")[1].split(":")[1].split("/")[0]
		tup=sp.getstatusoutput("curl {}:{}".format(masterIP,port))
		if tup[0]==0:
			if debug:
				print("deployment has been exposed and accessible successfully")
		else:
			if debug:
				print("error while exposing")
		tup=sp.getstatusoutput("kubectl delete svc/nginx-deployment")
		if tup[0]==0:
			if debug:
				print("service for nginx has been deleted")
		sp.getoutput("kubectl delete -f test-deploy.yaml")
		if debug:
			print("waiting for the pods to be terminated")
		pods=sp.getoutput("kubectl get pods")
		while pods != 'No resources found.':
			pods=sp.getoutput("kubectl get pods")
	else:
		if debug:
			print("error while creating deployment: {}".format(tup[1]))
	print("==============Test complete=============")
	test_case_time= time.time()  - start_time_test_case
	tests_time=time.time() - start_time_tests

	print("Time Taken by test="+str(test_case_time))
	print("Total Time elapsed="+str(tests_time))


def pod_with_probes():
	start_time_test_case=time.time()
	fh=open("pod_with_probes.yaml","w")
	fh.write("""apiVersion: apps/v1beta1
kind: Deployment
metadata:
  name: helloworld-deployment-with-probe
spec:
  selector:
    matchLabels:
      app: helloworld
  replicas: 1 # tells deployment to run 1 pods matching the template
  template: # create pods using pod definition in this template
    metadata:
      labels:
        app: helloworld
    spec:
      containers:
      - name: helloworld
        image: nginx
        ports:
        - containerPort: 80
        readinessProbe:
          # length of time to wait for a pod to initialize
          # after pod startup, before applying health checking
          initialDelaySeconds: 10
          # Amount of time to wait before timing out
          initialDelaySeconds: 1
          # Probe for http
          httpGet:
            # Path to probe
            path: /
            # Port to probe
            port: 80
        livenessProbe:
          # length of time to wait for a pod to initialize
          # after pod startup, before applying health checking
          initialDelaySeconds: 10
          # Amount of time to wait before timing out
          timeoutSeconds: 1
          # Probe for http
          httpGet:
            # Path to probe
            path: /
            # Port to probe
            port: 80""")
	fh.close()
	tup=sp.getstatusoutput("kubectl create -f pod_with_probes.yaml")
	if tup[0]==0:
		if debug:
			print("pod with probes is created")
		pods=sp.getoutput("kubectl get pods")
		pod_status=pods.split("\n")[1].split()[2]
		if debug:
			print("waiting for pod to be in running state")
		while pod_status != 'Running':
			pods=sp.getoutput("kubectl get pods")
			pod_status=pods.split("\n")[1].split()[2]
		if debug:
			print("pod is in running status")
		tup=sp.getstatusoutput("kubectl delete -f pod_with_probes.yaml")
		if tup[0]==0:
			if debug:
				print("pod deleted successfully")
	else:
		if debug:
			print("error in creating pod with probes")
	test_case_time= time.time()  - start_time_test_case
	tests_time=time.time() - start_time_tests
	print("=============Test case completed============")
	print("Time Taken by test="+str(test_case_time))
	print("Total Time elapsed="+str(tests_time))




def latency():
	start_time_test_case=time.time()
	print("==================Testing Latency of nfs server==============")

	tup=sp.getstatusoutput("mkdir /nfs_test")
	if tup[0]==0:
		if debug:
			print("Directory created for latency test")
		tup=sp.getstatusoutput("mount {}:{}   /nfs_test".format(nfsIP,nfsPATH))
		if tup[0]==0:
			if debug:
				print("Directory sucessfully mounted")
				print("creating file of 1Gi for uploading")
			tup=sp.getstatusoutput("dd if=/dev/zero  of=/try.txt count=1024  bs=1048576")
			if tup[0]==0:
				if debug:
					print("File created")
				start_time=time.time()
				tup=sp.getstatusoutput("cp /try.txt  /nfs_test")
				if tup[0]==0:
					if debug:
						print("File sucessfully copied in nfs server")
				end_time=time.time()
				time_taken=end_time-start_time
				print("Time taken in Transfering 1Gi of data: "+str(time_taken))
				sp.getoutput("rm -f /nfs_test/try.txt")
				if debug:
					print("File deleted from nfs directory")
				sp.getoutput("rm -f /try.txt") 
				if debug:
					print("File removed from local system")
				sp.getoutput("umount /nfs_test")
				sp.getoutput("rmdir /nfs_test")
				if debug:
					print("directory removed and deleted")
					print("======Test case sucessfull=====")
		else:
			print("error in mounting the directory")
	else:
		print("Error in creating the directory")

	test_case_time= time.time()  - start_time_test_case
	tests_time=time.time() - start_time_tests
	print("=============Test case completed============")
	print("Time Taken by test="+str(test_case_time))
	print("Total Time elapsed="+str(tests_time))



def versioning():
	start_time_test_case=time.time()
	print("==================Testing upgrading and rollback==============")
	fh=open("versioning.yaml","w")
	fh.write("""apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.7.9
        ports:
        - containerPort: 80""")
	fh.close()
	tup=sp.getstatusoutput("kubectl create -f versioning.yaml")
	if tup[0]==0:
		if debug:
			print("Deployment created")
		rs=sp.getoutput("kubectl get rs")
		rs=rs.split("\n")[1].split()
		while rs[3] != '3':
			rs=sp.getoutput("kubectl get rs")
			rs=rs.split("\n")[1].split()
		if debug:
			print("all instance of app is running of the application")
		tup=sp.getstatusoutput("kubectl set image deployment/nginx-deployment  nginx=nginx:1.9.1")
		if tup[0]==0:
			if debug:
				print("image of the running container is changed")
			rs = sp.getoutput("kubectl get rs")
			rs=rs.split("\n")[2].split()[3]
			while rs != '3':
				rs = sp.getoutput("kubectl get rs")
				rs=rs.split("\n")[2].split()[3]
			if debug:
				print("New pods are now running!!")
				print("going back to previous version")
			tup=sp.getstatusoutput("kubectl rollout undo deployment/nginx-deployment --to-revision=1")
		if tup[0]==0:
			if debug:
				print("waiting for that pods to be running")
			rs=sp.getoutput("kubectl get rs")
			rs=rs.split("\n")[1].split()[3]
			while rs != '3':
				rs=sp.getoutput("kubectl get rs")
				rs=rs.split("\n")[1].split()[3]
			if debug:
				print("Pods of previous version are now running")
		sp.getoutput("kubectl delete -f versioning.yaml")
		if debug:
			print("deployment deleted")
		print("===============Test Complete==============")
	else:
		if debug:
			print("error in creating deployment")

	test_case_time= time.time()  - start_time_test_case
	tests_time=time.time() - start_time_tests
	print("=============Test case completed============")
	print("Time Taken by test="+str(test_case_time))
	print("Total Time elapsed="+str(tests_time))



def job_pod():
	print("=================Creation and deletion of job pod================")
	fh=open("job.yaml","w")
	start_time_test_case=time.time()
	fh.write("""apiVersion: batch/v1
kind: Job
metadata:
  name: pi
spec:
  template:
    spec:
      containers:
      - name: pi
        image: perl
        command: ["perl",  "-Mbignum=bpi", "-wle", "print bpi(6)"]
      restartPolicy: Never
  backoffLimit: 4""")
	fh.close()
	tup=sp.getstatusoutput("kubectl create -f job.yaml")
	if tup[0]==0:
		if debug:
			print("Job pod created")
	pods=sp.getoutput("kubectl get pods")
	pod_status=pods.split("\n")[1].split()[2]
	if debug:
		print("waiting for the job to be completed")
	while pod_status != 'Completed':
		pods=sp.getoutput("kubectl get pods")
		pod_status=pods.split("\n")[1].split()[2]
	pod_name=pods.split("\n")[1].split()[0]
	log=sp.getoutput("kubectl logs {}".format(pod_name))
	if log == '3.14159':
		if debug:
			print("Job completed successfully")	
	tup=sp.getstatusoutput("kubectl delete -f job.yaml")
	if tup[0]==0:
		if debug:
			print("pod deleted successfully")
	test_case_time= time.time()  - start_time_test_case
	tests_time=time.time() - start_time_tests
	print("=============Test case completed============")
	print("Time Taken by test="+str(test_case_time))
	print("Total Time elapsed="+str(tests_time))


def cronjob_pod():
	start_time_test_case=time.time()
	print("========working of cronjob pod==========")
	fh=open("cronjob.yaml","w")
	fh.write("""apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: hello
spec:
  schedule: "*/1 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: hello
            image: busybox
            args:
            - /bin/sh
            - -c
            - date; echo Hello from the Kubernetes cluster
          restartPolicy: OnFailure""")
	fh.close()
	tup=sp.getstatusoutput("kubectl create -f cronjob.yaml")
	if tup[0]==0:
		if debug:
			print("cron job created sucessfully")
		pod=sp.getoutput("kubectl get pods")
		if debug:
			print("waiting 1 minute to check for cron job")
		if pod=='No resources found.':
			time.sleep(60)
		pod=sp.getoutput("kubectl get pods")
		pod=pod.split("\n")
		if len(pod)==2:
			if debug:
				print("cronjob working properly")
		tup=sp.getstatusoutput("kubectl delete -f cronjob.yaml")
		if tup[0]==0:
			if debug:
				print("cronjob has been deleted")
	else:
		print(tup[1])
	test_case_time= time.time()  - start_time_test_case
	tests_time=time.time() - start_time_tests
	print("=============Test case completed============")
	print("Time Taken by test="+str(test_case_time))
	print("Total Time elapsed="+str(tests_time))



def env_check_cm():
	start_time_test_case=time.time()
	print("===============Creation of config map and passing it as Env Var==========")
	fh=open("conf-env.yaml","w")
	fh.write("""apiVersion: v1
kind: Pod
metadata:
   name: test-env-cm
spec:
  containers:
     - name: env-test-conf
       image: bash
       env:
         - name: AUTHOR
           valueFrom:
              configMapKeyRef:
                  name: test
                  key: name
       command: ["echo"]
       args: ["$(AUTHOR)"]""")
	fh.close()
	tup=sp.getstatusoutput("kubectl create configmap test --from-literal=name=tarun")
	if tup[0]==0:
		if debug:
			print("config map has been created")
			print("checking if info is saved in clear text or not")
		name=sp.getoutput("kubectl get cm/test -o yaml")
		name=name.split("\n")[2].strip().split(":")[1].strip()
		if name == 'tarun':
			if debug:
				print("data is in clear test")
				print("creating pod with passing this configMap as env var")
		tup=sp.getstatusoutput("kubectl create -f conf-env.yaml")
		if tup[0]==0:
			if debug:
				print("pod has been created sucessfully")
			pod=sp.getoutput("kubectl get po/test-env-cm")
			pod_status=pod.split("\n")[1].split()[2]
			if debug:
				print("Waiting for pod to be completed")
			while pod_status != 'Completed':
				pod=sp.getoutput("kubectl get po/test-env-cm")
				pod_status=pod.split("\n")[1].split()[2]
			if debug:
				print("pod is completed")
			log=sp.getoutput("kubectl logs test-env-cm")
			if log == 'tarun':
				if debug:
					print("Env variables is passed correctly inside the pod")
			else:
				if debug:
					print("some errors in passing the env var")
			if debug:
				print("deleting the pod and config map")
			sp.getoutput("kubectl delete cm/test")
			sp.getoutput("kubectl delete -f conf-env.yaml")
	else:
		if debug:
			print("error in creating config map")
	test_case_time= time.time()  - start_time_test_case
	tests_time=time.time() - start_time_tests
	print("=============Test case completed============")
	print("Time Taken by test="+str(test_case_time))
	print("Total Time elapsed="+str(tests_time))



def env_check_secret():
	start_time_test_case=time.time()
	print("===============Creation of secret and passing it as Env Var==========")
	fh=open("sec-env.yaml","w")
	fh.write("""apiVersion: v1
kind: Pod
metadata:
   name: test-env-sec
spec:
  containers:
     - name: env-test-sec
       image: bash
       env:
         - name: AUTHOR
           valueFrom:
              secretKeyRef:
                  name: test
                  key: name
       command: ["echo"]
       args: ["$(AUTHOR)"]""")
	fh.close()
	tup=sp.getstatusoutput("kubectl create secret generic test --from-literal=name=tarun")
	if tup[0]==0:
		if debug:
			print("secret has been created")
			print("checking if info is saved encoded or not")
		name=sp.getoutput("kubectl get secret/test -o yaml")
		name=name.split("\n")[2].strip().split(":")[1].strip()
		if name != 'tarun':
			if debug:
				print("values in secret are succesfully encoded")
		tup=sp.getstatusoutput("kubectl create -f sec-env.yaml")
		if tup[0]==0:
			if debug:
				print("pod has been created sucessfully")
			pod=sp.getoutput("kubectl get po/test-env-sec")
			pod_status=pod.split("\n")[1].split()[2]
			if debug:
				print("Waiting for pod to be completed")
			while pod_status != 'Completed':
				pod=sp.getoutput("kubectl get po/test-env-sec")
				pod_status=pod.split("\n")[1].split()[2]
			if debug:
				print("pod is completed")
			log=sp.getoutput("kubectl logs test-env-sec")
			if log == 'tarun':
				if debug:
					print("Env variables is passed correctly inside the pod")
			else:
				if debug:
					print("some errors in passing the env var")
			if debug:
				print("deleting the pod and secret")
			sp.getoutput("kubectl delete secret/test")
			sp.getoutput("kubectl delete -f sec-env.yaml")
	test_case_time= time.time()  - start_time_test_case
	tests_time=time.time() - start_time_tests
	print("=============Test case completed============")
	print("Time Taken by test="+str(test_case_time))
	print("Total Time elapsed="+str(tests_time))


def env_check():
	start_time_test_case=time.time()
	print("=================Pod with env variables==============")
	fh=open("env_pod.yaml","w")
	fh.write("""apiVersion: v1
kind: Pod
metadata:
   name: test-env
spec:
  containers:
     - name: env-test
       image: bash
       env:
         - name: DEMO
           value: "Hello"
       command: ["echo"]
       args: ["$(DEMO)"]""")
	fh.close()
	tup=sp.getstatusoutput("kubectl create -f env_pod.yaml")
	if tup[0] == 0:
		if debug:
			print("pod with enviornment variable is created")
		pod=sp.getoutput("kubectl get po/test-env")
		pod_status=pod.split("\n")[1].split()[2]
		if debug:
			print("Waiting for pod to be completed")
		while pod_status != 'Completed':
			pod=sp.getoutput("kubectl get po/test-env")
			pod_status=pod.split("\n")[1].split()[2]
		log=sp.getoutput("kubectl logs test-env")
		if log == 'Hello':
			if debug:
				print("Env variable is successfully passed inside pod")
		else:
			if debug:
				print("Env variable is not correctly passes")
		if debug:
			print("Deleting the pod")
		sp.getoutput("kubectl delete -f env_pod.yaml")
	else:
		if debug:
			print("error in creating pod")
			print(tup[1])
	test_case_time= time.time()  - start_time_test_case
	tests_time=time.time() - start_time_tests
	print("=============Test case completed============")
	print("Time Taken by test="+str(test_case_time))
	print("Total Time elapsed="+str(tests_time))



def check_limit():
	start_time_test_case=time.time()
	print("===========Testing LimitRange==============")
	fh=open("limits.yaml","w")
	fh.write("""apiVersion: v1
kind: LimitRange
metadata:
  name: limit
spec:
  limits:
  - max:
      cpu: "700m"
      memory: "1Gi"
    min:
      cpu: "100m"
      memory: "100Mi"
    type: Pod
  - max:
      cpu: "1"
      memory: "1Gi"
    min:
      cpu: "50m"
      memory: "90Mi"
    default:
      cpu: "500m"
      memory: "400Mi"
    defaultRequest:
      cpu: "500m"
      memory: "400Mi"
    type: Container""")
	fh.close()
	fh1=open("pod.yaml","w")
	fh1.write("""apiVersion: v1
kind: Pod
metadata:
     name: test-pod
     labels:
         app-lang: python
         type: back-end
spec:
    containers:
       - name: test-cont
         image: nginx
         resources:
           requests:
              memory: '1000Mi'
              cpu: '2'""")
	fh1.close()
	tup=sp.getstatusoutput("kubectl create -f limits.yaml")
	if tup[0]==0:
		if debug:
			print("LimitRange created")
		tup=sp.getstatusoutput("kubectl get limits limit")
		tup=sp.getstatusoutput("kubectl create -f pod.yaml")
		if tup[0]==0:
			if debug:
				print("Error in creating limitrange")
		else:
			if debug:
				print("LimitRange is working correctly")

		sp.getoutput("kubectl delete -f limits.yaml")
		if debug:
			print("LimitRange deleted")
	else:
		print("error in creating the limitrange")
	test_case_time= time.time()  - start_time_test_case
	tests_time=time.time() - start_time_tests
	print("=============Test case completed============")
	print("Time Taken by test="+str(test_case_time))
	print("Total Time elapsed="+str(tests_time))



def check_quota():
	print("==============Creating quota and checking it===========")
	start_time_test_case=time.time()
	fh=open("quota.yaml","w")
	fh.write("""apiVersion: v1
kind: ResourceQuota
metadata:
    name: my-quota
spec:
  hard:
    cpu: '100'
    memory: '10Gi'
    pods: '3'""")
	fh.close()
	fh1=open("rs.yaml","w")
	fh1.write("""apiVersion: apps/v1
kind: ReplicaSet
metadata:
     name: test-pod
     labels:
       app: python
       type: back-end
spec:
    template:
       metadata:
          name: test-pod
          labels:
             app-lang: python
             type: back-end
       spec:
          containers:
              - name: test-cont
                image: nginx
    replicas: 3
    selector:
       matchLabels:
          app-lang: python
          type: back-end""")
	fh1.close()
	sp.getoutput("kubectl create -f rs.yaml")
	tup=sp.getstatusoutput("kubectl create -f quota.yaml")
	if tup[0]==0:
		if debug:
			print("quota has been created")
		sp.getoutput("kubectl scale rs/test-pod --replicas=5")
		rs=sp.getoutput("kubectl get rs/test-pod")
		rs=rs.split("\n")[1].split()[2]
		if rs != '5':
			if debug:
				print("quota is sucessfully created")

	sp.getoutput("kubectl delete -f rs.yaml")
	sp.getoutput("kubectl delete -f quota.yaml")
	if debug:
		print("quota is deleted")
	test_case_time= time.time()  - start_time_test_case
	tests_time=time.time() - start_time_tests
	print("=============Test case completed============")
	print("Time Taken by test="+str(test_case_time))
	print("Total Time elapsed="+str(tests_time))




if len(sys.argv) == 1:
	print("Please specify the tests to be run...")
elif sys.argv[1] == 'all':
	network_layer()
	single_pod_test()
	multi_pod_test()
	pod_with_probes()
	job_pod()
	cronjob_pod()
	versioning()
	rs_test()
	deployment()
	sc_pvc()
	latency()
	check_limit()
	check_quota()
	namespace()
	metric_server()
	env_check()
	env_check_cm()
	env_check_secret()
else:
	for x in sys.argv:
		if x== 'deployment':
			deployment()
		if x == 'pod':
			single_pod_test()
			multi_pod_test()			
                if x=='replicaset':
			rs_test()
		if x=='namespace':
			namespace()
		if x=='metrics':
			metric_server()
		if x=='pod_with_probes':
			pod_with_probes()
		if x == 'versioning':
			versioning()
		if x == 'job_pod':
			job_pod()
		if x == 'cronjob':
			cronjob_pod()
		if x == 'limits':
			check_limit()
		if x == 'quota':
			check_quota()
		if x == 'env':
			env_check()
			env_check_cm()
			env_check_secret()
		if x == 'storageclass':
			sc_pvc()
		if x == 'latency':
			latency()
		if x == 'network':
			network_layer()
