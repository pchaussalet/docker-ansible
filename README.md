Ansible Module for Docker
=========================

This module allows you to use [Ansible](http://ansible.cc) to provision and de-provision Linux containers using the
[docker](http://docker.io) container engine. 

Installation
============

1. Install [docker](http://www.docker.io/gettingstarted/)
2. Install [docker-py](https://github.com/dotcloud/docker-py) on the docker server, and/or on the host you will be
   running ansible playbooks from if you would like to use the docker remote API instead of ansible's SSH session. 

   <pre>
   git clone https://github.com/dotcloud/docker-py.git
   cd docker-py
   sudo python setup.py install 
   </pre>

   NB: In order to use the docker remote API  you will need to use `local_action` in your playbooks and set
   the `docker_url` argument to `http://${inventory_hostname}`.

2. Copy `docker-ansible.py` to your ansible module directory as `docker` (e.g. `/usr/local/share/ansbile/docker`)

   <pre>
   curl https://raw.github.com/cove/docker-ansible/master/docker-ansible.py > docker
   sudo mv docker /usr/local/share/ansible
   </pre>

Demo
====

[http://ascii.io/a/3348](http://ascii.io/a/3348)

Usage Examples
==============
The module will try to determine which containers it has already started on subsequent runs of the playbook.

Start one docker container running tomcat in each host of the web group and bind tomcat's listening port to 8080
on the host:

	- name: start tomcat
	  hosts: web
	  user: root
	  tasks:
	  - name: run tomcat servers
	    action: docker image=cove/tomcat7 command=/start-tomcat.sh ports=:8080

The tomcat server's port is NAT'ed to a dynamic port on the host, but you can determine which port the server was
mapped to using $DockerContainers:

	- name: start tomcat 
	  hosts: web
	  user: root
	  tasks:
	  - name: run tomcat servers
	    action: docker image=cove/tomcat7 command=/start-tomcat.sh ports=8080 count=5
	  - name: Display IP address and port mappings for containers
	    action: shell echo Mapped to ${inventory_hostname}:${item.NetworkSettings.PortMapping.8080}
	    with_items: $DockerContainers

Just as in the previous example, but iterates through the list of docker containers with a sequence:

	- name: start tomcat
	  hosts: web
	  user: root
	  vars:
	  	start_containers_count: 5
	  tasks:
	  - name: run tomcat servers
	    action: docker image=cove/tomcat7 command=/start-tomcat.sh ports=8080 count=$start_containers_count
	  - name: Display IP address and port mappings for containers
	    local_action: shell echo Mapped to ${inventory_hostname}:${DockerContainers[${item}].NetworkSettings.PortMapping.8080}
	    with_sequence: start=0 end=$start_containers_count

Stop all of the running tomcat containers:

	- name: stop tomcat
	  hosts: web
	  user: root
	  tasks:
	  - name: run tomcat servers
	    action: docker image=cove/tomcat7 command=/start-tomcat.sh state=absent

Parameters
==========
<table>
<tr>
<th class="head">parameter</th>
<th class="head">required</th>
<th class="head">default</th>
<th class="head">choices</th>
<th class="head">comments</th>
</tr>
<tr>
<td>username</td>
<td>no</td>
<td></td>
<td><ul></ul></td>
<td>Set remote API username</td>
</tr>
<tr>
<td>memory_limit</td>
<td>no</td>
<td>256MB</td>
<td><ul></ul></td>
<td>Set RAM allocated to container</td>
</tr>
<tr>
<td>env</td>
<td>no</td>
<td></td>
<td><ul></ul></td>
<td>Set environment variables</td>
</tr>
<tr>
<td>image</td>
<td>yes</td>
<td></td>
<td><ul></ul></td>
<td>Set container image to use</td>
</tr>
<tr>
<td>volumes</td>
<td>no</td>
<td></td>
<td><ul></ul></td>
<td>Set volume(s) to mount on the container</td>
</tr>
<tr>
<td>detach</td>
<td>no</td>
<td>True</td>
<td><ul></ul></td>
<td>Enable detached mode on start up, leaves container running in background</td>
</tr>
<tr>
<td>memory_swap</td>
<td>no</td>
<td></td>
<td><ul></ul></td>
<td>Set virtual memory swap space allocated to container</td>
</tr>
<tr>
<td>count</td>
<td>no</td>
<td>1</td>
<td><ul></ul></td>
<td>Set number of containers to run</td>
</tr>
<tr>
<td>password</td>
<td>no</td>
<td></td>
<td><ul></ul></td>
<td>Set remote API password</td>
</tr>
<tr>
<td>hostname</td>
<td>no</td>
<td></td>
<td><ul></ul></td>
<td>Set container hostname</td>
</tr>
<tr>
<td>docker_url</td>
<td>no</td>
<td>http://127.0.0.1:4243</td>
<td><ul></ul></td>
<td>URL of docker host to issue commands to</td>
</tr>
<tr>
<td>state</td>
<td>no</td>
<td>present</td>
<td><ul><li>present</li><li>stop</li><li>absent</li><li>kill</li><li>restart</li></ul></td>
<td>Set the state of the container</td>
</tr>
<tr>
<td>command</td>
<td>yes</td>
<td></td>
<td><ul></ul></td>
<td>Set command to run in a container on startup</td>
</tr>
<tr>
<td>dns</td>
<td>no</td>
<td></td>
<td><ul></ul></td>
<td>Set custom DNS servers for the container</td>
</tr>
<tr>
<td>volumes_from</td>
<td>no</td>
<td></td>
<td><ul></ul></td>
<td>Set shared volume(s) from another container</td>
</tr>
<tr>
<td>ports</td>
<td>yes</td>
<td></td>
<td><ul></ul></td>
<td>Set private to public port mapping specification (e.g. ports=22,80 or ports=:8080 maps 8080 directly to host)</td>
</tr>
</table>