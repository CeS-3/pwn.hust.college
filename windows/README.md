# Dojo Windows Infrastructure

## Requirements

The windows environment requires KVM.
It is possible to run without KVM, although this would be extremely slow and is not implemented.
If KVM is enabled, the device `/dev/kvm` will exist in the host operating system.

## Enabling

KVM is already passed through to the dojo container due to the `--privileged` flag.
The windows environment is gated behind the `WINDOWS_VM` environment variable, which can have the values `none` (default) and `full`.
This variable functions similarly to the `DOJO_CHALLENGE` environment variable: it can be modified using either `-e WINDOWS_VM=full` on the docker command-line, or by editing `data/config.env`.

## Basic architecture

The `WINDOWS_VM` environment variable is read by the `docker-compose.yml` file and used to conditionally pick between a no-op service and a builder service.
This is done so that the KVM-requiring full service is swapped with one that does not require KVM when the windows VM in not in use.
`docker-compose` also creates a windows volume which will be shared between the builder service and the challenge container.

The builder service is a docker image located in the `windows/` directory of the source tree.
This docker image contains the tools needed to run a QEMU VM and a floppy disk with files for the install.

Once the VM is built, the resulting image is stored the windows volume.
When a new challenge container is spun up, this volume will be read-only mounted into the container image.
This shared clean image will server as the base for every new copy-on-write image created by a user container.
The read-only mount ensures that the shared image file cannot be modified, even with `root` permissions in the challenge container.
The user can then interact with the VM using the `windows` setuid script within the challenge container.
The script manages the creation and interfacing with the VM image.

Users can interact with the VM over both SSH on port `22` and VNC on port `5912`.
Both of these ports are forwarded by QEMU, and connect to running servers inside the VM image.
QEMU VNC is not used because its limited integration with the operating system prevents the use of important features like copy-and-paste.
Instead, a tightVNC server is installed and configured within the VM.
The windows VNC desktop can be accessed in a similar manner to the linux desktop.

Two `virtio-fs` mounts are forwarded to the VM: one for `/challenge` and one for `/home`.
These are mounted as `Y:` and `Z:` respectively, although they can be configured to be mounted anywhere on the filesystem, including a subdirectory of the `C:\` drive.
The challenge mount is also used to pass the flag and information about whether practice mode is enabled to the VM.
The startup script will secure the flag in `C:\flag` prior to starting SSH.

## Builder service

The VM is not built by the Dockerfile due to a couple factors.
First, docker builders do not have access to devices, like the `/dev/kvm` device needed for the install, by default.
This can be sidestepped by enabling some newer docker features that allow you to define the "build container", allowing you to give this container access to devices and remove isolation from certain build steps.
This however comes at a performance cost, because the resulting image has to be exported as a tar file and transferred into the host docker daemon.
This process is extremely slow for large images.
At the size the VM will be, 10-15GB, this process can take 10-20 minutes for this transfer alone.
Due to this consideration, the image is instead built in the builder service's entrypoint.

The builder first repackages Red Hat's `virtio-win-tools` CDROM ISO, which contains needed drivers and executables, in the format that windows expects.
The repackaged ISO is stored in the volume for later use.
(The command for doing so was extracted from the source code of `hashicorp/packer`, which is used by `hashicorp/vagrant` internally.)
It then downloads a Windows Server 2022 Evaluation Image from Microsoft servers.
(As far as legal issues with this step, I am not a lawyer, but it seems like the evaluation image works fine and does not need to be activated for the dojo's use case.)
It will then check for an `image-built` file in the windows volume.
If this file is present, the builder will exit.
Otherwise it will rebuild the VM image into the `clean.qcow2` file in the windows volume.

## Building process

The builder boots with the server ISO, floppy disk, and virtio CDROM attached.
Users can monitor the building process by connecting via VNC to the top-level dojo container's port `5912`.
First, the VM will boot the windows server ISO.
The server ISO will read the `Autounattend.xml` file from the floppy disk.
This file is known as an answer file, it allows the setup to process completely unattended.
After the operating system is installed, it will reboot into the operating system and automatically log in to the hacker user.
The hacker user is chosen because the administrator account needs to be disabled by the install process for security reasons.
The hacker user has administrator in order to perform this setup.
Once hacker is logged in, it will run the first logon commands defined by the answer file.
These commands will disable the new network prompt pop-up, make the powershell execution policy more permissive, and then run the `setup.ps1` file.

The setup script does a few things to configure the image:

- Set the virtual network to be "private" to ensure windows trusts it
- Enable the SSH service, set the default shell to be PowerShell, and whitelist it in the firewall
- Install the required drivers for the filesystem bridging
- Setup the ChallengeProxy service
- Setup the startup script as a scheduled task
- Install the chocolately package manager
- Install and configure the TightVNC server
- Deactivate the administrator account

Finally, it shuts down the computer.
This automatic shutdown is convienient because it means we don't have to use a separate, potentially fragile script to wait for SSH or WinRM to come up and allow us to shut down the machine to end the build service.
Once the machine boots, control is handed to the startup service.

## Startup service

The startup service:

- mounts the filesystem bridges
- copies the flag out of the bridge (which doesn't support permissions and is therefore world readable) into the C drive, and sets up its permissions
- removes admin unless practice mode is enabled
- starts the SSH daemon and VNC server.
  These are set to manual startup mode so that users cannot connect before the startup script has properly configured permissions.

## Filesystem Sharing

The filesystem sharing has a component on each side of the VM.
The host side has a `virtiofsd` process running for each virtual filesystem that listens on a UNIX socket for connection from QEMU.
The guest side has a filesystem driver that connects to the virtual PCI device, and a userspace process that uses WinFsp, the windows equivalent of FUSE, to mount the filesystem and talks to the driver.

## Host

The biggest concern on the host side is sandboxing.
We don't want users to be able to abuse the filesystem daemon to access files outside of the directories we want to mount in (such as the flag) or escalate privileges.
The typical sandboxing approach with user namespaces is not available to us because of the constraints of the docker container security model.
Instead we can either use chroot sandboxing, which requires root access, or run as hacker and use no sandboxing.
Currently the chroot sandbox is used, however this may be changed in the future.

### Guest

Information about the guest side software can be found on [the virtio-win virtiofs wiki page](https://github.com/virtio-win/kvm-guest-drivers-windows/wiki/Virtiofs).
The userspace process defaults to mounting the first filesystem, unless command-line arguments specify a mount tag to select filesystem.
The mountpoint also defaults to `Z:\` unless overriden.
The userspace process can be started as a service, but, for some reason, windows has no way to persist service command-line arguments across boots, so this can only be used if the defaults are acceptable.
We want to have two filesystems, so our only option is to use the registry to store configuration.
WinFsp, the user filesystem driver library similar to linux's FUSE that the virtiofs service uses, has it's own scripts that can be used to define an FS service in the registry that can then be started by a launcher binary.
We first use the filesystem register script to add an entry to the registry for the virtiofs service, with a template for the command-line arguments.
Later, we can start up this service in the startup script with the launcher, specifying the command-line arguments to substitute into the template.

## Rebuilding the VM image

This can be done by removing the `image-built` file and updating the dojo:

```sh
sudo rm ./data/docker/volumes/pwncollege_windows/_data/image-built
sudo docker exec -it dojo dojo update
```

The existing `virtio-win` ISO and Windows Server ISO stored in the volume will be reused.
