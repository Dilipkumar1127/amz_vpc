import time
import boto
from boto import vpc
from boto import ec2

#REGION_NAME = 'us-east-1'
conn = boto.vpc.VPCConnection()

#create VPC
vpc = conn.create_vpc('10.0.0.0/16')

#create public subnet
pubsub = conn.create_subnet(vpc.id, '10.0.0.0/24')

#create private subnet
prvsub = conn.create_subnet(vpc.id, '10.0.1.0/24')
print "Subnets Done!"

#create the internet gateway
igw = conn.create_internet_gateway()
print "IGW Done!"

#attach the internet gateway
conn.attach_internet_gateway(igw.id, vpc.id)

#create routetable
rt = conn.create_route_table(vpc.id)

#associate route table for public subnet
conn.associate_route_table(rt.id,pubsub.id)

#public route to IGW
conn.create_route(rt.id, '0.0.0.0/0',igw.id)


#setup Security Group
sg_public = conn.create_security_group('SG for Public Sbunet','Public group for VPC via Python',vpc.id)
sg_public.authorize(ip_protocol='tcp', from_port=22,to_port=22,cidr_ip='0.0.0.0/0')
sg_public.authorize(ip_protocol='tcp', from_port=80,to_port=80,cidr_ip='0.0.0.0/0')


sg_private = conn.create_security_group('SG for Private Sbunet','Private group for VPC via Python',vpc.id)
sg_private.authorize(ip_protocol='tcp', from_port=22,to_port=22,cidr_ip='0.0.0.0/0')


vpc.add_tag("Name", "Python VPC")
pubsub.add_tag("Name","Public Subnet by Python")
prvsub.add_tag("Name","Private Subnet by Python")
igw.add_tag("Name","Python IGW")
rt.add_tag("Name","Python Route Table")
sg_public.add_tag ("Name","Public Subnet SG")
sg_private.add_tag("Name","Private Subnet SG")
print "Security Groups Done!"
print 'VPC Complete!'

#=======================================================================
#Time to create the NAT instance in the public space
ec2 = boto.ec2.connect_to_region('us-east-1')
reservation = ec2.run_instances(
        'ami-184dc970',
        key_name='east_keypair',
        instance_type='t2.micro',
        security_group_ids=[sg_public.id],
        subnet_id=pubsub.id)

inst = reservation.instances[0]
inst.add_tag("Name","NAT Instance by Python")
print "Tagged the instance!"


while inst.state == 'pending':
	time.sleep(5)
	inst.update()

#Change the attribute for NAT'ing
ec2.modify_instance_attribute(inst.id, attribute='sourceDestCheck', value=False)
print "Attribute changed!"

#Assign elastic IP 54.173.234.49 to the NAT Instance
eip = ec2.allocate_address(None, False)
eip.associate(inst.id,None, None,False,False)


#========================================================================

#========================================================================
# Create the Private Instance
ec2 = boto.ec2.connect_to_region('us-east-1')
reservation = ec2.run_instances(
        'ami-b66ed3de',
        key_name='east_keypair',
        instance_type='t2.micro',
        security_group_ids=[sg_private.id],
        subnet_id=prvsub.id)

inst = reservation.instances[0]
inst.add_tag("Name","Private Instance by Python")
print "Tagged the instance!"


while inst.state == 'pending':
	time.sleep(5)
	inst.update()
#=========================================================================

#Now lets point Private routes to the NAT
rtPrv = conn.create_route_table(vpc.id)
conn.associate_route_table(rtPrv.id,prvsub.id)
print rtPrv.id + " Createdf or Private subnet : " + prvsub.id

#public route to NAT instance
conn.create_route(rtPrv.id, '0.0.0.0/0',None,inst.id)
rtPrv.add_tag("Name","Private Route Through NAT Python")


print "DONE!!!!!!"


