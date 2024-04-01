"""
    @author: Massiles Ghernaout (github.com/MassiGy)

    We need to represent a network of routers and machines connected to these routers.
    So the main entities that we have to deal with are: 
        - router
        - normal machine ( like a computer )

    Each router contains: 
        - list of interfaces (optional)
        - list of nieghbors
        - routing table
    
    Each normal machine contains: 
        - list of interfaces (optional)
        - list of routers in the nieghborhood.
        - connections list ( other machines that we've previously talked to )


    
    Each router is connected to other routers which are its nieghbors.
    Each machine is connected to one router which is its gateway.

    Then using the Bellman-Ford algorithm, we can setup the routing tables for each router.
    Going from the routing tables, we can find paths from one machine to another.


    A router will be represented by a dictionnary: 
    router_type = {
        "id": int,
        "type": "router",
        "interfaces": [string],
        "nieghbors": [(router_id:int, cost:int)],
        "routing_table": dict[int, [int]]  #  mapping id of dist router to a list of best (routers(ids), total_cost) tuples to follow.
    }

    A machine will be represented by a dictionnary: 
    machine_type = {
        "id": int,
        "type": "machine",
        "interfaces": [string],
        "nieghbors": [router_id:int],
        "prev_connections": [(machine_id:int, total_cost:int)]      # maybe consider storing the path 
    }

    A network will be represented by a tuple: 
    network_type = ([router_type], [machine_type])

    So for representing all of this to the user, we are going to start simple and easy and use the stdout on the console.
    Or, we can use xdot tool to represent the network if it appears to be hard to do so on the console.

"""

########################################################################
####################### Program globals    #############################
########################################################################

# declare our routers   ( seed data )
"""
    NOTE: make sure that the ids of the routers start at 0.
"""
routers:list[dict] = [
    {
        "id": 0,
        "type": "router",
        # "interfaces": ["eth0", "eth1", "wlo1"],
        "nieghbors": [(1, 1), (2,2)],
        "routing_table": {}
    },
    {
        "id": 1,
        "type": "router",
        # "interfaces": ["eth0", "wlo1"],
        "nieghbors": [(0, 1), (2,2),(3,3), (4,1)],
        "routing_table": {}
    },
    {
        "id": 2,
        "type": "router",
        # "interfaces": ["eth0", "eth1"],
        "nieghbors": [(0, 2), (1,2), (4,3)],
        "routing_table": {}
    },
    {
        "id": 3,
        "type": "router",
        # "interfaces": ["eth0", "eth1"],
        "nieghbors": [(1, 3), (4,1),(5,1)],
        "routing_table": {}
    },
    {
        "id": 4,
        "type": "router",
        # "interfaces": ["eth0", "eth1"],
        "nieghbors": [(1,1), (2,3), (3,1),(5,3)],
        "routing_table": {}
    },
    {
        "id": 5,
        "type": "router",
        # "interfaces": ["eth0", "eth1"],
        "nieghbors": [(3, 1), (4,3)],
        "routing_table": {}
    }
]


# declare our machines (optional)
"""
    NOTE: make sure that the ids of the machines start at 0.
"""
machines:list[dict]= [
    # {
    #     "id": 1,
    #     "type": "machine",
    #     # "interfaces": ["wlo1"],
    #     "nieghbors": [1],
    #     "prev_connections": []     
    # },
    # {
    #     "id": 2,
    #     "type": "machine",
    #     # "interfaces": ["eth0"],
    #     "nieghbors": [0],
    #     "prev_connections": []     
    # },
    # {
    #     "id": 3,
    #     "type": "machine",
    #     # "interfaces": ["eth0"],
    #     "nieghbors": [2],
    #     "prev_connections": []     
    # }
]

# declare our network
network:tuple[list[dict], list[dict]] = (routers, machines)



########################################################################
####################### Program procedures #############################
########################################################################

