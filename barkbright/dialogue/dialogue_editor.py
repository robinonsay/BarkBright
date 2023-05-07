import json
import os
import dearpygui.dearpygui as dpg
from barkbright import bb_config
from dataset import BB_INTENTS

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
node_ids = list()
for key in dialogue.keys():
    if key != 'root' and key != 'sleep':
        node_ids.append(int(key))
node_ids.sort()
# callback runs when user attempts to connect attributes
def _link_callback(sender, app_data):
    # app_data -> (link_id1, link_id2)
    node_0 = str(uuid_node_map[dpg.get_item_parent(app_data[0])])
    node_1 = str(uuid_node_map[dpg.get_item_parent(app_data[1])])
    dialogue[node_0]['children'][node_1] = dialogue[node_1]['intent']
    dialogue[node_0]['transition'][dialogue[node_1]['intent']] = node_1
    link = dpg.add_node_link(app_data[0], app_data[1], parent=sender)
    links[link] = (node_0, node_1)

# callback runs when user attempts to disconnect attributes
def _delink_callback(sender, app_data):
    # app_data -> link_id
    node_0 = links[app_data][0]
    node_1 = links[app_data][1]
    intent = dialogue[node_0]['children'][node_1]
    del dialogue[node_0]['transition'][intent]
    del dialogue[node_0]['children'][node_1]
    del links[app_data]
    dpg.delete_item(app_data)

def _del_node_callback(sender, app_data, user_data):
    del dialogue[uuid_node_map[user_data]]
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

def __set_hub(sender, app_data, user_data):
    value = dpg.get_value(sender)
    node, out_attr, hub_attr = user_data
    node = uuid_node_map[node]
    if  value == 'hub':
        dpg.hide_item(out_attr)
        dpg.show_item(hub_attr)
    else:
        dpg.show_item(out_attr)
        dpg.hide_item(hub_attr)
    dialogue[node]['intent'] = value

def _add_node_callback(sender, app_data):
    with dpg.node(parent='node_editor') as new_node_uuid:
        node_ids.append(node_ids[-1] + 1)
        new_node = str(node_ids[-1])
        uuid_node_map[new_node_uuid] = new_node
        node_uuid_map[new_node] = new_node_uuid
        dialogue[new_node] = {
            'intent': None,
            'dialogue': None,
            'children': dict(),
            'transition': dict()
        }
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_button(label='delete', callback=_del_node_callback, user_data=new_node_uuid)
        out_attr = dpg.generate_uuid()
        hub_attr = dpg.generate_uuid()
        with dpg.node_attribute(label='in') as in_attr:
            intent_str = dpg.add_combo(items=BB_INTENTS + ('hub',),
                                       label="Intent",
                                       width=100,
                                       callback=__set_hub,
                                       user_data=(new_node_uuid, out_attr, hub_attr))
        with dpg.node_attribute(label='output', attribute_type=dpg.mvNode_Attr_Output, tag=out_attr, show=False):
            dialogue_str = dpg.add_input_text(multiline=True, width= 200)
        dpg.add_node_attribute(label='hub', attribute_type=dpg.mvNode_Attr_Output, tag=hub_attr, show=False)
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
            if 'root' in dialogue:
                with dpg.node(label="Wakeword", pos=dialogue['root']['coords']) as root_node:
                    with dpg.node_attribute(label='output', attribute_type=dpg.mvNode_Attr_Output) as root_node_out:
                        root_tedit = dpg.add_input_text(multiline=True, width=200, default_value=dialogue['root']['dialogue'])
                    node_values_reg["root"] = (None, root_tedit)
                uuid_node_map[root_node] = "root"
                node_attr_uuid_map["root"] = (None, root_node_out, None)
                node_uuid_map["root"] = root_node
                with dpg.node(label="sleep", pos=dialogue['sleep']['coords']) as sleep_node:
                    with dpg.node_attribute(label='input', attribute_type=dpg.mvNode_Attr_Input) as end_node_out:
                        end_tedit = dpg.add_input_text(multiline=True, width=200, default_value=dialogue['sleep']['dialogue'])
                    node_values_reg["sleep"] = (None, end_tedit)
                uuid_node_map[sleep_node] = "sleep"
                node_attr_uuid_map["sleep"] = (end_node_out, None, None)
                node_uuid_map["sleep"] = sleep_node


                for node in node_ids:
                    node = str(node)
                    value = dialogue[node]
                    with dpg.node(label=value['intent'], pos=value['coords']) as node_uuid:
                        uuid_node_map[node_uuid] = str(node)
                        node_uuid_map[node] = node_uuid
                        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                            dpg.add_button(label='delete', callback=_del_node_callback, user_data=node_uuid)
                        intent_id = None
                        in_attr = None
                        out_attr = dpg.generate_uuid()
                        hub_attr = dpg.generate_uuid()
                        with dpg.node_attribute(label='in') as in_attr:
                            intent_id = dpg.add_combo(items=BB_INTENTS + ('hub',),
                                                        label="Intent",
                                                        width=100,
                                                        default_value=value['intent'],
                                                        callback=__set_hub,
                                                        user_data=(node_uuid, out_attr, hub_attr))
                        show_hub = value['intent'] == 'hub'
                        with dpg.node_attribute(label='output', attribute_type=dpg.mvNode_Attr_Output, tag=out_attr, show=(not show_hub)):
                            dialogue_id = dpg.add_input_text(multiline=True, width= 200, default_value=value['dialogue'])
                        dpg.add_node_attribute(label='hub', attribute_type=dpg.mvNode_Attr_Output, tag=hub_attr, show=show_hub)
                        node_attr_uuid_map[node] = (in_attr, out_attr, hub_attr)
                    node_values_reg[node] = (intent_id, dialogue_id)
                for node, value in dialogue.items():
                    for child in value['children'].keys():
                        link = None
                        if value['intent'] == 'hub':
                            out_attr = node_attr_uuid_map[node][2]
                            in_attr = node_attr_uuid_map[child][0]
                        else:
                            out_attr = node_attr_uuid_map[node][1]
                            in_attr = node_attr_uuid_map[child][0]
                        if out_attr and in_attr:
                            link = dpg.add_node_link(out_attr, in_attr)
                            links[link] = (node, child)
            else:
                with dpg.node(label="Wakeword") as root_node:
                    with dpg.node_attribute(label='output', attribute_type=dpg.mvNode_Attr_Output) as root_node_out:
                        root_tedit = dpg.add_input_text(multiline=True, width=200, default_value="Hi, how can I help you?")
                    dialogue["root"] = {
                        "intent": None,
                        "dialogue": dpg.get_value(root_tedit),
                        'children': dict(),
                        'transition': dict()
                    }
                    node_values_reg["root"] = (None, root_tedit)
                uuid_node_map[root_node] = "root"
                node_attr_uuid_map["root"] = (None, root_node_out)
                node_uuid_map["root"] = root_node
                with dpg.node(label="sleep") as sleep_node:
                    with dpg.node_attribute(label='input', attribute_type=dpg.mvNode_Attr_Input) as end_node_out:
                        end_tedit = dpg.add_input_text(multiline=True, width=200, default_value="Good bye!")
                    dialogue["sleep"] = {
                        "intent": "sleep",
                        "dialogue": dpg.get_value(end_tedit),
                        'children': dict(),
                        'transition': dict()
                    }
                    node_values_reg["sleep"] = (None, end_tedit)
                uuid_node_map[sleep_node] = "sleep"
                node_attr_uuid_map["sleep"] = (None, end_node_out)
                node_uuid_map["sleep"] = sleep_node
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window(primary, True)
    dpg.start_dearpygui()
