def choose_server_in_rack(migrate_to_rack, vm_consumption, physical_config):
    operations = []
    for migration in migrate_to_rack:
        vm, rack = migration[0], migration[1]
        candidate_servers = []
        for server in physical_config.rack_user_servers[rack]:
            if physical_config.constraint_cpu[server] > vm_consumption[vm][0] and physical_config.constraint_memory[server] > vm_consumption[vm][1] and physical_config.constraint_disk[server] > vm_consumption[vm][2]:
                candidate_servers.append(server)

        server_with_most_memory, most_memory = 0, 0
        for s in candidate_servers:
            if physical_config.constraint_memory[s] > most_memory:
                server_with_most_memory, most_memory = s, physical_config.constraint_memory[s]
                
        physical_config.constraint_cpu[server_with_most_memory] -= vm_consumption[vm][0]
        physical_config.constraint_memory[server_with_most_memory] -= vm_consumption[vm][1]
        physical_config.constraint_disk[server_with_most_memory] -= vm_consumption[vm][2]
        operations.append([vm, server_with_most_memory])

        
    print "final operations", operations
    return operations

