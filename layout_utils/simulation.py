from dataclasses import dataclass
from abc import ABC, abstractmethod
import heapq
from queue import PriorityQueue
from typing import List, Mapping, Literal
import datetime
import networkx as nx
from layout_utils.layout import Layout
import os

def aisle_to_sku(order, system: Layout):
    aisle_sku_mapping = {}

    for sku in order:
        loc = system.nodes_list[system.storage_assignment[sku]] 
        aisle = system.access_mapping[loc]["aisle"]
        if aisle not in aisle_sku_mapping.keys():
            aisle_sku_mapping[aisle] = []
        aisle_sku_mapping[aisle].append(sku)
    return aisle_sku_mapping

def aisle_order(aisle_sku_mapping: dict, system: Layout, source: tuple[Literal, Literal, Literal]):
    aisle_queue = []
    for aisle_idx in aisle_sku_mapping.keys():
        aisle_start = system.aisles_start_end[aisle_idx]["start"]
        dist = system.dist_mat[system.nodes_list.index(source)][system.nodes_list.index(aisle_start)]
        pos = (dist, aisle_idx)
        heapq.heappush(aisle_queue, pos)
    return aisle_queue
    


def stichgang(order, system: Layout):
    order_queue = []
    for sku in order:
        loc = system.nodes_list[system.storage_assignment[sku]] 
        aisle = system.access_mapping[loc]["aisle"]
        access = system.access_mapping[loc]["access"]
        pos = (aisle, access[0], loc, access, sku) 
        heapq.heappush(order_queue, pos)
    
    ordered = []
    for pos in range(len(order_queue)):
        ordered.append(heapq.heappop(order_queue)[4])

    return ordered

def stichgang1(order, system: Layout, start: tuple[Literal, Literal, Literal]):
    source = start
    aisle_sku_mapping = aisle_to_sku(order, system)
    distance = 0
    zugriff = 0
    route = []
    line = []
    route.append(source)

    aisle_queue = aisle_order(aisle_sku_mapping, system, start)
    
    if source[0] == 0:
        at_start = True
    else:
        at_start = False

    for a in range(len(aisle_queue)):
        if at_start == True:
            begin = "start"
        else:
            begin = "end"
        aisle = heapq.heappop(aisle_queue)[1]
        distance += system.dist_mat[system.nodes_list.index(source)][system.nodes_list.index(system.aisles_start_end[aisle][begin])]
        source = system.aisles_start_end[aisle][begin]
        route.append(source)
        line.append(source)
        order_queue = []
        #build orderd Order for current aisle
        for sku in aisle_sku_mapping[aisle]:
            loc = system.nodes_list[system.storage_assignment[sku]] 
            aisle = system.access_mapping[loc]["aisle"]
            access = system.access_mapping[loc]["access"]
            pos = (aisle, access[0], loc, access, sku) 
            heapq.heappush(order_queue, pos)
        
        ordered = []
        for pos in range(len(order_queue)):
            ordered.append(heapq.heappop(order_queue)[4])
        
        if begin == "start":
            for sku in ordered:
                loc = system.nodes_list[system.storage_assignment[sku]] 
                access = system.access_mapping[loc]["access"]
                distance += system.dist_mat[system.nodes_list.index(source)][system.nodes_list.index(access)]
                zugriff += system.dist_mat[system.nodes_list.index(access)][system.nodes_list.index(loc)]
                source = access
                route.append(source)
                line.append(source)
                route.append(loc)
                route.append(source)

            distance += system.dist_mat[system.nodes_list.index(source)][system.nodes_list.index(system.aisles_start_end[aisle]["start"])]
            source = system.aisles_start_end[aisle]["start"] 
            route.append(source)
            line.append(source)

        
        if begin == "end":
            ordered.reverse()
            for sku in ordered:
                loc = system.nodes_list[system.storage_assignment[sku]] 
                access = system.access_mapping[loc]["access"]
                distance += system.dist_mat[system.nodes_list.index(source)][system.nodes_list.index(access)]
                zugriff += system.dist_mat[system.nodes_list.index(access)][system.nodes_list.index(loc)]
                source = access
                route.append(source)
                line.append(source)
                route.append(loc)
                route.append(source)

            distance += system.dist_mat[system.nodes_list.index(source)][system.nodes_list.index(system.aisles_start_end[aisle]["end"])]
            source = system.aisles_start_end[aisle]["end"] 
            route.append(source)
            line.append(source)

    distance += system.dist_mat[system.nodes_list.index(source)][system.nodes_list.index(start)]
    source = start
    route.append(source)     
    line.append(source)   
    return route, line, distance, zugriff