# declare a procedure for representing the network
def represent_network(network:tuple[routers: list[dict], machines: list[dict]], tohighlight:list[(int, int)]=[]) -> None:
    """ 
        @author: Massiles Ghernaout (github.com/MassiGy)

        we are going to write the network presentation to a file,
        we are going to use the xdot markup language to represent the mesh-like network.
        the filename will be network.dot, and can be viewed using "$ xdot network.dot ".

        NOTE: make sure that the ids of the routers and the machines start at 0.
    """

    # use the w flag to clear the file first
    file = open("./network.dot", "w")

    # this will be the accumulator that will be flushed to the file
    content = ""

    # extract our data
    routers = network[0]
    machines = network[1]

    if len(routers) == 0: 
        print("network should have a non blank routers list")
        file.close()
        return

    # add the xdot leading markup 
    content +="digraph network {\n" 
    

    for router in routers:  
        for nieghbor in router["nieghbors"]: 
            # nieghbor is a tuple(router_id:int, cost:int)
            content += "\tr_"+str(router["id"]+1) +"->r_"+str(nieghbor[0]+1)
            content += ' [label ="'+str(nieghbor[1])+'"]'
            if (router["id"], nieghbor[0]) in tohighlight: 
                content += ' [color ="red"]'


            content += ";\n"
        


    for machine in machines:
        for nieghbor in machine["nieghbors"]: 
            # nieghbor is a router_id:int
            content += "\tm_"+str(machine["id"]) +"->r_"+str(nieghbor+1)
            content += ";\n"


    # add the xdot trailing markup 
    content +="}\n" 
    file.write(content) 
    file.close()
    return 


# declare a procedure to calculate our routing tables
def setup_routing_tables(routers:list[dict])-> None: 
    """ 
        @author: Massiles Ghernaout (github.com/MassiGy)

        NOTE: I've been able to write this algorithm from scratch 
        thanks to Pr. Geoffrey Messier and his lecture about Routing
        Algorithms.
        Link: https://www.youtube.com/watch?v=Ko7BChxlAFU&list=PL7sWxFnBVJLXZdk6_kPjcfOJBT-H1VSG1&index=19


        we are going to iterate through the routers list, and foreach 
        router we are going to setup the routing table.

        The routing table is a dictionary mapping each destination to 
        a list of routers which represent the next hops to follow, this
        list will be in ascending order regarding the cost of each hop.

        To do so, we'll use the Bellman-Ford algorithm. The steps are simple:
        - set a destination.
        - set the cost for reaching the destination from itself to 0.
        - set the seed cost of all the routers to that destination to be infinity.
        - going from the destination, update the routing tables of its nieghbors to 
          indicate the correct cost that can be found in thier nieghbors list. 
        - iterate through all the routers of the network.
        - for each router, update the routing table entry indicating how to reach 
          destination by asking its nieghbors for a better next hop ( lower cost )
        - if some nieghbors do not know how to reach the destination in the first
          iteration pass, iterate over again from the start.
        
        - do this for every router out there as a destination. 

        NOTE: The only issue with this algorithm is that it does not indicate 
        the list of fallback routers to use if the primary (best next hop) one
        is down. So as Pr. Geoffrey Messier pointed out in the video, the algorithm
        should be re-executed periodicaly to keep the routing table reliable, thus
        making the routing and the network self-healing.
    """

    if len(routers) == 0: 
        print("routers list should not be blank for setting up the routing tables.")
        return

    infinity = pow(10,10)
    # for _ in routers: 
    for router in routers: 
        # reset the routing table

        # set the first entry, indicating that to reach self the cost==0 
        router["routing_table"].__setitem__(router["id"], [(router["id"], 0)])


        # let destination to be r 
        destination = router
        
        # start the seed as Bellman-Ford algorithm suggest (start at a cost of infinity)
        for _r in routers: 
            if _r != destination:
                _r["routing_table"].__setitem__(destination["id"], [(-1, infinity)])

        # update the values on the routers that have destination as a nieghbor
        destination_nieghbors = destination["nieghbors"]    # connections are bidirectionnal

        for _r in destination_nieghbors: 
            # _r is a tuple of (router_id:int, cost:id)
            cost_to_destination=infinity

            # find the cost to destination going from _r
            for n in routers[_r[0]]["nieghbors"]: 
                if n[0] == destination["id"]:
                    cost_to_destination = n[1]
                    break

            routers[_r[0]]["routing_table"][destination["id"]].append(
                (
                    destination["id"],
                    cost_to_destination
                )
            )

        for _ in routers: 
            # we iterate quadratically since at the end of a cycle of iterations, 
            # we can end up with routers that do not know how to reach the destination
            # since they need to wait for thier nieghbors to know that informations first. 
            # Besides, iterating quadratically can optimize the routing tables, since we can 
            # have a situation where a router find out that one of its nieghbors has a better
            # cost compared to its own, since its own cost was calculated earlier. 

            for r in routers: 
                if r == destination: 
                    continue

                # now, starting from our start neighbors,
                # we need to ask each neighbors if there is a better route 
                # for reaching the destination and we only update our routing
                # table if there is a better route then the one we've registered. 
                start = r
                nieghbors = start["nieghbors"]
                
                for nieghbor in nieghbors: 
                    # nieghbor is a tuple of (router_id:int, cost:int)

                    n = routers[nieghbor[0]]
                    nieghbor_to_dest_best_hop = n["routing_table"][destination["id"]][-1]
                    nieghbor_to_destination_cost = nieghbor_to_dest_best_hop[1]

                    if nieghbor_to_destination_cost == infinity: 
                        continue
                    
                    start_to_nieghbor_cost = nieghbor[1]

                    start_to_destination_cost = start["routing_table"][destination["id"]][-1][1]
                    if  start_to_nieghbor_cost + nieghbor_to_destination_cost < start_to_destination_cost:
                        # we append instead of overriding to keep track of the alternative routes in case 
                        # where the best next hop is dead or subjected to intense traffic
                        # this means that the best next hop will be at the end of the list

                        start["routing_table"][destination["id"]].append(
                                (
                                    nieghbor[0],
                                    start_to_nieghbor_cost +nieghbor_to_destination_cost
                                )
                        )

    return


