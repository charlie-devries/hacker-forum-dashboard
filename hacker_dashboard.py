from ast import Continue
from re import L
from turtle import up
import streamlit as st
# import streamlit.components.v1 as components
import networkx as nx
import pickle
from streamlit_agraph import agraph, Node, Edge, Config
import numpy as np
import random

st.title("Hacker Forum Inquiry")
st.write("The tool allows for the interactive investigation of hacker forum communities and members. Use the drop down menus to narrow your search.")
#cipher, antionline bad
select_forum_box = st.selectbox("Select forum to investigate:", ('cardingteam','antionline','exetools','wilderssecurity','cipher','go4expert'))
with open(select_forum_box+'_nx.pickle', 'rb') as f:
    G = pickle.load(f)
st.write("The " + select_forum_box + " forum contains", len(G.nodes),"unique members", 'and', len(G.edges), 'edges')


# function to take a graph and add a color attribute that correlates with the communities for each clustering method.
# this will stop the color of nodes from changing each time we refresh.
# remember to include the "no group" color
comm_nums = []
comm_colors = []
comm_count = []
comm_dict = G.nodes[list(G.nodes)[0]]
keys = [key for key in comm_dict.keys() if "community" in key]
print(keys)
for i in G.nodes:
    comm_dict = G.nodes[i]
    G.nodes[i]["size"] = np.log(G.degree(i)+1) * 20
    for key in keys:
        # st.write(comm_dict)
        color = ""
        try:
            if(comm_dict[key] not in comm_nums):
                comm_nums.append(comm_dict[key])
                color = "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])
                comm_colors.append(color)
                comm_count.append(1)
            else:
                color = comm_colors[comm_nums.index(comm_dict[key])]
                comm_count[comm_nums.index(comm_dict[key])] = comm_count[comm_nums.index(comm_dict[key])] + 1

        except:
            color = "#808080"

        G.nodes[i][key + '_color'] = color


# function to take the processed graph and turn it into an agraph
# this function will be called every time the filter changes
# should take the clustering method as a parameter
def generate_agraph(G, method):
    nodes = []
    edges = [Edge(source=i, target=j, type="STRAIGHT") for (i,j,n) in G.edges]
    for i in G.nodes:
        attr = G.nodes[i]
        nodes.append(Node(id=i, label=i, size=attr["size"], color=attr[method + "_color"]))
    
    config = Config(width=500, 
                height=500, 
                directed=True,
                nodeHighlightBehavior=True, 
                highlightColor="#F7A7A6",
                collapsible=True,
                node={'labelProperty':'label'},
                link={'labelProperty': 'label', 'renderLabel': True}
                ) 

    return_value = agraph(nodes=nodes, 
                        edges=edges, 
                        config=config)


# FILTER 1
# select from a dropdown of community detection methods
# this will call the generate_agraph function
print(G.graph)
select_cd_method_box = st.selectbox("Select community detection method: ", keys, format_func= lambda x: x.replace("community_","").replace("_community", "").replace("_", " "))
print('TEST',G.graph.keys())
print(select_cd_method_box.replace("_community","" + "_coverage_coverage") in G.graph.keys())
st.markdown("*Modularity* is a leading metric to determine the quality of community structure.  A score near 1 indicates more separate, distinct communities, and a score near 0 indicates little separtion of members into communities.")
st.markdown("The *coverage* of a partition is the ratio of the number of intra-community edges to the total number of edges in the graph.")
st.write("Using the "+ select_cd_method_box.replace("community_","").replace("_community", "").replace("_", " ") +" algorithm, modularity =",
 round(G.graph[select_cd_method_box.replace("_community","")],4), 'and coverage = ', round(G.graph[select_cd_method_box.replace("_community","") + "_coverage_coverage"],4))


generate_agraph(G, select_cd_method_box)
# FILTER 2
#gets unique clusters for a given clustering.
# this will take the processed graph, get all unique communities for a given CD method along with the counts
# this will return a filtered nx graph
# the nx graph will be plotted as an agraph, and a new filter will show up if the selection != ""
comm_dict = dict()
for i in G.nodes:
    color = G.nodes[i][select_cd_method_box + "_color"]
    if color not in comm_dict.keys():
        comm_dict[color] = 1
    else:
        comm_dict[color] = comm_dict[color] + 1

options = []
cnt = 1
for i in comm_dict:
    options.append("Community " + str(cnt) + ": " + str(comm_dict[i]) + " members")
    cnt += 1



select_cluster_box = int(st.selectbox("Select a community:", options)[10:11])
cnt = 1
for i in comm_dict:
    if select_cluster_box == cnt:
        select_cluster_box = i
    cnt +=1
print(select_cluster_box)
filt_G = G.copy()

# creates a copy of the nx graph and filters out all other nodes
for i in G.nodes:
    if(select_cluster_box != ""):
        color = filt_G.nodes[i][select_cd_method_box + "_color"]

        comm_dict = filt_G.nodes[i]
        try:
            if(color != select_cluster_box):
                filt_G.remove_node(i)
            
        except:
            filt_G.remove_node(i)


generate_agraph(filt_G, select_cd_method_box)

# FILTER 3
# This new filter has all the members of the graph.  The options are filt_graph.nodes
# if the selection != "", a new filter will show up
member_filter_box = st.selectbox("select a community member:", list(filt_G.nodes))

# FILTER 4
# Will loop thru all the edges and determine all unique edge titles where the source was the selected user
# if the selection !="" a new filter will show up
print("edge data")
titles = set()
for i in G.edges:
    try:
        if(i[0] == member_filter_box):
            edge_data = G.get_edge_data(i[0], i[1])
            for key in edge_data:
                # print(edge_data[key]['threadTitle'])
                titles.add(edge_data[key]['threadTitle'])

    except:
        print("error")
        print(G.get_edge_data(i[0], i[1]))
title_filter_box = st.selectbox("select a thread of interest:", titles)

# FILTER 5
thread_dict = dict()
for i in G.edges:
    try:
        if(i[0] == member_filter_box):
            edge_data = G.get_edge_data(i[0], i[1])
            for key in edge_data:
                thread = edge_data[key]['threadTitle']
                if(thread == title_filter_box):
                    content = edge_data[key]['postContent']
                    date = edge_data[key]['postDate']
                    if(thread not in thread_dict.keys()):
                        thread_dict[thread] = [(content, date)]
                    else:
                        thread_dict[thread].append((content, date))
    except:
        pass

for thread in thread_dict:
    st.markdown("#### {}".format(thread))
    for post in thread_dict[thread]:
        content, date = post
        st.markdown("*posted by {0} on {1}*".format(member_filter_box, date))
        st.markdown(content)
        st.markdown("---")