def s_shape(order, system: Layout, start: tuple[Literal, Literal, Literal]):
    source = start
    aisle_sku_mapping = {}
    distance = 0
    zugriff = 0
    route = []
    line = []
    route.append(source)
    line.append(source)


    for sku in order:
        loc = system.nodes_list[system.storage_assignment[sku]] 
        aisle = system.access_mapping[loc]["aisle"]
        if aisle not in aisle_sku_mapping.keys():
            aisle_sku_mapping[aisle] = []
        aisle_sku_mapping[aisle].append(sku)

    aisle_queue = []
    for aisle_idx in aisle_sku_mapping.keys():
        aisle_start = system.aisles_start_end[aisle_idx]["start"]
        dist = system.dist_mat[system.nodes_list.index(source)][system.nodes_list.index(aisle_start)]
        pos = (dist, aisle_idx)
        heapq.heappush(aisle_queue, pos)
    at_start = True

    for a in range(len(aisle_queue)):
        if at_start == True:
            begin = "start"
        else:
            begin = "end"
        aisle = heapq.heappop(aisle_queue)[1]
        distance += system.dist_mat[system.nodes_list.index(source)][system.nodes_list.index(system.aisles_start_end[aisle][begin])]
        source = system.aisles_start_end[aisle][begin]
        route.append(source)
        line.append(source)
        order_queue = []
        #build orderd Order for current aisle
        for sku in aisle_sku_mapping[aisle]:
            loc = system.nodes_list[system.storage_assignment[sku]] 
            aisle = system.access_mapping[loc]["aisle"]
            access = system.access_mapping[loc]["access"]
            pos = (aisle, access[0], loc, access, sku) 
            heapq.heappush(order_queue, pos)
        
        ordered = []
        for pos in range(len(order_queue)):
            ordered.append(heapq.heappop(order_queue)[4])
        
        if begin == "start":
            for sku in ordered:
                loc = system.nodes_list[system.storage_assignment[sku]] 
                access = system.access_mapping[loc]["access"]
                distance += system.dist_mat[system.nodes_list.index(source)][system.nodes_list.index(access)]
                zugriff += system.dist_mat[system.nodes_list.index(access)][system.nodes_list.index(loc)]
                source = access
                route.append(source)
                line.append(source)
                route.append(loc)
                route.append(source)
            distance += system.dist_mat[system.nodes_list.index(source)][system.nodes_list.index(system.aisles_start_end[aisle]["end"])]
            source = system.aisles_start_end[aisle]["end"] 
            route.append(source)
            line.append(source)

        
        if begin == "end":
            ordered.reverse()
            for sku in ordered:
                loc = system.nodes_list[system.storage_assignment[sku]] 
                access = system.access_mapping[loc]["access"]
                distance += system.dist_mat[system.nodes_list.index(source)][system.nodes_list.index(access)]
                zugriff += system.dist_mat[system.nodes_list.index(access)][system.nodes_list.index(loc)]
                source = access
                route.append(source)
                line.append(source)
                route.append(loc)
                route.append(source)
                

            distance += system.dist_mat[system.nodes_list.index(source)][system.nodes_list.index(system.aisles_start_end[aisle]["start"])]
            source = system.aisles_start_end[aisle]["start"] 
            route.append(source)
            line.append(source)


        if at_start == True:
            at_start = False
        else:
            at_start = True

    distance += system.dist_mat[system.nodes_list.index(source)][system.nodes_list.index(start)]
    source = start
    route.append(source)    
    line.append(source)    
    return route, line, distance, zugriff

