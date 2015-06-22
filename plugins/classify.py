#!/usr/bin/env python

__author__ = "Gabriel Bassett"
"""
 AUTHOR: {0}
 DATE: <DATE>
 DEPENDENCIES: <a list of modules requiring installation>
 Copyright <YEAR> {0}

 LICENSE:
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.

 DESCRIPTION:
 <ENTER DESCRIPTION>

""".format(__author__)
# PRE-USER SETUP
pass

########### NOT USER EDITABLE ABOVE THIS POINT #################


# USER VARIABLES
PLUGIN_CONFIG_FILE = "classify.yapsy-plugin"
NAME = "classify"


########### NOT USER EDITABLE BELOW THIS POINT #################


## IMPORTS
from yapsy.IPlugin import IPlugin
import logging
import networkx as nx
from datetime import datetime # timedelta imported above
import uuid
import ConfigParser
import inspect
try:
    import tldextract
    module_import_success = True
except:
    module_import_success = False
    logging.error("Module import failed.  Please install the following module: tldextract.")
    raise


## SETUP
loc = inspect.getfile(inspect.currentframe())
ind = loc.rfind("/")
loc = loc[:ind+1]
config = ConfigParser.SafeConfigParser()
config.readfp(open(loc + PLUGIN_CONFIG_FILE))

if config.has_section('Core'):
    if 'name' in config.options('Core'):
        NAME = config.get('Core', 'name')
if config.has_section('Log'):
    if 'level' in config.options('Log'):
        LOGLEVEL = config.get('Log', 'level')
    if 'file' in config.options('Log'):
        LOGFILE = config.get('Log', 'file')


