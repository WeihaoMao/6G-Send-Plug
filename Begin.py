sys.setrecursionlimit(100000)
def main():
    ## Read YAML file 读取配置文件
    CONF_FILENAME = os.path.join(os.path.dirname(__file__), "data.json")
    try:
        with open(CONF_FILENAME, 'r', encoding='utf-8') as stream:
            data = json.load(stream)
    except FileNotFoundError:
        print('File Not Found:', CONF_FILENAME)
        exit(0)
    SETTINGS = data['settings']
    SLICES_INFO = data['slices']
    NUM_CLIENTS = SETTINGS['num_clients']
    MOBILITY_PATTERNS = data['mobility_patterns']
    BASE_STATIONS = data['base_stations']
    CLIENTS = data['clients']


    ##添加输出文件，将日志保存入文件中
    if SETTINGS['logging']:
        sys.stdout = open("./data/"+SETTINGS['log_file'],'wt')
    else:
        sys.stdout = open(os.devnull, 'w')

    import matplotlib.pyplot as plt
    plt.rcParams['figure.max_open_warning'] = 20

    
    ##打印每一次图，存入pic中（假设该动作为离散动作）
    for current_time in range(int(SETTINGS['simulation_time'])+1):
        # 在这里添加可能需要的绘图操作
        # 例如：graph.draw_all(*current_stats)
        if SETTINGS['plotting_params']['plotting'] and current_time % 5 == 0:
            xlim_left = int(SETTINGS['simulation_time'] * SETTINGS['statistics_params']['warmup_ratio'])
            xlim_right = int(SETTINGS['simulation_time'] * (1 - SETTINGS['statistics_params']['cooldown_ratio'])) + 1

            graph = Graph(base_stations, clients, (xlim_left, xlim_right),
                          ((x_vals['min'], x_vals['max']), (y_vals['min'], y_vals['max'])),
                          output_dpi=SETTINGS['plotting_params']['plot_file_dpi'],
                          scatter_size=SETTINGS['plotting_params']['scatter_size'],
                          output_filename=SETTINGS['plotting_params']['plot_file'])
            graph.draw_all(current_time, *stats.get_stats())
            # graph.show_plot()
            if SETTINGS['plotting_params']['plot_save']:
                plt.savefig("./pic/" + "output_"+str(current_time) + '.png', format='png')
        # 运行仿真的下一个时间步骤
        env.run(until=current_time + 1)
    plt.savefig("./data/" + "output_" + str(SETTINGS['simulation_time']) + '.png', format='png')
    from PIL import Image, ImageSequence

    
    # 将pic变成一张gif图片。创建一个空白的GIF图像
    gif_frames = []

    # 将output_0到output_50的图像文件逐一添加到gif_frames中
    for i in range(0, int(SETTINGS['simulation_time']), 5):
        # 读取图像文件
        image_path = f"./pic/output_{i}.png"
        img = Image.open(image_path)
        gif_frames.append(img)

    # 保存为GIF动态图
    gif_frames[0].save('./data/output.gif',
                       save_all=True,
                       append_images=gif_frames[1:],
                       duration=100,  # 图像之间的持续时间（毫秒）
                       loop=0)  # 设置循环次数，0表示无限循环
    
    ##输出print直接会存入txt中
    for client in clients:
        print(client)
        print(f'\tTotal connected time: {client.total_connected_time:>5}')
        print(f'\tTotal unconnected time: {client.total_unconnected_time:>5}')
        print(f'\tTotal request count: {client.total_request_count:>5}')
        print(f'\tTotal consume time: {client.total_consume_time:>5}')
        print(f'\tTotal usage: {client.total_usage:>5}')
        print()

    print(stats.get_stats())
    #结束保存txt
    sys.stdout = sys.__stdout__

    
    print('Simulation has ran completely and output file created to:', "./pic/"+SETTINGS['log_file'])

if __name__ == "__main__":
    main()
