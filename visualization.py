import os
import json
import matplotlib.pyplot as plt

def process_files(folder_path):

    results = {}  
    
    for filename in os.listdir(folder_path):
        if filename.endswith(".jsonl"):
            filepath = os.path.join(folder_path, filename)
            total_requests = 0
            blocked_requests = 0
            
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue  
                    try:
                        record = json.loads(line)
                        total_requests += 1
                        if record.get("action", "").upper() == "BLOCKED":
                            blocked_requests += 1
                    except json.JSONDecodeError:
                        print(f"Error parsing line in {filename}: {line}")
            
            percentage_blocked = (blocked_requests / total_requests * 100) if total_requests > 0 else 0
            base_name = filename[12:-6]
            parts = base_name.split('.')
            display_name = '.'.join(parts[1:]) if len(parts) > 1 else base_name
            
            results[display_name] = percentage_blocked

    return results

def plot_results(results, output_path = "/Users/hovietbaolong/Documents/HCMUS-SchoolYears/4thyear/Thesis/Document/NetworkTraffic/Adverts_Trackers/BlockedRequestPercentage.png"):

    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    x_labels = [item[0] for item in sorted_results]
    y_values = [item[1] for item in sorted_results]
    
    plt.figure(figsize=(16, 10)) 

    plt.rcParams.update({
        'font.size': 14,        
        'axes.titlesize': 26,   
        'axes.labelsize': 22,   
        'xtick.labelsize': 19,  
        'ytick.labelsize': 20    
    })

    plt.bar(x_labels, y_values, color='skyblue')
    plt.xlabel("Application")
    plt.ylabel("Percentage(%)")
    plt.title("Percentage of BLOCKED Requests per Application")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    print(f"Plot saved to: {output_path}")
    plt.show()

if __name__ == '__main__':
    folder_path = 'results2'  
    results = process_files(folder_path)
    i=0
    
    print("BLOCKED request percentages per file:")
    for name, percentage in results.items():
        if percentage>3:
            i+=1
            print(f"{name}: {percentage:.2f}%")
    print(f'Total >=5: {i}')
    plot_results(results)
