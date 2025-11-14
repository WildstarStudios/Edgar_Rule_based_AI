# clustering using Kubernetes
* 4 Pi's handle Ai Engine and Modules individually
* 5th Pi handles load balancing, Web Ui, traffic, and user accounts
* each 5th pi will handle updating the ai model per node on each cluster.
* handle traffic receiving and forwarding with traffic.py to 5th Pi

# Scaling
* Cloudflare load balancer to ballence clusters automaticly
* Specilzed cluster to store user data for fetching from other servers
* Store updates on specialized cluster to store module and model files
* Sync user data across nodes until end of the day to specilzed server
* Scaling 5th node Pi's to use nuitka to compile the runtime