import sys; args = sys.argv[1:]
import re, math

def grfParse(lstArgs):
    size, width, rwd, graph_type = 0, 0, 12, ""
    for i,arg in enumerate(lstArgs):
        if arg[0] == 'G':
            match = re.search("G(G|N)?(\d+)(W\d+)?(R\d+)?", arg, re.I)
            if match.group(1) != None: graph_type = match.group(1)
            else: graph_type = 'G'
            size = int(match.group(2))
            if match.group(3) != None: 
                # what if list is empty
                width = int(match.group(3)[1:])
            else:
                possible_width = [x for x in range(math.ceil(math.sqrt(size)), size) if size % x == 0]
                if len(possible_width) == 0: width = size
                else: width = possible_width[0]
            if match.group(4) != None: rwd = int(match.group(4)[1:])
            

            edges = []
            if width != 0 and graph_type == 'G':
                for i in range(size):
                    edges.append(nativeEdges(i, size, width))
            props = {'rwd': rwd, 'vprops': [{} for n in range(size)], 'eprops': {}}

            graph = {'type': graph_type, 'size': size, 'width': width, 'rwd': rwd, 'edges': edges, 'props': props}
        if arg[0] == 'V':
            match = re.search("V((-?\d|,|:|#)+)(.*)", arg, re.I)
            if match: 
                vertices = set(parseVSlices(match.group(1), graph))
                opers = match.group(3)
            else: 
                vertices = set()
                opers = ""
            opes = processOps(opers, graph)
            
            for op in opes:
                if op == 'B':
                    for vertex in vertices:
                        edges = graph['edges'][vertex][:]
                        for edge in set(nativeEdges(vertex, graph['size'], graph['width']) + edges):
                            edgeEdges = graph['edges'][edge]
                            if edge not in edges and edge not in vertices:
                                graph['edges'][vertex].append(edge)
                            elif edge not in vertices:
                                graph['edges'][vertex].remove(edge)
                            if vertex not in edgeEdges and edge not in vertices and vertex in nativeEdges(edge, graph['size'], graph['width']):
                                graph['edges'][edge].append(vertex)
                            elif edge not in vertices and vertex in graph['edges'][edge]:
                                graph['edges'][edge].remove(vertex)
                        for possibleEdge in range(graph['size']):
                            if possibleEdge in set(nativeEdges(vertex, graph['size'], graph['width']) + edges): continue
                            if vertex in graph['edges'][possibleEdge]:
                                graph['edges'][possibleEdge].remove(vertex)
                        #natives = 
                        #for n in natives: # adding natives
                        #    if n not in graph['edges'][vertex]:
                        #        graph['edges'][vertex].append(n)
                        #for n in graph['edges'][vertex][:]: # removing
                        #    if n not in vertices and vertex in graph['edges'][n] and n in graph['edges'][vertex]: 
                        #      graph['edges'][n].remove(vertex)
                        #        graph['edges'][vertex].remove(n)
                if 'R' in op:
                    num = op[op.index('R')+1:]
                    if num: num = int(num)
                    else: num = graph['rwd']
                    if '-' in op[:op.index('R')]: num = 0
                    for vertex in vertices:
                        graph['props']['vprops'][vertex] = {'rwd': num}
        if arg[0] == 'E':
            match = re.search("E([!+*~@])?((-?\d|,|:|#)+)([=~])((-?\d|,|:|#)+)(.*)", arg, re.I)
            if not match: # check form 2
                match = re.search("E([!+*~@])?((-?\d|,|:|#)+)([NSEW]+)([=~])(.*)", arg, re.I)
                option = '~' if not match.group(1) else match.group(1)
                vertices = parseVSlices(match.group(2), graph)
                direction = match.group(5)
                opers = match.group(6)
                directions = match.group(4)
                edges = set()
                width = graph['width']
                for v in vertices:
                    for d in directions:
                        if d == 'N' and v - width >= 0 and ((v-width, v) not in edges or direction == '~'):
                            edges.add((v, v-width))
                        elif d == 'S' and v + width < graph['size'] and ((v+width, v) not in edges or direction == '~'):
                            edges.add((v, v+width))
                        elif d == 'E' and (v + 1) % width != 0 and ((v+1, v) not in edges or direction == '~'):
                            edges.add((v, v+1))
                        elif d == 'W' and v % width != 0 and ((v-1, v) not in edges or direction == '~'):
                            edges.add((v, v-1))
            else:
                option = '~' if not match.group(1) else match.group(1)
                vertices1 = parseVSlices(match.group(2), graph)
                direction = match.group(4)
                vertices2 = parseVSlices(match.group(5), graph)
                opers = match.group(7)
                edges = set() #set(zip(vertices1, vertices2))
                for i in range(len(vertices1)):
                    if (vertices2[i], vertices1[i]) not in edges or direction == '~': edges.add((vertices1[i], vertices2[i]))
            ops = processOps(opers, graph)
            rwd = ops[2]
            if rwd != 'no':
                rwd = 12 if rwd[-1] == 'R' else int(rwd[rwd.index('R')+1:])
            else: rwd = None
            terminal = ops[1]
            for edge in edges:
                if option == '!': # remove extant edges
                    if edge[1] in graph['edges'][edge[0]]: 
                        graph['edges'][edge[0]].remove(edge[1])
                    if edge[0] in graph['edges'][edge[1]] and direction == '=': graph['edges'][edge[1]].remove(edge[0])
                elif option == '+': # add new with props, skip extant edges
                    if edge[1] not in graph['edges'][edge[0]]:
                        graph['edges'][edge[0]].append(edge[1])
                        if rwd != None: graph['props']['eprops'][edge] = {'rwd': rwd}
                    if edge[0] not in graph['edges'][edge[1]] and direction == '=':
                        graph['edges'][edge[1]].append(edge[0])
                        if rwd != None: graph['props']['eprops'][(edge[1], edge[0])] = {'rwd': rwd} # might need this to be flipped
                elif option == '*': # add if missing, apply props to both new and previously extant
                    if edge[1] not in graph['edges'][edge[0]]: graph['edges'][edge[0]].append(edge[1])
                    if edge[0] not in graph['edges'][edge[1]] and direction == '=': graph['edges'][edge[1]].append(edge[0])
                    if rwd != None: graph['props']['eprops'][edge] = {'rwd': rwd}
                    if rwd != None and direction == '=': graph['props']['eprops'][(edge[1], edge[0])] = {'rwd': rwd}
                elif option == '~':
                    if edge[1] in graph['edges'][edge[0]]: graph['edges'][edge[0]].remove(edge[1]) # maybe need to remove props from deleted edges?
                    else: 
                        if rwd != None: graph['props']['eprops'][edge] = {'rwd': rwd}
                        graph['edges'][edge[0]].append(edge[1])
                    if direction == '=' and edge[0] != edge[1]:
                        if edge[0] in graph['edges'][edge[1]]: graph['edges'][edge[1]].remove(edge[0])
                        else: 
                            if rwd != None: graph['props']['eprops'][(edge[1], edge[0])] = {'rwd': rwd}
                            graph['edges'][edge[1]].append(edge[0])
                
                elif option == '@': # apply props to extants
                    if rwd != None and edge[1] in graph['edges'][edge[0]]: graph['props']['eprops'][edge] = {'rwd': rwd}
                    if rwd != None and edge[0] in graph['edges'][edge[1]] and direction == '=': graph['props']['eprops'][(edge[1], edge[0])] = {'rwd': rwd}
    return graph

