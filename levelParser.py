def parse_level_file(filename):
    with open(filename, 'r') as file:
        content = file.read().split('#end')[0].strip().split('\n')
        
    sections = {
        '#domain': "",
        '#levelname': "",
        '#colors': {},
        '#initial': [],
        '#goal': []
    }
    
    current_section = None
    
    for line in content:
        line = line.strip()
        if line.startswith('#'):
            if line in sections:
                current_section = line
                continue
        
        if current_section == '#colors':
            color, agents = line.split(': ')
            agents = agents.split(',')
            try:
                for agent in agents:
                    sections[current_section][int(agent.strip())] = color.strip()
            except:
                sections[current_section][agent.strip()] = color.strip()
        elif current_section in ['#initial', '#goal']:
            sections[current_section].append(line)
        else:
            sections[current_section] = line
    
    return sections