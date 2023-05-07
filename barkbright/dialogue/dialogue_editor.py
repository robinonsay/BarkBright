import json
import os
import dearpygui.dearpygui as dpg
from barkbright import bb_config
from dataset import BB_INTENTS
dpg.create_context()

if os.path.exists(bb_config["dialogue_editor_config"]['dialogue_path']):
    with open(bb_config["dialogue_editor_config"]['dialogue_path'], 'r') as f:
        dialogue = json.load(f)
else:
    dialogue = dict()
links = dict()
node_values_reg = dict()
node_attr_uuid_map = dict()
node_uuid_map = dict()
uuid_node_map = dict()
node_ids = [int(key) for key in dialogue.keys()]
node_ids.sort()
# callback runs when user attempts to connect attributes
def _link_callback(sender, app_data):
    # app_data -> (link_id1, link_id2)
    node_0 = str(uuid_node_map[dpg.get_item_parent(app_data[0])])
    node_1 = str(uuid_node_map[dpg.get_item_parent(app_data[1])])
    dialogue[node_0]['children'][node_1] = None
    link = dpg.add_node_link(app_data[0], app_data[1], parent=sender)
    links[link] = (node_0, node_1)

# callback runs when user attempts to disconnect attributes
def _delink_callback(sender, app_data):
    # app_data -> link_id
    node_0 = links[app_data][0]
    node_1 = links[app_data][1]
    del dialogue[node_0]['children'][node_1]
    del links[app_data]
    dpg.delete_item(app_data)

def _del_node_callback(sender, app_data, user_data):
    del dialogue[user_data]
    del_links = list()
    for link, nodes in links.items():
        if str(uuid_node_map[user_data]) in nodes:
            del_links.append(link)
    for link in del_links:
        del links[link]
    for node in dialogue.values():
        if str(uuid_node_map[user_data]) in node['children']:
            del node['children'][str(uuid_node_map[user_data]) ]
    dpg.delete_item(user_data)

def _add_node_callback(sender, app_data):
    with dpg.node(parent='node_editor') as new_node_uuid:
        new_node = node_ids[-1] + 1
        node_ids.append(new_node)
        uuid_node_map[new_node_uuid] = str(new_node)
        node_uuid_map[str(new_node)] = new_node_uuid
        dialogue[new_node] = {
            'intent': None,
            'dialogue': None,
            'children': dict()
        }
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_button(label='delete', callback=_del_node_callback, user_data=new_node_uuid)
        with dpg.node_attribute(label='in') as in_attr:
            intent_str = dpg.add_combo(items=BB_INTENTS, label="Intent", width=100)
        with dpg.node_attribute(label='output', attribute_type=dpg.mvNode_Attr_Output) as out_attr:
            dialogue_str = dpg.add_input_text(multiline=True, width= 200)
        node_attr_uuid_map[new_node] = (in_attr, out_attr)
        node_values_reg[new_node] = (intent_str, dialogue_str)

def _save_callback(sender, app_data):
    for node, value in dialogue.items():
        if node_values_reg[node][0]:
            value['intent'] = dpg.get_value(node_values_reg[node][0])
        value['dialogue'] = dpg.get_value(node_values_reg[node][1])
        value['coords'] = dpg.get_item_pos(node_uuid_map[node])
    with open(bb_config["dialogue_editor_config"]['dialogue_path'], 'w') as f:
        json.dump(dialogue, f, indent=4)
def main():
    dpg.create_viewport(title='Dialogue Editor', width=800, height=800)
    with dpg.window() as primary:
        add_node_btn = dpg.add_button(label='Add Dialogue Node', callback=_add_node_callback)
        save_btn = dpg.add_button(label='Save', callback=_save_callback)
        with dpg.node_editor(callback=_link_callback, delink_callback=_delink_callback, tag='node_editor', tracked=True, minimap=True):
            if '0' in dialogue:
                for node, value in dialogue.items():
                    label = value['intent'] if value['intent'] else "wakeword"
                    with dpg.node(label=label, pos=value['coords']) as node_uuid:
                        uuid_node_map[node_uuid] = str(node)
                        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                            dpg.add_button(label='delete', callback=_del_node_callback, user_data=node_uuid)
                        intent_id = None
                        in_attr = None
                        if value['intent']:
                            with dpg.node_attribute(label='in') as in_attr:
                                intent_id = dpg.add_combo(items=BB_INTENTS,
                                                          label="Intent",
                                                          width=100,
                                                          default_value=value['intent'])
                        with dpg.node_attribute(label='output', attribute_type=dpg.mvNode_Attr_Output) as out_attr:
                            dialogue_id = dpg.add_input_text(multiline=True,
                                                             width= 200,
                                                             default_value=value['dialogue'])
                        node_attr_uuid_map[node] = (in_attr, out_attr)
                        node_uuid_map[node] = node_uuid
                    node_values_reg[node] = (intent_id, dialogue_id)
                for node, value in dialogue.items():
                    for child in value['children'].keys():
                        link = dpg.add_node_link(node_attr_uuid_map[node][1], node_attr_uuid_map[child][0])
                        links[link] = (node, child)
            else:
                with dpg.node(label="Wakeword") as root_node:
                    with dpg.node_attribute(label='output', attribute_type=dpg.mvNode_Attr_Output) as root_node_out:
                        root_tedit = dpg.add_input_text(multiline=True, width=200, default_value="Hi, how can I help you?")
                    dialogue[0] = {
                        "intent": None,
                        "dialogue": dpg.get_value(root_tedit),
                        'children': dict()
                    }
                    node_values_reg[0] = (None, root_tedit)
                uuid_node_map[root_node] = "0"
                node_attr_uuid_map["0"] = (None, root_node_out)
                node_uuid_map["0"] = root_node
                node_ids.append(0)


    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window(primary, True)
    dpg.start_dearpygui()