def parseVSlices(strSlices, graph):
    indices = [i for i in range(graph['size'])]
    vertices = []
    vslcs = strSlices.split(",")
    for slic in vslcs:
        if not '#' in slic:
            parts = slic.split(':')
            if len(parts) == 1:
                vertices.append(int(parts[0]))
            elif len(parts) == 2:
                for i in indices[0 if not parts[0] else int(parts[0]):graph['size'] if not parts[1] else int(parts[1])]:
                    vertices.append(i)
            elif len(parts) == 3:
                step = 1 if not parts[2] else int(parts[2])
                for i in indices[(graph['size']-1 if step < 0 else 0) if not parts[0] else int(parts[0]):(0 if step < 0 else graph['size']) if not parts[1] else int(parts[1]):step]:
                    vertices.append(i)
                if (not parts[1]) and (step < 0) and ((graph['size'] - 1 if not parts[0] else int(parts[0])) % step) == 0: # issue here with ordering?
                    vertices.append(indices[0]) # correct issue on second block
        else:
            start = 0 if slic[0] == '#' else int(slic[:slic.index('#')])
            end = graph['size']-1 if slic[-1] == '#' else int(slic[slic.index('#')+1:])
            for x in range((end%graph['width'])-(start%graph['width'])+1):
                for y in range((end//graph['width'])-(start//graph['width'])+1):
                    vertices.append(start+x+y*graph['width'])
    vertices = [n if n>= 0 else graph['size']+n for n in vertices]
    return vertices
            
def processOps(opers, graph):
    ops = []
    for i,char in enumerate(opers):
        if char == 'B': ops.append('B')
        elif char == 'T': ops.append('T')
        elif char == 'R':
            oop = ""
            if opers[i-1] == '-': oop += '-'
            oop += 'R'
            for c in opers[i+1:]:
                if c in "0123456789": oop += c
                else: break
            ops.append(oop)
    b = None
    t = None
    r = None
    for i in range(len(ops)):
        if 'B' in ops[i]:
            b = i
        if 'T' in ops[i]:
            t = i
        if 'R' in ops[i]:
            r = i
    opes = ['no' if b == None else ops[b], 'no' if t == None else ops[t], 'no' if r == None else ops[r]]
    return opes

def nativeEdges(vertex, size, width):
    edges = []
    if vertex % width != 0: # left
        edges.append(vertex-1)
    if vertex % width != width-1: # right
        edges.append(vertex+1)
    if vertex + width < size: # bottom
        edges.append(vertex+width)
    if vertex - width >= 0: # top
        edges.append(vertex-width)
    return edges


def grfSize(graph):
    return graph['size']

def grfNbrs(graph, v):
    if v < len(graph['edges']):
        return graph['edges'][v]
    return []

def grfGProps(graph):
    return {k: graph[k] for k in ({'width', 'rwd'} if graph['type'] != 'N' else {'rwd'})}

def grfVProps(graph, v):
    return graph['props']['vprops'][v]

def grfEProps(graph, v1, v2):
    if (v1, v2) in graph['props']['eprops'] and v2 in graph['edges'][v1]: # maybe note that edge props still exist tho
        return graph['props']['eprops'][(v1, v2)]
    else: return {}

def grfStrEdges(graph):
    if graph['width'] == 0 or len(graph['edges'])==0: return ""
    symbols = {1100:'J',100:'N',1110:'^',110:'L',1101:'<',1000:'W',1111:'+',10:'E',111:'>',1001:'7',1:'S',1011:'v',11:'r',1010:'-',101:'|',0:'.'} # south add 1, east add 10, north add 100, west add 1000
    # south add 1, east add 10, north add 100, west add 1000
    ret = ""
    for v in range(graph['size']):
        if not v < len(graph['edges']):
            ret += '.'
            continue
        edges = graph['edges'][v]
        val = 0
        for edge in edges: # maybe have to watch for edge cases of jump edges wrapping around
            if edge == v + 1 and edge % graph['width'] != 0: # east
                val += 10
            elif edge == v - 1 and v % graph['width'] != 0: # west
                val += 1000
            elif edge == v + graph['width'] and v + graph['width'] < graph['size']: # south
                val += 1
            elif edge == v - graph['width'] and v - graph['width'] >= 0: # north
                val += 100
        ret += symbols[val]
    # jumps
    jumps = []
    for v in range(graph['size']):
        for n in graph['edges'][v]:
            if n not in {v+1 if (v+1)%graph['width'] != 0 else -1, v-1 if v%graph['width'] != 0 else -1, v+graph['width'] if v+graph['width'] < graph['size'] else -1, v-graph['width'] if v-graph['width'] >= 0 else -1}:
                jumps.append((v, n))
    if jumps: 
        ret += "\nJumps: "
        jumps2 = []
        for j in jumps:
            if (j[1], j[0]) in [(ju[0], ju[1]) for ju in jumps2]: continue
            if (j[1], j[0]) in jumps and j[0] != j[1]: 
                jumps2.append((j[0], j[1], '='))
            else: jumps2.append((j[0], j[1], '~'))
        for j in jumps2:
            ret += str(j[0]) + j[2] + str(j[1]) + ";"
        ret = ret[:-1]
    return ret


def grfStrProps(graph):
    ret = ""
    gProps = grfGProps(graph)
    for item in gProps:
        ret += item + ": " + str(gProps[item]) + ", "
    if ret[-2] == ',': ret = ret[:-2]
    ret += "\n"
    rwds = set()
    for vert in range(graph['size']):
        vprops = grfVProps(graph, vert)
        if vprops and 'rwd' in vprops:
            rwds.add(vprops['rwd'])
    for rwd in rwds:
        vertices = []
        for vert in range(graph['size']):
            vprops = grfVProps(graph, vert)
            if not vprops or not 'rwd' in vprops: continue
            if vprops['rwd'] == rwd: vertices.append(str(vert))
        ret += ", ".join(vertices) + ": rwd: " + str(rwd) + "\n"
    rwds = set()
    for edge in graph['props']['eprops']:
        eProps = grfEProps(graph, edge[0], edge[1])
        if 'rwd' not in eProps: continue
        rwds.add(eProps['rwd'])
    for rwd in rwds:
        edges = []
        for edge in graph['props']['eprops']:
            eProps = grfEProps(graph, edge[0], edge[1])
            if 'rwd' not in eProps: continue
            if eProps['rwd'] == rwd: edges.append(str(edge))
        ret += ", ".join(edges) + ": rwd: " + str(rwd) + "\n"


    if ret[-2] == ',': ret = ret[:-2]
    return ret

def policy(graph):
    ret = "Policy: \n"
    jumps = ""
    for v in range(graph['size']):
        if v % graph['width'] == 0: ret += "\n"
        policy = single_policy(graph, v)
        if "JUMP" in policy:
            ret += policy[0]
            jumps += str(v) + "~" + str(policy[5:]) + ";"
        else:
            ret += policy
    ret += "\nJumps: " + jumps
    return ret

def single_policy(graph, vertex):
    if 'rwd' in graph['props']['vprops'][vertex]:
        return "*"
    gSize = graph['size']
    gWidth = graph['width']
    dirs = graph['edges'][vertex][:]
    costs = []
    for d in dirs:
        if (vertex, d) in graph['props']['eprops'] and 'rwd' in graph['props']['eprops'][(vertex, d)]:
            costs.append(1)
        else:
            costs.append(BFS(graph, d))
            
    j = 0
    while j < len(costs):
        if costs[j] == None:
            costs.pop(j)
            dirs.pop(j)
            j -= 1
        j += 1
        
    symbols = {1100:'J',100:'N',1110:'^',110:'L',1101:'<',1000:'W',1111:'+',10:'E',111:'>',1001:'7',1:'S',1011:'v',11:'r',1010:'-',101:'|',0:'.'} # south add 1, east add 10, north add 100, west add 1000
    # south add 1, east add 10, north add 100, west add 1000
    val = 0
    jump = ""
    for i in range(len(costs)):
        c = costs[i]
        v = dirs[i]
        if c == min(costs):
            if v == vertex+1 and (vertex+1) % gWidth != 0: val += 10
            elif v == vertex-1 and vertex % gWidth != 0: val += 1000
            elif v == vertex+gWidth: val += 1
            elif v == vertex-gWidth: val += 100
            else:
                jump += "JUMP" + str(v)
    return symbols[val] + jump

def BFS(graph, start):
    seen, queue = set(), [(start, 1)]
    while queue:
        info = queue.pop(0)
        v = info[0]
        if v in seen: continue
        seen.add(v)
        if 'rwd' in graph['props']['vprops'][v]: 
            return info[1]
        for v2 in graph['edges'][v]:
            if 'rwd' in graph['props']['vprops'][v2]:
                return info[1] + 1
            if ((v, v2) in graph['props']['eprops'] and 'rwd' in graph['props']['eprops'][(v, v2)]):
                return info[1] + 1
        queue.extend([(v, info[1]+1) for v in graph['edges'][v]])
    return None

def main():
    graph = grfParse(args)
    #edgesStr = grfStrEdges(graph)
    #propsStr = grfStrProps(graph)
    # output edges str
    #for i in range(len(edgesStr)):
    #    if i % graph['width'] == 0 and i != 0:
    #        print()
    #    print(edgesStr[i], end="")
    #    if i == graph['size']-1: 
    #        print(edgesStr[graph['size']:])
    #        break
    #print()
    #print(propsStr)
    print(policy(graph))

if __name__ == '__main__': main()

# Elliott Rosenberg, Period 5, 2027