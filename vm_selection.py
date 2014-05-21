def select_most_noisy_vms(num_vms, traffic_matrix, original_placement, physical_config, num_top_noisy_vms, fixed_vms, link_traffic):
    #return [0, 1]

    num_congestion_flows = int(num_top_noisy_vms / 2)

    indice_largest_flows = compute_largest_flows(num_vms, traffic_matrix, original_placement, physical_config, num_top_noisy_vms - num_congestion_flows, fixed_vms)

    #print ans, indice
    indice_congestion_flows = compute_congestion_flows(num_vms, traffic_matrix, original_placement, physical_config, num_congestion_flows, fixed_vms, link_traffic, indice_largest_flows)
    
    print "congestion vms:", indice_congestion_flows
    print "largest traffic vms", indice_largest_flows
    indice = indice_congestion_flows + indice_largest_flows

    return indice


def compute_largest_flows(num_vms, traffic_matrix, original_placement, physical_config, num_top_noisy_vms, fixed_vms):
    traffic = [0 for k in range(num_vms)]
    for k in range(num_vms):
        for i in range(num_vms):
            if physical_config.which_rack[original_placement[k]] == physical_config.which_rack[original_placement[i]]:
                continue
            traffic[k] += traffic_matrix[k][i]
    # the list traffic is INDEED the traffic each vm contributes on each link
    indice = select_top_k_max(traffic_list = traffic, k = num_top_noisy_vms, fixed_vms = fixed_vms)

    return indice

def compute_congestion_flows(num_vms, traffic_matrix, original_placement, physical_config, num_top_noisy_vms, fixed_vms, link_traffic, indice_exclude = []):
    busiest_link = link_traffic.index(max(link_traffic))

    vm_contribution_to_busiest_link = [0 for k in range(num_vms)]

    for p in range(num_vms):
        rack_p = physical_config.which_rack[original_placement[p]]
        for q in range(p+1, num_vms):
            rack_q = physical_config.which_rack[original_placement[q]]
            if rack_p == busiest_link and rack_q != busiest_link or rack_p != busiest_link and rack_q == busiest_link:
                vm_contribution_to_busiest_link[p] += traffic_matrix[p][q]
                vm_contribution_to_busiest_link[q] += traffic_matrix[p][q]

    indice = select_top_k_max(traffic_list = vm_contribution_to_busiest_link, k = num_top_noisy_vms, fixed_vms = fixed_vms+indice_exclude)
    return indice



def select_top_k_max(traffic_list, k, fixed_vms):
    ans = []
    indice = []
    traffic_copy, traffic_copy_for_search_index = traffic_list[:], traffic_list[:]

    loop_variable = k
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

    return indice
    
