### how to run? ###

You need to add the following codes into your file

    from physical_configuration import PhysicalConfig
    from MIP_rack_interface import migrate_policy

Then you can call the function defined in *MIP_rack_interface.py*
    
    migrate_policy(num_vms, vm_consumption, traffic_matrix, original_placement, physical_config)

The return value is a list of vm-server pair. For example, *[[2, 7], [0, 4]]* means *migrate vm2 to server7, and then migrate vm0 to server 4*
A runnable example is *create_testbench_part_vm_rack.py*, you can start up by playing with it.

*****

╮(╯▽╰)╭毕设干巴爹

