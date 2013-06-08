Ansible Module for Docker
=========================

This module allows you to use [Ansible](http://ansible.cc) to provision and de-provision Linux containers using the [docker](http://docker.io) container engine. 

Installation
============
TBD

Usage Examples
==============

Start one docker container running tomcat in each host of the web group and bind tomcat's listening port to 8080 on the host:

	- name: start tomcat
	  hosts: web
	  user: root
	  tasks:
	  - name: run tomcat servers
	    action: docker image=cove/tomcat7 command=/start-tomcat.sh ports=:8080

The tomcat server's port is NAT'ed to a dynamic port on the host, but you can determine which port the server was mapped to using $DockerContainers:

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

Idempotence
===========
The module will try to determine if the containers are already running, need to be started or stopped etc. This is 
currently accomplished by comparing the image name and command to the currently running containers to determine if t
hey are the same containers previously started. 

At some point Docker may support tagging of running containers which will make this more robust. Currently the only
other option would be to track the instances IDs of the started containers in Ansible, which doesn't seem like the
Ansible way of doing things.


