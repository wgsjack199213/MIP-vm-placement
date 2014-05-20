def select_most_noisy_vms(num_vms, traffic_matrix, original_placement, physical_config, num_top_noisy_vms, fixed_vms):
    #return [0, 1]

    traffic = [0 for k in range(num_vms)]
    for k in range(num_vms):
        for i in range(num_vms):
            if physical_config.which_rack[original_placement[k]] == physical_config.which_rack[original_placement[i]]:
                continue
            traffic[k] += traffic_matrix[k][i]
    # the list traffic is INDEED the traffic each vm contributes on each link
    ans = []
    indice = []
    traffic_copy, traffic_copy_for_search_index = traffic[:], traffic[:]

    loop_variable = num_top_noisy_vms
    while loop_variable > 0 and traffic_copy != []:
        tmp_max = max(traffic_copy)
        index_max = traffic_copy_for_search_index.index(tmp_max)
        traffic_copy.remove(tmp_max)
        traffic_copy_for_search_index[index_max] = -1

        if index_max in fixed_vms:     # we do not count(choose) the vms that should be fixed
            # TODO
            #print index_max, "can not be moved!========================================="
            continue
        ans.append(tmp_max)
        indice.append(index_max)
        
        loop_variable -= 1

    #print ans, indice
    return indice

