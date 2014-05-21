### how to run? ###

Fork the branch *5.22* to get the latest version.

You need to add the following codes into your file

    from physical_configuration import PhysicalConfig
    from MIP_rack_interface import migrate_policy

Then you can call the function defined in *MIP_rack_interface.py*
    
    def migrate_policy(num_vms, vm_consumption, vm_traffic_matrix, original_placement, physical_config, num_top_noisy_vms, fixed_vms, cost_migration = [])


The return value is a list of vm-server pairs. For example, *[[2, 7], [0, 4]]* means *migrate vm2 to server7, and then migrate vm0 to server4*.

A runnable example is *create_testbench_part_vm_rack.py*, you can start up by playing with it. To run the test, just run the command

    python create_testbench_part_vm_rack.py

*****

╮(╯▽╰)╭毕设干巴爹

