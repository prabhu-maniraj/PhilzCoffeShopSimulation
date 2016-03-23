#!/usr/bin/env python
from __future__ import division
import random
import simpy
import itertools
import time
import csv



INTV_CUSTOMERS=10.0
MIN_PATIENCE=1 #minimum patience of the customer
MAX_PATIENCE=3 # maximum patience of the customer
CONTAINER_SIZE=100 # capacity of bean_container
THRESHOLD=10 # threshold percentage for refilling bean_container
FETCH_BEAN_TIME=20 # time to fetch coffee beans while refilling bean_container
bean_usage={"lightRoast":20, "mediumRoast": 10, "darkRoast":5}
prep_time={"small":3, "medium":5, "large":7}
cssv = csv.writer(open("names.csv", "wb"))
global wait_time


def source(env,interval,counter,container,checkout_counter):
	#Generating Customers after a random interval
	for i in itertools.count():
		c=customer(env,i,counter,container,checkout_counter,time_to_order=10.0) 
		env.process(c)
		t= random.expovariate(1.0/interval) #random interval
		yield env.timeout(t) 

def customer(env,customer_no,counter,container,checkout_counter,time_to_order):
	arrive=env.now
	#bean_usage=random.randint(*BEAN_USAGE)
	print("Customer %d arrived at %7.4f" %(customer_no,arrive))
    

	with counter.request() as req:
		patience=random.uniform(MIN_PATIENCE, MAX_PATIENCE) # random patience value between MIN_PATIENCE and MAX_PATIENCE
		print("Customer %d patience is %6.3f" %(customer_no,patience))
		results=yield req | env.timeout(patience)

		wait=env.now - arrive #time of customer waiting in queue before going to order or before leaving queue due to no patience

		if req in results:
			print("%7.4f: Customer %d Waited for %6.3f" %(env.now,customer_no,wait))

			time_to_order=random.expovariate(1.0/time_to_order) # random time to order item
			print("Customer %d takes %6.3f time near counter" %(customer_no,time_to_order))
			usage= random.choice(bean_usage.keys());
			number_of_coffee=random.randint(1,10) #random number of coffee chosen by customer
			size=random.choice(prep_time.keys())
			yield env.timeout(time_to_order)
			print('%7.4f: Customer %d has finished ordering %d %s %s' %(env.now,customer_no,number_of_coffee,size,usage))
			bean_amount=number_of_coffee * bean_usage[usage]
			if container.level > bean_amount:
				yield container.get(bean_amount)
				print("Bean_Usage is %d" %(bean_amount))
				print("Container level is %d" %(container.level))
				global wait_time
				wait_time= number_of_coffee * prep_time[size]
				print("%7.4f: Customer %d wait_time after ordering is %f" %(env.now,customer_no,wait_time))

			else:
				print("Sorry, Your order may take time as the process of refilling coffee_beans has to be done")

			


		else:
			print("%7.4f: Customer %d left out  due to no patience after %6.3f" %(env.now,customer_no,wait))
			return


	yield env.timeout(wait_time) #customer waiting after giving order
	env.process(checkout(env,checkout_counter,customer_no,arrive)) #checking out after receiving the order

  


def container_control(env,container):
	#monitors bean_container to refill it if necessary
	while True:
		condition= container.level/container.capacity
		condition_percentage=condition * 100
		

		if condition_percentage< THRESHOLD:
			
			yield env.process(fill(env,container)) #refill the bean_container

		else:
			#print("inside else case in refill")
			yield env.timeout(10)
		   
		


def fill(env,container):
	print("inside fill")
	print('Calling for Refilling container with beans at %7.4f' % env.now)
	yield env.timeout(FETCH_BEAN_TIME)
	
	print("Received beans for refilling at %7.4f" % env.now)
	amount=container.capacity-container.level
	print("Refilled %d" %(amount))
	yield container.put(amount)
	print("Container level after refilling is %d" %(container.level))


def checkout(env,checkout_counter,customer_no,arrive):
	#print("inside checkout")
	#print(env.now)
	with checkout_counter.request() as req:
		yield req
		print("Customer %d paying bill at %7.4f" %(customer_no, env.now))
		total_time_in_shop= env.now-arrive
		r1= str(customer_no)+','+str(total_time_in_shop)
		cssv.writerow([r1])
		yield env.timeout(10)


		
		
		



    

	






if __name__ == "__main__":

	#print "inside main"
	env=simpy.Environment()

	counter=simpy.Resource(env, capacity=2) #creating 2 resources representing service counters
	checkout_counter=simpy.Resource(env, capacity=1) #creating a checkout_counter resource
	bean_container=simpy.Container(env, CONTAINER_SIZE,init=CONTAINER_SIZE) #creating a container named bean_container which holds coffee beans.
	env.process(container_control(env,bean_container)) #container_control process monitors bean_container and refills it when it is less than THRESHOLD
	env.process(source(env,INTV_CUSTOMERS,counter,bean_container,checkout_counter))# source process is  used to monitor customers and theiractivities at Service Counter
	sim_time=input("Enter the Simulation time:") # Providing time over which simulation of environment takes place
	env.run(until=int(sim_time)) # running the environment