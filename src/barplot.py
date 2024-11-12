import time
import matplotlib.pyplot as plt


def run_barplot(state_dict : dict[str, any], words : enumerate[str]):
    plt.ion()
    fig = plt.figure(1)
    n_classes = len(words)
    
    while True:
        if state_dict["display_barplot"]:
            #plt.figure(1)
            colors = ['tab:blue' for m in range(n_classes)]

            if state_dict["index_best_class"] is not None:
                colors[int(state_dict["index_best_class"])] = 'tab:green'

            mean_classification_values = state_dict["mean_classificaiton_values"][0:n_classes] # '[0:n_classes]' might be replacable by '[:]'
            fig.clear()
            plt.bar(words, mean_classification_values, color = colors)
            fig.canvas.draw()
            fig.canvas.flush_events()
            
        time.sleep(0.1)