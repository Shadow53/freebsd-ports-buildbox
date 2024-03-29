# -*- mode: ruby -*-
# vi: set ft=ruby :

# Install vagrant-disksize to allow resizing the vagrant box disk.
unless Vagrant.has_plugin?('vagrant-disksize')
    raise  Vagrant::Errors::VagrantError.new, 'vagrant-disksize plugin is missing. Please install it using "vagrant plugin install vagrant-disksize" and rerun "vagrant up"'
end

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure('2') do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://vagrantcloud.com/search.
  config.vm.box = 'freebsd/FreeBSD-12.2-RELEASE'
  config.vm.box_version = '2020.10.23'
  config.vm.boot_timeout = 600

  config.vm.guest = :freebsd
  config.vm.synced_folder '.', '/vagrant', id: 'vagrant-root', disabled: false
  config.vm.synced_folder './config', '/home/vagrant/.config/ports', id: 'ports-config', disabled: false
  config.vm.synced_folder './options', '/home/vagrant/.config/ports/options', id: 'ports-options', disabled: false
  #config.vm.synced_folder './packages', '/usr/local/poudriere/data/'
  config.vm.base_mac = '080027D14C66'
  config.ssh.keep_alive = true

  config.disksize.size = '150GB'

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  # config.vm.box_check_update = false

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  # NOTE: This will enable public access to the opened port
  # config.vm.network "forwarded_port", guest: 80, host: 8080

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine and only allow access
  # via 127.0.0.1 to disable public access
  # config.vm.network "forwarded_port", guest: 80, host: 8080, host_ip: "127.0.0.1"

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  # config.vm.network "private_network", ip: "192.168.33.10"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  # config.vm.synced_folder "../data", "/vagrant_data"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
  config.vm.provider 'virtualbox' do |vb|
    # Display the VirtualBox GUI when booting the machine
    vb.gui = true
    vb.name = 'ports_builder'
    vb.cpus = Integer(`nproc`) - 1
    vb.memory = 8192

    vb.customize ['modifyvm', :id, '--hwvirtex', 'on']
    vb.customize ['modifyvm', :id, '--audio', 'none']
    vb.customize ['modifyvm', :id, '--nictype1', 'virtio']
    vb.customize ['modifyvm', :id, '--nictype2', 'virtio']
    vb.customize ['modifyvm', :id, '--cableconnected1', 'on']
  end
  #
  # View the documentation for the provider you are using for more
  # information on available options.

  config.ssh.shell = 'sh'

  # Enable provisioning with a shell script. Additional provisioners such as
  # Ansible, Chef, Docker, Puppet and Salt are also available. Please see the
  # documentation for more information about their specific syntax and use.
  # config.vm.provision "shell", inline: <<-SHELL
  #   apt-get update
  #   apt-get install -y apache2
  # SHELL
  config.vm.provision :shell, path: 'bootstrap.sh'

  config.vm.network :forwarded_port, guest: 80, host: 8282
end
