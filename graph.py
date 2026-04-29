def distance(x1,y1,x2,y2):
    return ((x1-x2)**2+(y1-y2)**2)**0.5
class Node:
    def __init__(self,id,x,y):
        self.id=id
        self.x=x
        self.y=y
        self.next=None
    def add_next(self,next):
        self.next=next
    def __str__(self):
        return f"id:{self.id} x:{self.x} y:{self.y}, next:{self.next.id if self.next else None}"
class Graph:
    def __init__(self):
        self.nodes=[]
        self.init_nodes()
        self.init_edges()
        # for node in self.nodes:
        #     print(node)
    def init_nodes(self):
        file=[i.strip() for i in open('graph.txt','r')]
        # print(file)
        startline=7
        i=startline
        while file[i][0]!="]":
            self.add_node(file,i)
            i+=6
    def add_node(self,file,line):
        id=int(file[line+1].split()[1][:-1])
        x=float(file[line+3].split()[1][:-1])
        y=float(file[line+4].split()[1])
        node=Node(id,x,y)
        self.nodes.append(node)
    def get_start_edge(self):
        file=[i.strip().split() for i in open('graph.txt','r')]
        for i in range(len(file)):
            if file[i][0]=='"edges":':
                return i+1
    def init_edges(self):
        file=[i.strip() for i in open('graph.txt','r')]
        startline=self.get_start_edge()
        i=startline
        print(i)
        while file[i][0]!="]":
            self.add_edge(file,i)
            i+=6

    def add_edge(self,file,i):
        id1=int(file[i+1].split()[1][:-1])
        id2=int(file[i+2].split()[1][:-1])
        self.nodes[id1].add_next(self.nodes[id2])
    def find_closest_to(self,x,y):
        closest=None
        closest_dist=None
        for node in self.nodes:
            if node.next is None:
                continue
            dist=distance(x,y,node.x,node.y)
            if closest_dist is None or dist<closest_dist:
                closest=node
                closest_dist=dist
        return closest
