import json
import os
import dearpygui.dearpygui as dpg
from barkbright import bb_config
dpg.create_context()

if os.path.exists(bb_config["dialogue_editor_config"]['dialogue_path']):
    with open(bb_config["dialogue_editor_config"]['dialogue_path'], 'r') as f:
        dialogue = json.load(f)
else:
    dialogue = dict()

# callback runs when user attempts to connect attributes
def _link_callback(sender, app_data):
    # app_data -> (link_id1, link_id2)
    if app_data[0] in dialogue:
        dialogue[app_data[0]]['children'].append(app_data[1])
    else:
        dialogue[app_data[0]] = {
            'node': None,
            'intent': None,
            'dialogue': None,
            'children': list()
        }
    dpg.add_node_link(app_data[0], app_data[1], parent=sender)

# callback runs when user attempts to disconnect attributes
def _delink_callback(sender, app_data):
    # app_data -> link_id
    dpg.delete_item(app_data)

def _add_node_callback(sender, app_data):
    with dpg.node(label='New Node', parent='node_editor'):
        with dpg.node_attribute(label='in'):
            dpg.add_input_text(label='intent', width= 200)
        with dpg.node_attribute(label='out', attribute_type=dpg.mvNode_Attr_Output):
            dpg.add_input_text(label='output', multiline=True, width= 200)

def _save_callback(sender, app_data):
    with open(bb_config["dialogue_editor_config"]['dialogue_path'], 'w') as f:
        json.dump(dialogue, f)


def main():

    dpg.create_viewport(title='Dialogue Editor', width=600, height=300)
    with dpg.window() as primary:
        add_node_btn = dpg.add_button(label='Add Dialogue Node', callback=_add_node_callback)
        save_btn = dpg.add_button(label='Save', callback=_save_callback)
        with dpg.node_editor(callback=_link_callback, delink_callback=_delink_callback, tag='node_editor'):
            if 'root' in dialogue:
                visited = {'root'}
                queue = ['root']
                parent_node = None
                while queue:
                    current_obj = queue.pop(0)
                    with dpg.node(label=current_obj['intent'], tag=current_obj['node']) as current_node:
                        with dpg.add_node_attribute(label='in'):
                            dpg.add_input_text(label='intent', width= 200)
                        with dpg.node_attribute(label='out', attribute_type=dpg.mvNode_Attr_Output):
                            dpg.add_input_text(label='output', multiline=True, width= 200)
                        if parent_node:
                            dpg.add_node_link(parent_node, current_node)
                    queue += current_obj['children']
            with dpg.node(label="Wakeword"):
                dpg.add_node_attribute(attribute_type=dpg.mvNode_Attr_Output)


    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window(primary, True)
    dpg.start_dearpygui()