def sim_loop(routing: str, orders, warehouse: Layout, start: tuple[Literal, Literal, Literal]):
    if routing == "stichgang":
        route = []
        orders_sim = []
        for order in orders:
            order_s_shaped = stichgang(order, warehouse)
            orders_sim.append(order_s_shaped)

        distance = 0
        for order in orders_sim:
            source = start
            route.append(source) 

            for sku in order:
                loc = warehouse.nodes_list[warehouse.storage_assignment[sku]] 
                distance += warehouse.dist_mat[warehouse.nodes_list.index(source)][warehouse.nodes_list.index(loc)]
                source = loc
            distance += warehouse.dist_mat[warehouse.nodes_list.index(source)][warehouse.nodes_list.index(start)]
        
        return distance
    
    if routing == "s_shape":
        route = []
        line = []
        distance = 0
        zugriff = 0
        for order in orders:
            route_order, line_order, distance_order, zugriff_order = s_shape(order, warehouse, start)
            route.append(route_order)
            line.append(line_order)
            distance += distance_order
            zugriff += zugriff_order
        return route, line, distance, zugriff

    if routing == "stichgang1":
        route = []
        line = []
        distance = 0
        zugriff = 0
        for order in orders:
            route_order, line_order, distance_order, zugriff_order = stichgang1(order, warehouse, start)
            route.append(route_order)
            line.append(line_order)
            distance += distance_order
            zugriff += zugriff_order
        return route, line, distance, zugriff


@dataclass
class Order:
    order_id: str
    start_time: datetime.datetime
    sku: str
    
class Agent:
    def __init__(self, speed, capacity):
        self.speed = speed
        self.capacity = capacity
        self.curr_load = 0
        self.occupied = False
        self.location = (0, 0, 0)
        self.distance_traveled = 0
        self.time_retrival = 0
    
    def load(self):
        self.curr_load +=1
    
    def unload(self):
        self.curr_load -= 1

    def block(self):
        self.occupied = True

    def unblock(self):
        self.occupied = False
    
    def change_loc(self):
        pass

    def reset(self):
        self.curr_load = 0
        self.occupied = False
        self.location = (0,0,0)

class EventList():
    def __init__(self) -> None:
        self.event_list: List = []
    
    def add_event(self, event):
        heapq.heappush(self.event_list, event)
    
    def next_event_time(self):
        next_event = self.event_list[0]
        return next_event.time
    
    def reset(self):
        self.event_list = []
    
    def pop_event(self):
        next_event = heapq.heappop(self.event_list)
        return next_event

    def is_empty(self):
        if len(self.event_list) == 0:
            return True
        else:
            return False



class Event():
    def __init__(self, time: datetime.datetime) -> None:
        self.time = time

    def __lt__(self, other):
        return self.time < other.time

    def __le__(self, other):
        return not (other < self)

    def __gt__(self, other):
        return self.time > other.time
    
    def __ge__(self, other):
        return not (self < other)
    
    def handle_event(self): 
        pass

class PickEvent(Event):
    def __init__(self, time, order: Order, target, agent_id) -> None:
        Event.__init__(self, time)
        self._order = order
        self.target = target
        self.agent_id = agent_id
    
    def handle_event(self, system: Layout, agents):
        pass

class TravelEvent(Event):
    def __init__(self, time, order: Order, agent_id) -> None:
        Event.__init__(self, time)
        self._order = order
        self.agent_id = agent_id
    
    def handle_event(self, system: Layout, agents):
        source = agents[self.agent_id].location
        # print("sku: ", self._order.sku[-1])
        loc = system.nodes_list[system.storage_assignment[self._order.sku.pop(0)]] 
        target = system.access_mapping[loc]["access"]
        #target = system.nodes_list[system.storage_assignment[self._order.sku.pop(0)]]
        # target = system.storage_locs[self._order.sku.pop()]
        # print(f"Agent {self.agent_id} Traveling from {source} to {target}")
        system.nodes_list.index(source)
        system.nodes_list.index(target)
        distance = system.dist_mat[system.nodes_list.index(source)][system.nodes_list.index(target)]
        travel_duration = distance
        completed_time = self.time + datetime.timedelta(minutes=travel_duration)
        agents[self.agent_id].distance_traveled += distance
        return [TravelCompletedEvent(completed_time, self._order, target, loc, self.agent_id)]


