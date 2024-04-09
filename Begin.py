def main():
    # if len(sys.argv) != 2:
    #     print('Please type an input file.')
    #     print('python -m slicesim <input-file>')
    #     exit(1)

    # Read YAML file 读取配置文件
    CONF_FILENAME = os.path.join(os.path.dirname(__file__), "data.json")
    try:
        with open(CONF_FILENAME, 'r', encoding='utf-8') as stream:
            data = json.load(stream)
    except FileNotFoundError:
        print('File Not Found:', CONF_FILENAME)
        exit(0)

    random.seed()
    env = simpy.Environment()


    SETTINGS = data['settings']
    SLICES_INFO = data['slices']
    NUM_CLIENTS = SETTINGS['num_clients']
    MOBILITY_PATTERNS = data['mobility_patterns']
    BASE_STATIONS = data['base_stations']
    CLIENTS = data['clients']

    if SETTINGS['logging']:
        sys.stdout = open("./pic/"+SETTINGS['log_file'],'wt')
    else:
        sys.stdout = open(os.devnull, 'w')