# declare a procedure for finding the best route path
def find_best_route(routers:list[dict], src:dict, dest:dict)->list[int]:
    """ 
        @author: Massiles Ghernaout (github.com/MassiGy)

        Going from the routing tables, it is really easy to 
        find a path, it is just a matter of jumping from point
        to point starting from the destination entry in the src 
        routing table. All ways look for the destination entry, 
        and follow that router.
    """
    path = []

    if src not in routers or dest not in routers: 
        print("source and destination routers should be in the routers list to find a path.")

    path.append(src["id"])
    
    curr = src["routing_table"][dest["id"]][0][0]
    while curr != dest["id"]: 
        path.append(curr)
        curr = routers[curr]["routing_table"][dest["id"]][0][0]

    path.append(dest["id"])
    
    return path








########################################################################
####################### Program execution #############################
########################################################################

represent_network(network=network)

# create the routing tables
setup_routing_tables(routers=routers)

# print out the routing tables

print("Routing tables: ")
for router in routers: 
    print("\tRouter: ", router["id"]+1)

    for nieghbor_id,hops in router["routing_table"].items(): 
        entry=""
        entry += "\t"+ str(nieghbor_id+1) + ":"

        # sort by cost
        hops.sort(key=lambda x:x[1])
        
        # print the best route
        entry +=" "+str(hops[0][0]+1)


        print(entry)

# calculate path from router 1 to 6 
path = find_best_route(routers=routers, src=routers[0], dest=routers[-1])
print("Path from router 1 to 6:")
path_as_str = ""
for point in path: 
    path_as_str += "-> "+ str(point+1)

print(path_as_str)
    
# create the list of the path steps 
steps:list[(int,int)] = []
for i in range(len(path)-1):
    steps.append((path[i], path[i+1]))



# generate a new file highlighting that path
represent_network(network=network, tohighlight=steps)