# class TravelCompletedEvent(Event):
#     def __init__(self, time, order: Order, target, loc, agent_id) -> None:
#         Event.__init__(self, time)
#         self._order = order
#         self.target = target
#         self.loc = loc
#         self.agent_id = agent_id
    
#     def handle_event(self, system: Layout, agents):
#         print(f"Agent {self.agent_id} arrived at {self.target}")
#         agents[self.agent_id].location = self.target
#         if len(self._order.sku) > 0:
#             return [TravelEvent(self.time, self._order, self.agent_id)]
#         else:
#             return [OrderFinishEvent(self.time, self._order, self.agent_id)]

class TravelCompletedEvent(Event):
    def __init__(self, time, order: Order, target, loc, agent_id) -> None:
        Event.__init__(self, time)
        self._order = order
        self.target = target
        self.loc = loc
        self.agent_id = agent_id
    
    def handle_event(self, system: Layout, agents):
        # print(f"Agent {self.agent_id} arrived at {self.target}")
        agents[self.agent_id].location = self.target
        return [SKURetrivalEvent(self.time, self._order, self.agent_id, self.loc)]

class SKURetrivalEvent(Event):
    def __init__(self, time, order: Order, agent_id, loc) -> None:
        Event.__init__(self, time)
        self._order = order
        self.loc = loc
        self.agent_id = agent_id
    
    def handle_event(self, system: Layout, agents):
        # print(f"Agent {self.agent_id} starts retrival at {self.loc}")
        # print(f"SKU is at level: {self.loc[2]}")
        retrival = 1 * self.loc[2]
        agents[self.agent_id].time_retrival += retrival

        if len(self._order.sku) > 0:
            return [TravelEvent(self.time + datetime.timedelta(minutes=retrival), self._order, self.agent_id)]
        else:
            return [OrderFinishEvent(self.time + datetime.timedelta(minutes=retrival), self._order, self.agent_id)]


class OrderPickEvent(Event):
    _order: Order
    def __init__(self, order: Order) -> None:
        Event.__init__(self, order.start_time)
        self._order = order
    
    def handle_event(self, system: Layout, agents):
        # print(f"Start {self._order.order_id}")

        for id, agent in enumerate(agents):
            
            # print(f"AGENT: {id} is {agent.occupied}")
            if agent.occupied == False:
                # print(f"Agent {id} available")
                agent.block()
                return [TravelEvent(self.time, self._order, id)]
            
        # print("Agent not available")
        self._order.start_time += datetime.timedelta(minutes=1)
        return [OrderPickEvent(self._order)]

class OrderFinishEvent(Event):
    _order: Order
    def __init__(self, time, order: Order, agent_id) -> None:
        Event.__init__(self, time)
        self._order = order
        self.agent_id = agent_id
    
    def handle_event(self, system: Layout, agents):
        source = agents[self.agent_id].location
        distance = system.dist_mat[system.nodes_list.index(source)][system.nodes_list.index((0,0,0))]
        agents[self.agent_id].distance_traveled += distance
        agents[self.agent_id].reset()
        return []
    

def run_simulation(initial_events: list[Event], system: Layout, agent: Agent):
    event_list = EventList()
    for event in initial_events:
        event_list.add_event(event)
    
    while not event_list.is_empty():
        event = event_list.pop_event()
        # print("Time: ", event.time)
        new_events = event.handle_event(system, agent)
        for new_event in new_events:
            event_list.add_event(new_event)