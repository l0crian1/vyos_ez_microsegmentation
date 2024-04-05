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
    states = load_states()
    configs = generate_configs()  # Generate configs based on current states
    return render_template('index.html', groups=groups, states=states, configs=configs)

@app.route('/get_configs')
def get_configs():
    if not vpn_info:  # Check if vpn_info is empty
        # Return a response indicating no VPN information is available
        return jsonify({'error': 'No VPN information available. Ensure route-targets are exported in your config, or press the "Update VRF List button".'}), 400  # Using 400 status code for demonstration
    configs = generate_configs()
    return jsonify(configs=configs)

@app.route('/set_state')
def set_state():
    group1 = request.args.get('group1')
    group2 = request.args.get('group2')
    state = request.args.get('state')

    save_state(group1, group2, state)
    return jsonify({'status': 'success', 'group1': group1, 'group2': group2, 'state': state})

@app.route('/update_vrf_list')
def update_vrf_list_route():
    updateVRF_list()
    return jsonify({'status': 'success', 'message': 'VRF list updated successfully'})

@app.route('/push_config_to_vyos', methods=['POST'])
def push_config_to_vyos():
    configs = generate_configs()
    configCommand = "sg vyattacfg -c ./config_scripts/config.sh"
    file_path = '/config/scripts/tempConfigFile.py'

    try:
        with open(file_path, 'w') as file:
            file.write("#!/usr/bin/env python3\n")
            for command in configs:
                file.write(f'print("{command}")\n')
        os.chmod(file_path, 0o777)

        subprocess.run(configCommand, check=True, shell=True, text=True)
        execution_result = "Command executed successfully."
    except subprocess.CalledProcessError as e:
        execution_result = f"An error occurred: {e}"
    finally:
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
    except (FileNotFoundError, json.JSONDecodeError):
        states = {}
    return states

def updateVRF_list():
    global vpn_info, groups
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    groups = []
    url = "https://127.0.0.1/retrieve"
    headers = {}
    apiKey = 'key'
    payload = {'data': '{"op": "showConfig", "path": ["vrf"]}', 'key': apiKey}

    try:
        response = requests.post(url, headers=headers, data=payload, verify=False)
        response.raise_for_status()  # This will raise an exception for HTTP errors
        data = response.json()
    except requests.exceptions.HTTPError as errh:
        print(f"Http Error: {errh}")
        vpn_info = []
        return
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}")
        vpn_info = []
        return
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
        vpn_info = []
        return
    except requests.exceptions.RequestException as err:
        print(f"Oops: Something Else: {err}")
        vpn_info = []
        return

    vpn_info = []
    for name, info in data.get('data', {}).get('name', {}).items():
        rt_export = info.get("protocols", {}).get("bgp", {}).get("address-family", {}).get("ipv4-unicast", {}).get("route-target", {}).get("vpn", {}).get("export")
        if rt_export:
            vpn_info.append([name, rt_export])
            groups.append(name)
    if not vpn_info:
        print("No VRFs with route-target export found.")

def generate_configs():
    if not vpn_info:  # Check if vpn_info is empty
        print("No VPN information available. Ensure 'updateVRF_list' is successfully executed.")
        return []

    try:
        with open(states_file_path, 'r') as file:
            button_states = json.load(file)
    except FileNotFoundError:
        button_states = {}
        with open(states_file_path, 'w') as file:
            json.dump(button_states, file)

    vrf_imports = {vrf: set() for vrf, rt in vpn_info}
    for pairing, state in button_states.items():
        if state == 'On':
            vrf1, vrf2 = pairing.split('-')
            rt1 = next((rt for vrf, rt in vpn_info if vrf == vrf1), None)
            rt2 = next((rt for vrf, rt in vpn_info if vrf == vrf2), None)
            if rt1 and rt2:
                vrf_imports[vrf1].add(rt2)
                vrf_imports[vrf2].add(rt1)

    config_commands = []
    for vrf, imports in vrf_imports.items():
        if imports:
            rt_imports = ' '.join(imports)
            config_commands.append(f"set vrf name {vrf} protocols bgp address-family ipv4-unicast route-target vpn import '{rt_imports}'")
        else:
            config_commands.append(f"delete vrf name {vrf} protocols bgp address-family ipv4-unicast route-target vpn import")

    return config_commands

if __name__ == '__main__':
    updateVRF_list()
    app.run(debug=True, port=5001, host='0.0.0.0')