## EXECUTION
class PluginOne(IPlugin):
    inputs = None

    #  TODO: The init should contain anything to load modules or data files that should be variables of the  plugin object
    def __init__(self):
        pass

    #  TODO: Configuration needs to set the values needed to identify the plugin in the plugin database as well as ensure everyhing loaded correctly
    #  TODO: Current  layout is for an enrichment plugin
    #  TODO: enrichment [type, successful_load, name, description, inputs to enrichment such as 'ip', cost, speed]
    #  TODO: interface [type, successful_load, name]
    #  TODO: score [TBD]
    #  TODO: minion [TBD]
    def configure(self):
        """

        :return: return list of [configure success (bool), name, description, list of acceptable inputs, resource cost (1-10, 1=low), speed (1-10, 1=fast)]
        """
        config_options = config.options("Configuration")

        if 'cost' in config_options:
            cost = config.get('Configuration', 'cost')
        else:
            cost = 9999
        if 'speed' in config_options:
            speed = config.get('Configuration', 'speed')
        else:
            speed = 9999

        if config.has_section('Documentation') and 'description' in config.options('Documentation'):
            description = config.get('Configuration', 'type')
        else:
            logging.error("'Description not in config file.")
            return [None, False, NAME, None, cost, speed]

        if 'type' in config_options:
            plugin_type = config.get('Configuration', 'type')
        else:
            logging.error("'Type' not specified in config file.")
            return [None, False, NAME, description, None, cost, speed]

        if 'inputs' in config_options:
            self.inputs = config.get('Configuration', 'Inputs')
            self.inputs = [l.strip().lower() for l in self.inputs.split(",")]
        else:
            logging.error("No input types specified in config file.")
            return [plugin_type, False, NAME, description, None, cost, speed]

        return [plugin_type, True, NAME, description, self.inputs, cost, speed]


    #  TODO: The correct type of execution function must be defined for the type of plugin
    #  TODO: enrichment: "run(<thing to enrich>, start_time, any other plugin-specific attributes-MUST HAVE DEFAULTS)
    #  TODO: interface: enrich(graph, any other plugin-specific attributes-MUST HAVE DEFAULTS)
    #  TODO:            query(topic, max_depth, config, dont_follow, any other plugin-specific attributes-MUST HAVE DEFAULTS)
    #  TODO: score: score(subgraph, topic, any other plugin-specific attributes-MUST HAVE DEFAULTS)
    #  TODO: minion [TBD] 
    #  TODO: Enrichment plugin specifics:
    #  -     Created nodes/edges must follow http://blog.infosecanalytics.com/2014/11/cyber-attack-graph-schema-cags-20.html
    #  -     The enrichment should include a node for the <thing to enrich>
    #  -     The enrichment should include a node for the enrichment which is is statically defined & key of "enrichment"
    #  -     An edge should exist from <thing to enrich> to the enrichment node, created at the end after enrichment
    #  -     Each enrichment datum should have a node
    #  -     An edge should exist from <thing to enrich> to each enrichment datum
    #  -     The run function should then return a networkx directed multi-graph including the nodes and edges
    #  TODO: Interface plugin specifics:
    #  -     In the most efficient way possible, merge nodes and edges into the storage medium
    #  -     Merger of nodes should be done based on matching key & value.
    #  -     URI should remain static for a given node.
    #  -     Start time should be updated to the sending graph
    #  -     Edges should be added w/o attempts to merge with edges in the storage back end
    #  -     When adding nodes it is highly recommended to keep a node-to-storage-id mapping with a key of the node
    #  -       URI.  This will assist in bulk-adding the edges.
    #  -     Query specifics of interface plugins:
    #  -     In the most efficient way possible retrieve and return the merged subgraph (as a networkx graph) including all nodes and 
    #  -     edges within the max_distance from any node in the topic graph from the storage backend graph.
    #  -     As a default, ['enrichment', 'classification'] should not be followed.
    #  -     The query function must add a 'topic_distance' property to all nodes.
    #  TODO: Score plugin specifics:
    #  -     Scoring plugins should take a topic and networkx (sub)graph and return a dictionary keyed with the node (name) and with
    #  -     values of the score assigned to the node for the given topic.
    #  TODO: Minion plugin specifics:
    #  -     [TBD]
    def run(self, value, key, classification, start_time="", confidence=1):
        """

        :param domain: a string containing a domain to look up
        :param include_subdomain: Boolean value.  Default False.  If true, subdomain will be returned in enrichment graph
        :return: a networkx graph representing the sections of the domain
        """
        g = nx.MultiDiGraph()

        if type(start_time) is str:
            try:
                time = datetime.strptime("%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%dT%H:%M:%SZ")
            except:
                time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        elif type(star_time) is datetime:
            time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # Get or create target node
        target_uri = "class=attribute&key={0}&value={1}".format(key, value)
        g.add_node(target_uri, {
            'class': 'attribute',
            'key': key,
            "value": value,
            "start_time": time,
            "uri": target_uri
        })

        # Get or create classification node
        classification_uri = "class=attribute&key={0}&value={1}".format("classification", classification)
        g.add_node(classification_uri, {
            'class': 'attribute',
            'key': "classification",
            "value": classification,
            "start_time": time,
            "uri": classification_uri
        })


        # Link target to classification
        edge_attr = {
            "relationship": "describedBy",
            "start_time": time,
            "origin": "classification",
            "confidence": confidence
        }
        source_hash = uuid.uuid3(uuid.NAMESPACE_URL, target_uri)
        dest_hash = uuid.uuid3(uuid.NAMESPACE_URL, classification_uri)
        edge_uri = "source={0}&destionation={1}".format(str(source_hash), str(dest_hash))
        rel_chain = "relationship"
        while rel_chain in edge_attr:
            edge_uri = edge_uri + "&{0}={1}".format(rel_chain,edge_attr[rel_chain])
            rel_chain = edge_attr[rel_chain]
        if "origin" in edge_attr:
            edge_uri += "&{0}={1}".format("origin", edge_attr["origin"])
        edge_attr["uri"] = edge_uri
        g.add_edge(target_uri, classification_uri, edge_uri, edge_attr)

        return g