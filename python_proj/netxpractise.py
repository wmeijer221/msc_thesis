import networkx as nx
# from dataclasses import dataclass
# from enum import Enum


# class ActivityTypes(Enum):
#     PULL_REQUEST = 1
#     ISSUE = 2


# class ParticipantType(Enum):
#     SUBMITTER = 1
#     INTEGRATOR = 2
#     COMMENTER = 3


# @dataclass(frozen=True)
# class EventParticipant:
#     user_id: int
#     participant_type: ParticipantType


# @dataclass(frozen=True)
# class EventEntry:
#     activity_type: ActivityTypes
#     project_id: str
#     activity_id: int
#     user_a: EventParticipant
#     user_b: EventParticipant


# G = nx.Graph()

# user_a = EventParticipant(0, ParticipantType.COMMENTER)
# user_b = EventParticipant(123, ParticipantType.SUBMITTER)
# event = EventEntry(ActivityTypes.PULL_REQUEST, 123, 15155, user_a, user_b)
# entry = (0, event)

# G.add_node(entry)

# user_c = EventParticipant(30989, ParticipantType.INTEGRATOR)
# event_b = EventEntry(ActivityTypes.ISSUE, 123, 56546, user_a, user_c)
# entry_b = (1, event_b)

# G.add_node(entry)

# G.add_edge(0, 1)
# G.add_edge(1)

# print(G.edges)
# print(G.nodes)

# pr = nx.pagerank(G, alpha=0.9)
# print(pr)

import random

G = nx.Graph()

node_count = 100
for i in range(node_count):
    entry = (i, f"My name is {i}")
    G.add_node(entry)

edge_count = int(0.01 * node_count**2)
for i in range(edge_count):
    u = random.randint(0, node_count)
    v = random.randint(0, node_count)
    G.add_edge(u, v)

pr = nx.pagerank(G, 0.9)
print(max(pr.values()))
print(min(pr.values()))
