from flask import Flask, render_template, request, jsonify
import requests
import urllib3
import json
import os
import subprocess

config_sh_path = './config_scripts/config.sh'
os.chmod(config_sh_path, 0o755)

states_file_path = 'button_states.json'

app = Flask(__name__)

@app.route('/')
def home():
    #global configs
    states = load_states()
    configs = generate_configs()  # Generate configs based on current states

    return render_template('index.html', groups=groups, states=states, configs=configs)

@app.route('/get_configs')
def get_configs():
    configs = generate_configs()  # This should be the function that generates the current configs
    return jsonify(configs=configs)

@app.route('/set_state')
def set_state():
    group1 = request.args.get('group1')
    group2 = request.args.get('group2')
    state = request.args.get('state')
    
    save_state(group1, group2, state)
    #generate_route_target_config()  # Generate config after state change
    return jsonify({'status': 'success', 'group1': group1, 'group2': group2, 'state': state})

@app.route('/update_vrf_list')
def update_vrf_list_route():
    updateVRF_list()  # Call the function to update the VRF list
    #generate_route_target_config()  # Generate config after VRF list update
    return jsonify({'status': 'success', 'message': 'VRF list updated successfully'})

@app.route('/push_config_to_vyos', methods=['POST'])
def push_config_to_vyos():
    # Logic to push the configuration to VyOS
    # This could involve SSH commands, API calls, etc., depending on your setup
    # File path where the Python script will be saved
    configs = generate_configs()
    configCommand = "sg vyattacfg -c ./config_scripts/config.sh"
    file_path = '/config/scripts/tempConfigFile.py'

    # Write the configuration commands to a file
    with open(file_path, 'w') as file:
        file.write("#!/usr/bin/env python3\n")
        for command in configs:
            file.write(f'print("{command}")\n')

    # Return the path to the created file for download
    os.chmod(file_path, 0o777)
    
    try:
        subprocess.run(configCommand, check=True, shell=True, text=True)
        execution_result = "Command executed successfully."
    except subprocess.CalledProcessError as e:
        execution_result = f"An error occurred: {e}"
    try:
        os.remove(file_path)
        deletion_result = "File deleted successfully."
    except OSError as e:
        deletion_result = f"Error deleting file: {e}"
    
    return jsonify({'message': 'Config pushed to VyOS successfully'})

def save_state(group1, group2, state):
    try:
        with open(states_file_path, 'r') as file:
            states = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        states = {}
    states[f'{group1}-{group2}'] = state
    with open(states_file_path, 'w') as file:
        json.dump(states, file)

def load_states():
    try:
        with open(states_file_path, 'r') as file:
            states = json.load(file)
            return states
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def updateVRF_list():
    global vpn_info, groups
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    groups = []
    url = "https://127.0.0.1/retrieve"
    headers = {}
    apiKey = 'key'
    payload = {'data': '{"op": "showConfig", "path": ["vrf"]}', 'key': apiKey}
    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    data = response.json()
    vpn_info = []
    for name, info in data['data']['name'].items():
        rt_export = info.get("protocols", {}).get("bgp", {}).get("address-family", {}).get("ipv4-unicast", {}).get("route-target", {}).get("vpn", {}).get("export")
        if rt_export:
            vpn_info.append([name, rt_export])
    for i in vpn_info:
        groups.append(i[0])

def generate_configs():
    # Load button states
    try:
        with open(states_file_path, 'r') as file:
            button_states = json.load(file)
    except FileNotFoundError:
        button_states = {}
        with open(states_file_path, 'w') as file:
            json.dump(button_states, file) 

    # Prepare a dictionary to store VRF import configurations
    vrf_imports = {vrf: set() for vrf, rt in vpn_info}

    # Go through the button states to determine the route-target imports
    for pairing, state in button_states.items():
        if state == 'On':
            vrf1, vrf2 = pairing.split('-')
            # Find route-targets for each VRF
            rt1 = next((rt for vrf, rt in vpn_info if vrf == vrf1), None)
            rt2 = next((rt for vrf, rt in vpn_info if vrf == vrf2), None)
            # Add each other's route-targets to the import list
            if rt1 and rt2:
                vrf_imports[vrf1].add(rt2)
                vrf_imports[vrf2].add(rt1)

    # Generate the configuration commands
    config_commands = []
    for vrf, imports in vrf_imports.items():
        if imports:  # If there are imports for this VRF
            rt_imports = ' '.join(imports)
            config_commands.append(f"set vrf name {vrf} protocols bgp address-family ipv4-unicast route-target vpn import '{rt_imports}'")
        else:
            config_commands.append(f"delete vrf name {vrf} protocols bgp address-family ipv4-unicast route-target vpn import")

    return config_commands


if __name__ == '__main__':
    updateVRF_list()
    app.run(debug=True, port=5001, host='0.0.0.0')
